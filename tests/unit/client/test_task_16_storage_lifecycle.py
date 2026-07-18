"""Task 16 lifecycle, cache policy, recovery, and repository evidence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from bluebubbles.client.configuration.settings import ClientStorageSettings
from bluebubbles.client.domain.transfers import (
    FileTransfer,
    TransferDirection,
    TransferProgress,
    TransferRecovery,
    TransferState,
)
from bluebubbles.client.repositories.sqlite.synchronisation import (
    SQLiteSynchronisationStateRepository,
)
from bluebubbles.client.repositories.sqlite.transfers import (
    SQLiteTransferStateRepository,
)
from bluebubbles.client.security.local_encryption import LocalEncryptionService
from bluebubbles.client.security.local_keys import ProfileLocalKeyProvider
from bluebubbles.client.storage.cache_manager import CacheManager
from bluebubbles.client.storage.database import LocalDatabaseManager
from bluebubbles.client.storage.migrations import ClientMigrationManager
from bluebubbles.client.storage.models import (
    CacheEntry,
    CacheEntryType,
    SynchronisationState,
)
from bluebubbles.client.storage.paths import ProfilePaths
from bluebubbles.client.storage.service import LocalStorageService
from bluebubbles.shared.errors.exceptions import LocalStorageError


class MemorySecureStore:
    """Implement the protected-store boundary without platform state."""

    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}
        self.deleted_profiles: list[UUID] = []

    async def set_secret(self, key: str, value: bytes) -> None:
        self.values[key] = value

    async def get_secret(self, key: str) -> bytes | None:
        return self.values.get(key)

    async def delete_secret(self, key: str) -> None:
        self.values.pop(key, None)

    async def delete_profile(self, profile_id: UUID) -> None:
        self.deleted_profiles.append(profile_id)
        prefix = f"profile:{profile_id}:"
        self.values = {
            key: value
            for key, value in self.values.items()
            if not key.startswith(prefix)
        }


def database(path: Path) -> LocalDatabaseManager:
    """Construct one migration-aware temporary database."""
    return LocalDatabaseManager(
        path, ClientMigrationManager(path, path.parent / "recovery")
    )


@pytest.mark.asyncio
async def test_profile_key_create_lock_destroy_and_invalid_value() -> None:
    store = MemorySecureStore()
    profile_id = uuid4()
    provider = ProfileLocalKeyProvider(store, profile_id)
    first = await provider.get_master_key()
    assert len(first) == 32
    assert await provider.get_master_key() == first
    await provider.lock()
    assert await provider.get_master_key() == first
    await provider.destroy()
    assert not store.values
    store.values[f"profile:{profile_id}:local_master_key"] = b"short"
    await provider.lock()
    with pytest.raises(LocalStorageError):
        await provider.get_master_key()


@pytest.mark.asyncio
async def test_cache_eviction_expiry_and_usage(tmp_path: Path) -> None:
    profile_id = uuid4()
    paths = ProfilePaths(tmp_path, profile_id)
    paths.initialise()
    manager = database(paths.database)
    await manager.open(b"k" * 32)
    cache = CacheManager(manager, paths, maximum_bytes=20_000, cleanup_target_ratio=0.5)
    now = datetime.now(UTC)
    expired_path = paths.managed_path("cache/expired.bin")
    expired_path.write_bytes(b"x" * 100)
    await cache.register(
        CacheEntry(
            cache_key="expired",
            cache_type=CacheEntryType.TEMPORARY,
            size_bytes=100,
            created_at=now,
            last_accessed_at=now,
            storage_reference="cache/expired.bin",
            expires_at=now - timedelta(seconds=1),
        )
    )
    expired = await cache.remove_expired_entries()
    assert expired.removed_entries == 1
    assert not expired_path.exists()
    large_path = paths.managed_path("cache/large.bin")
    large_path.write_bytes(b"z" * 50_000)
    await cache.register(
        CacheEntry(
            cache_key="large",
            cache_type=CacheEntryType.THUMBNAIL,
            size_bytes=50_000,
            created_at=now,
            last_accessed_at=now,
            storage_reference="cache/large.bin",
        )
    )
    await cache.mark_accessed("large")
    result = await cache.enforce_limits()
    assert result.removed_entries == 1
    assert not large_path.exists()
    await manager.close()


@pytest.mark.asyncio
async def test_transfer_recovery_and_synchronisation_versions(tmp_path: Path) -> None:
    manager = database(tmp_path / "cache.db")
    await manager.open(b"r" * 32)

    class KeyProvider:
        async def get_master_key(self) -> bytes:
            return b"r" * 32

    profile_id = uuid4()
    transfers = SQLiteTransferStateRepository(
        manager, LocalEncryptionService(KeyProvider()), profile_id
    )
    transfer = FileTransfer(
        id=uuid4(),
        attachment_id=uuid4(),
        direction=TransferDirection.UPLOAD,
        state=TransferState.TRANSFERRING,
        progress=TransferProgress(10, 20, 5.0, 2.0),
        recovery=TransferRecovery(
            temporary_path=(tmp_path / "encrypted").resolve(),
            upload_id=uuid4(),
            destination_path=(tmp_path / "destination").resolve(),
            confirmed_chunks=(0, 2),
            session_expires_at=datetime.now(UTC) + timedelta(hours=1),
            file_key=b"f" * 32,
        ),
    )
    await transfers.save(transfer)
    restored = await transfers.get(transfer.id)
    assert restored == transfer
    assert await transfers.list_incomplete() == [transfer]
    await transfers.delete(transfer.id)
    assert await transfers.get(transfer.id) is None
    sync = SQLiteSynchronisationStateRepository(manager)
    current = SynchronisationState(
        "messages", "conversation", "cursor-2", 2, datetime.now(UTC)
    )
    assert await sync.save(current)
    older = SynchronisationState(
        "messages", "conversation", "cursor-1", 1, datetime.now(UTC)
    )
    assert not await sync.save(older)
    assert await sync.get("messages", "conversation") == current
    assert await sync.get("missing") is None
    await manager.close()


@pytest.mark.asyncio
async def test_storage_service_recovery_selective_and_complete_clear(
    tmp_path: Path,
) -> None:
    store = MemorySecureStore()
    profile_id = uuid4()
    settings = ClientStorageSettings(
        profile_root=tmp_path,
        default_cache_limit_bytes=1_000_000,
    )
    service = LocalStorageService(profile_id, settings, store)
    await service.initialise()
    assert (await service.verify_integrity()).healthy
    await service.database.execute(
        "INSERT INTO local_users(user_id, username, display_name, profile_version, "
        "cached_at) VALUES (?, ?, ?, ?, ?)",
        (str(uuid4()), "user", "User", 1, datetime.now(UTC).isoformat()),
    )
    await service.clear_replaceable_cache()
    assert await service.database.fetch_one("SELECT user_id FROM local_users") is None
    quarantined = await service.recover_corrupt_cache()
    assert quarantined is not None and quarantined.exists()
    await service.perform_maintenance()
    usage = await service.get_storage_usage()
    assert usage.database_bytes > 0
    await service.clear_all_local_data()
    assert not service.paths.profile_root.exists()
    assert store.deleted_profiles == [profile_id]


@pytest.mark.asyncio
async def test_migration_backup_restore_and_database_error_paths(
    tmp_path: Path,
) -> None:
    path = tmp_path / "cache.db"
    migrations = ClientMigrationManager(path, tmp_path / "recovery")
    assert await migrations.get_current_version() == 0
    with pytest.raises(LocalStorageError):
        await migrations.create_backup()
    manager = LocalDatabaseManager(path, migrations)
    with pytest.raises(LocalStorageError):
        await manager.open(b"short")
    await manager.open(b"m" * 32)
    assert await migrations.get_current_version() == migrations.latest_version
    backup = await migrations.create_backup()
    assert backup.exists()
    await manager.executemany(
        "INSERT INTO local_settings(setting_key, value_json, updated_at) "
        "VALUES (?, ?, ?)",
        [
            ("one", "1", datetime.now(UTC).isoformat()),
            ("two", "2", datetime.now(UTC).isoformat()),
        ],
    )
    await manager.vacuum()
    await manager.close()
    with pytest.raises(LocalStorageError):
        await manager.fetch_one("SELECT 1")
    invalid_backup = tmp_path / "outside.db"
    invalid_backup.write_bytes(b"invalid")
    with pytest.raises(LocalStorageError):
        await migrations.restore_backup(invalid_backup)
    await migrations.restore_backup(backup)
    await manager.open(b"m" * 32)
    assert (
        await manager.fetch_one(
            "SELECT setting_key FROM local_settings WHERE setting_key = ?", ("one",)
        )
        is None
    )
    await manager.close()
