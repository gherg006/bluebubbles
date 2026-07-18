"""Task 16 local storage, encryption, migration and recovery evidence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from bluebubbles.client.domain.messages import MessageDraft
from bluebubbles.client.domain.offline_actions import OfflineAction
from bluebubbles.client.domain.search import SearchQuery
from bluebubbles.client.domain.transfers import (
    FileTransfer,
    TransferDirection,
    TransferProgress,
    TransferState,
)
from bluebubbles.client.repositories.models import (
    CachedConversationRecord,
    CachedUserRecord,
)
from bluebubbles.client.repositories.sqlite.conversations import (
    SQLiteCachedConversationRepository,
)
from bluebubbles.client.repositories.sqlite.drafts import SQLiteDraftRepository
from bluebubbles.client.repositories.sqlite.keys import SQLitePublicKeyCacheRepository
from bluebubbles.client.repositories.sqlite.offline_actions import (
    SQLiteOfflineActionRepository,
)
from bluebubbles.client.repositories.sqlite.settings import (
    SQLiteLocalSettingsRepository,
)
from bluebubbles.client.repositories.sqlite.transfers import (
    SQLiteTransferStateRepository,
)
from bluebubbles.client.repositories.sqlite.users import SQLiteCachedUserRepository
from bluebubbles.client.security.local_encryption import LocalEncryptionService
from bluebubbles.client.services.messaging import DurableEncryptedMessageQueue
from bluebubbles.client.services.search import LocalSearchService, SearchTokenService
from bluebubbles.client.storage.database import LocalDatabaseManager
from bluebubbles.client.storage.migrations import ClientMigrationManager
from bluebubbles.client.storage.models import CachedPublicKey
from bluebubbles.client.storage.profile_lock import ProfileLock
from bluebubbles.shared.errors.exceptions import LocalStorageError


class FixedKeyProvider:
    """Return a deterministic synthetic master key for local-storage tests."""

    def __init__(self, key: bytes) -> None:
        self._key = key

    async def get_master_key(self) -> bytes:
        return self._key


def build_database(path: Path) -> LocalDatabaseManager:
    """Construct a database manager with recovery below the test profile."""
    return LocalDatabaseManager(
        path,
        ClientMigrationManager(path, path.parent / "recovery"),
    )


@pytest.mark.asyncio
async def test_database_migrates_verifies_integrity_and_rejects_wrong_key(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "profile" / "client_cache.db"
    database = build_database(database_path)
    await database.open(b"a" * 32)
    assert database.is_open
    assert (await database.verify_integrity()).healthy
    version = await database.fetch_one(
        "SELECT version FROM local_schema_version WHERE singleton = 1"
    )
    assert version is not None and version[0] == 2
    await database.close()

    wrong_key_database = build_database(database_path)
    with pytest.raises(LocalStorageError, match="key is invalid"):
        await wrong_key_database.open(b"b" * 32)
    assert not wrong_key_database.is_open


def test_profile_lock_is_exclusive_and_recoverable(tmp_path: Path) -> None:
    path = tmp_path / "profile" / ".profile.lock"
    first = ProfileLock(path)
    second = ProfileLock(path)
    first.acquire()
    with pytest.raises(LocalStorageError, match="already open"):
        second.acquire()
    first.release()
    second.acquire()
    second.release()


def test_profile_lock_recovers_stale_crash_file(tmp_path: Path) -> None:
    path = tmp_path / "profile" / ".profile.lock"
    path.parent.mkdir(parents=True)
    path.write_text("not-a-process", encoding="ascii")
    lock = ProfileLock(path)
    lock.acquire()
    assert lock.acquired
    lock.release()


@pytest.mark.asyncio
async def test_drafts_are_encrypted_bound_and_survive_reopen(tmp_path: Path) -> None:
    database_path = tmp_path / "client_cache.db"
    profile_id = uuid4()
    conversation_id = uuid4()
    key_provider = FixedKeyProvider(b"c" * 32)
    database = build_database(database_path)
    await database.open(await key_provider.get_master_key())
    repository = SQLiteDraftRepository(
        database, LocalEncryptionService(key_provider), profile_id
    )
    marker = "TASK16-DRAFT-PLAINTEXT-MARKER"
    draft = MessageDraft(conversation_id, marker, updated_at=datetime.now(UTC))
    await repository.save_draft(draft)
    assert (await repository.get_draft(conversation_id)) == draft
    await database.close()
    assert marker.encode() not in database_path.read_bytes()

    reopened = build_database(database_path)
    await reopened.open(await key_provider.get_master_key())
    reopened_repository = SQLiteDraftRepository(
        reopened, LocalEncryptionService(key_provider), profile_id
    )
    assert (await reopened_repository.get_draft(conversation_id)) == draft
    await reopened.close()


@pytest.mark.asyncio
async def test_offline_and_transfer_state_are_encrypted_and_recovered(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "client_cache.db"
    profile_id = uuid4()
    key_provider = FixedKeyProvider(b"d" * 32)
    database = build_database(database_path)
    await database.open(await key_provider.get_master_key())
    encryption = LocalEncryptionService(key_provider)
    offline = SQLiteOfflineActionRepository(database, encryption, profile_id)
    action = OfflineAction(
        id=uuid4(),
        action_type="send_message",
        idempotency_key=uuid4(),
        encrypted_payload=b"OFFLINE-LOCAL-MARKER",
        created_at=datetime.now(UTC),
    )
    await offline.save(action)
    assert await offline.get(action.id) == action
    assert await offline.list_pending() == [action]

    transfers = SQLiteTransferStateRepository(database, encryption, profile_id)
    transfer = FileTransfer(
        uuid4(),
        uuid4(),
        TransferDirection.UPLOAD,
        TransferState.TRANSFERRING,
        TransferProgress(5, 10),
    )
    await transfers.save(transfer)
    assert await transfers.get(transfer.id) == transfer
    assert await transfers.list_incomplete() == [transfer]
    await database.close()
    content = database_path.read_bytes()
    assert b"OFFLINE-LOCAL-MARKER" not in content
    assert b"transferred_bytes" not in content


@pytest.mark.asyncio
async def test_search_uses_hmac_tokens_and_encrypted_previews(tmp_path: Path) -> None:
    database_path = tmp_path / "client_cache.db"
    profile_id = uuid4()
    key_provider = FixedKeyProvider(b"e" * 32)
    database = build_database(database_path)
    await database.open(await key_provider.get_master_key())
    token_service = SearchTokenService(key_provider)
    service = LocalSearchService(
        database,
        LocalEncryptionService(key_provider),
        token_service,
        profile_id,
    )
    message_id = uuid4()
    conversation_id = uuid4()
    text = "Café TASK16-SEARCH-PLAINTEXT phrase"
    await service.index_message(
        message_id,
        conversation_id,
        uuid4(),
        datetime.now(UTC),
        text,
    )
    results = await service.search(SearchQuery("café task16", conversation_id))
    assert [result.message_id for result in results] == [message_id]
    token = await token_service.token_digest("café")
    assert len(token) == 32
    assert token != await SearchTokenService(FixedKeyProvider(b"f" * 32)).token_digest(
        "café"
    )
    await database.close()
    raw = database_path.read_bytes()
    assert b"TASK16-SEARCH-PLAINTEXT" not in raw
    assert b"caf\xc3\xa9" not in raw.lower()


@pytest.mark.asyncio
async def test_versioned_caches_keys_and_settings(tmp_path: Path) -> None:
    database = build_database(tmp_path / "client_cache.db")
    await database.open(b"g" * 32)
    now = datetime.now(UTC)
    users = SQLiteCachedUserRepository(database)
    user_id = uuid4()
    current_user = CachedUserRecord(user_id, "user", "Current", 2, now)
    assert await users.save(current_user)
    assert not await users.save(CachedUserRecord(user_id, "user", "Old", 1, now))
    assert await users.get(user_id) == current_user

    conversations = SQLiteCachedConversationRepository(database)
    conversation_id = uuid4()
    current_conversation = CachedConversationRecord(
        conversation_id, "direct", now, 3, now, "Current"
    )
    assert await conversations.save(current_conversation)
    assert not await conversations.save(
        CachedConversationRecord(conversation_id, "direct", now, 2, now, "Old")
    )
    assert await conversations.get(conversation_id) == current_conversation

    keys = SQLitePublicKeyCacheRepository(database)
    cached_key = CachedPublicKey(
        user_id,
        "signing",
        1,
        b"p" * 32,
        "fingerprint",
        now,
        now + timedelta(hours=1),
    )
    await keys.save(cached_key)
    assert await keys.get_valid(user_id, "signing", 1) == cached_key
    await keys.invalidate_user(user_id)
    assert await keys.get_valid(user_id, "signing", 1) is None

    settings = SQLiteLocalSettingsRepository(database)
    await settings.set("theme", {"name": "dark"})
    assert await settings.get("theme") == {"name": "dark"}
    await database.close()


@pytest.mark.asyncio
async def test_durable_queue_round_trip_uses_existing_messaging_protocol(
    tmp_path: Path,
) -> None:
    from tests.unit.client.test_task_13_client_messaging import _contracts

    database = build_database(tmp_path / "client_cache.db")
    key_provider = FixedKeyProvider(b"h" * 32)
    await database.open(await key_provider.get_master_key())
    repository = SQLiteOfflineActionRepository(
        database, LocalEncryptionService(key_provider), uuid4()
    )
    queue = DurableEncryptedMessageQueue(repository)
    request, _ = _contracts()
    await queue.enqueue(request)
    due = await queue.due(datetime.now(UTC) + timedelta(seconds=1))
    assert len(due) == 1 and due[0].request == request
    await queue.mark_retry(request.client_message_id, "network_unavailable")
    assert await queue.due(datetime.now(UTC)) == ()
    assert len(await queue.due(datetime.now(UTC) + timedelta(seconds=31))) == 1
    await queue.mark_stored(request.client_message_id)
    assert await queue.due(datetime.now(UTC) + timedelta(seconds=31)) == ()
    await database.close()
