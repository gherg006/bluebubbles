"""Lifecycle coordination for one authenticated user's local storage."""

from __future__ import annotations

from uuid import UUID

from bluebubbles.client.configuration.settings import ClientStorageSettings
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
