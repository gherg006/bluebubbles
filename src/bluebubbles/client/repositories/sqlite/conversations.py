"""Version-safe SQLite cache for conversation summaries."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from bluebubbles.client.repositories.models import CachedConversationRecord
from bluebubbles.client.storage.database import LocalDatabaseManager


class SQLiteCachedConversationRepository:
    """Cache startup summaries without accepting delayed older events."""

    def __init__(self, database: LocalDatabaseManager) -> None:
        self._database = database

    async def save(self, conversation: CachedConversationRecord) -> bool:
        """Upsert a summary only when its server version is not older."""
        if conversation.server_version < 1 or conversation.unread_count < 0:
            raise ValueError("Conversation cache metadata is invalid")
        changed = await self._database.execute(
            "INSERT INTO cached_conversations(conversation_id, conversation_type, "
            "title, last_activity_at, latest_message_id, unread_count, is_muted, "
            "is_pinned, is_archived, server_version, cached_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(conversation_id) DO UPDATE SET "
            "conversation_type=excluded.conversation_type, title=excluded.title, "
            "last_activity_at=excluded.last_activity_at, "
            "latest_message_id=excluded.latest_message_id, "
            "unread_count=excluded.unread_count, is_muted=excluded.is_muted, "
            "is_pinned=excluded.is_pinned, is_archived=excluded.is_archived, "
            "server_version=excluded.server_version, cached_at=excluded.cached_at "
            "WHERE excluded.server_version >= cached_conversations.server_version",
            (
                str(conversation.conversation_id),
                conversation.conversation_type,
                conversation.title,
                conversation.last_activity_at.isoformat(),
                (
                    str(conversation.latest_message_id)
                    if conversation.latest_message_id
                    else None
                ),
                conversation.unread_count,
                int(conversation.is_muted),
                int(conversation.is_pinned),
                int(conversation.is_archived),
                conversation.server_version,
                conversation.cached_at.isoformat(),
            ),
        )
        return changed > 0

    async def get(self, conversation_id: UUID) -> CachedConversationRecord | None:
        """Return one startup summary from the local cache."""
        row = await self._database.fetch_one(
            "SELECT conversation_type, title, last_activity_at, latest_message_id, "
            "unread_count, is_muted, is_pinned, is_archived, server_version, cached_at "
            "FROM cached_conversations WHERE conversation_id = ?",
            (str(conversation_id),),
        )
        if row is None:
            return None
        return CachedConversationRecord(
            conversation_id,
            str(row[0]),
            datetime.fromisoformat(str(row[2])),
            int(row[8]),
            datetime.fromisoformat(str(row[9])),
            str(row[1]) if row[1] else None,
            UUID(str(row[3])) if row[3] else None,
            int(row[4]),
            bool(row[5]),
            bool(row[6]),
            bool(row[7]),
        )
