"""Lifecycle coordination for one authenticated user's local storage."""

from __future__ import annotations

import asyncio
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from bluebubbles.client.configuration.settings import ClientStorageSettings
from bluebubbles.client.repositories.sqlite.offline_actions import (
    SQLiteOfflineActionRepository,
)
from bluebubbles.client.repositories.sqlite.synchronisation import (
    SQLiteSynchronisationStateRepository,
)
from bluebubbles.client.repositories.sqlite.synchronisation_metadata import (
    SQLiteConflictRepository,
    SQLiteTombstoneRepository,
)
from bluebubbles.client.security.local_encryption import LocalEncryptionService
from bluebubbles.client.security.local_keys import ProfileLocalKeyProvider
from bluebubbles.client.security.secure_store import SecureStore
from bluebubbles.client.storage.cache_manager import CacheManager
from bluebubbles.client.storage.database import LocalDatabaseManager
from bluebubbles.client.storage.migrations import ClientMigrationManager
from bluebubbles.client.storage.models import (
    LocalDatabaseIntegrityResult,
    LocalStorageUsage,
)
from bluebubbles.client.storage.paths import ProfilePaths
from bluebubbles.client.storage.profile_lock import ProfileLock
from bluebubbles.shared.errors.exceptions import LocalStorageError


class LocalStorageService:
    """Own profile lock, protected key, database, migrations and cache maintenance."""

    def __init__(
        self,
        profile_id: UUID,
        settings: ClientStorageSettings,
        secure_store: SecureStore,
    ) -> None:
        self.profile_id = profile_id
        self._secure_store = secure_store
        self.paths = ProfilePaths(settings.profile_root, profile_id)
        self.key_provider = ProfileLocalKeyProvider(secure_store, profile_id)
        self.encryption = LocalEncryptionService(self.key_provider)
        self.migrations = ClientMigrationManager(
            self.paths.database, self.paths.recovery
        )
        self.database = LocalDatabaseManager(self.paths.database, self.migrations)
        self.cache = CacheManager(
            self.database,
            self.paths,
            settings.default_cache_limit_bytes,
        )
        self.offline_actions = SQLiteOfflineActionRepository(
            self.database, self.encryption, profile_id
        )
        self.synchronisation_state = SQLiteSynchronisationStateRepository(self.database)
        self.conflicts = SQLiteConflictRepository(self.database)
        self.tombstones = SQLiteTombstoneRepository(self.database)
        self._profile_lock = ProfileLock(self.paths.lock_file)

    async def initialise(self) -> None:
        """Open the correct user's verified cache in the required startup order."""
        self.paths.initialise()
        self._profile_lock.acquire()
        try:
            await self.database.open(await self.key_provider.get_master_key())
            integrity = await self.database.verify_integrity()
            if not integrity.healthy:
                raise LocalStorageError(user_message="The local cache is damaged.")
        except BaseException:
            await self.database.close()
            await self.key_provider.lock()
            self._profile_lock.release()
            raise

    async def close(self) -> None:
        """Close the profile database, clear key memory and release its lock."""
        await self.database.close()
        await self.key_provider.lock()
        self._profile_lock.release()

    async def verify_integrity(self) -> LocalDatabaseIntegrityResult:
        """Return the current SQLite integrity result."""
        return await self.database.verify_integrity()

    async def get_storage_usage(self) -> LocalStorageUsage:
        """Return database and managed filesystem accounting."""
        return await self.cache.calculate_usage()

    async def perform_maintenance(self) -> None:
        """Remove expired entries and enforce the configured LRU limit."""
        await self.cache.remove_expired_entries()
        await self.cache.enforce_limits()

    async def recover_corrupt_cache(self) -> Path | None:
        """Quarantine a damaged cache and create a fresh encrypted database."""
        await self.database.close()
        database = self.paths.database
        quarantined: Path | None = None
        if database.exists():
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
            quarantined = self.paths.recovery / f"client_cache.corrupt-{stamp}.db"
            await asyncio.to_thread(database.replace, quarantined)
            for suffix in ("-wal", "-shm"):
                sidecar = Path(f"{database}{suffix}")
                if sidecar.exists():
                    await asyncio.to_thread(sidecar.unlink)
        await self.database.open(await self.key_provider.get_master_key())
        return quarantined

    async def clear_replaceable_cache(self) -> None:
        """Remove rebuildable message/search/cache data while preserving user work."""

        def operation(connection: sqlite3.Connection) -> None:
            connection.execute("DELETE FROM search_documents")
            connection.execute("DELETE FROM cached_messages")
            connection.execute("DELETE FROM cached_conversation_members")
            connection.execute("DELETE FROM cached_conversations")
            connection.execute("DELETE FROM local_users")
            connection.execute("DELETE FROM cached_public_keys")
            connection.execute("DELETE FROM synchronisation_state")
            connection.execute(
                "DELETE FROM cache_entries WHERE cache_type NOT IN (?, ?)",
                ("transfer", "temporary"),
            )
            connection.commit()

        await self.database.run_transaction(operation)

    async def clear_all_local_data(self) -> None:
        """Destroy profile keys and managed local data without touching the server."""
        profile_root = self.paths.profile_root
        root = self.paths.root.expanduser().resolve()
        if profile_root == root or root not in profile_root.parents:
            raise LocalStorageError(user_message="The local profile path is invalid.")
        await self.database.close()
        await self.key_provider.destroy()
        await self._secure_store.delete_profile(self.profile_id)
        self._profile_lock.release()
        await asyncio.to_thread(shutil.rmtree, profile_root, True)
