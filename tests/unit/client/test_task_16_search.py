"""Task 16 search rebuild, invalidation, and privacy edge cases."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from bluebubbles.client.domain.search import SearchQuery
from bluebubbles.client.security.local_encryption import LocalEncryptionService
from bluebubbles.client.services.search import (
    LocalSearchService,
    SearchIndexRecord,
    SearchTokenService,
)
from bluebubbles.client.storage.database import LocalDatabaseManager
from bluebubbles.client.storage.migrations import ClientMigrationManager


class KeyProvider:
    """Return stable synthetic search key material."""

    async def get_master_key(self) -> bytes:
        return b"s" * 32


@pytest.mark.asyncio
async def test_rebuild_clear_and_invalid_search_inputs(tmp_path: Path) -> None:
    path = tmp_path / "cache.db"
    database = LocalDatabaseManager(
        path, ClientMigrationManager(path, tmp_path / "recovery")
    )
    await database.open(b"s" * 32)
    profile_id = uuid4()
    tokens = SearchTokenService(KeyProvider())
    search = LocalSearchService(
        database,
        LocalEncryptionService(KeyProvider()),
        tokens,
        profile_id,
    )
    conversation_id, sender_id = uuid4(), uuid4()
    records = [
        SearchIndexRecord(
            uuid4(),
            conversation_id,
            sender_id,
            datetime.now(UTC),
            "Alpha beta phrase",
        ),
        SearchIndexRecord(
            uuid4(),
            conversation_id,
            sender_id,
            datetime.now(UTC),
            "Another alpha record",
        ),
    ]
    assert await search.rebuild(records) == 2
    assert len(await search.search(SearchQuery("alpha"))) == 2
    await search.clear_conversation(conversation_id)
    assert await search.search(SearchQuery("alpha")) == []
    await search.index_message(
        records[0].message_id,
        conversation_id,
        sender_id,
        records[0].created_at,
        "punctuation only !!!",
    )
    await search.index_message(
        records[0].message_id,
        conversation_id,
        sender_id,
        records[0].created_at,
        "___",
    )
    assert await search.search(SearchQuery("punctuation")) == []
    with pytest.raises(ValueError):
        await search.search(SearchQuery("___"))
    with pytest.raises(ValueError):
        await tokens.token_digest("two words")
    await search.clear()
    await database.close()
