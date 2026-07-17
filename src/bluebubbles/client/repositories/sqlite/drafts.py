"""Encrypted SQLite repository for unsent message drafts."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from bluebubbles.client.domain.messages import MessageDraft
from bluebubbles.client.repositories.sqlite._serialisation import (
    decode_json,
    encode_json,
)
from bluebubbles.client.security.local_encryption import (
    EncryptedLocalValue,
    LocalEncryptionPurpose,
    LocalEncryptionService,
)
from bluebubbles.client.storage.database import LocalDatabaseManager


class SQLiteDraftRepository:
    """Store draft plaintext only inside authenticated encrypted payloads."""

    def __init__(
        self,
        database: LocalDatabaseManager,
        encryption: LocalEncryptionService,
        profile_id: UUID,
    ) -> None:
        self._database = database
        self._encryption = encryption
        self._profile_id = profile_id

    async def save_draft(self, draft: MessageDraft) -> None:
        """Encrypt and upsert one profile/conversation-bound draft."""
        updated = draft.updated_at or datetime.now(UTC)
        plaintext = encode_json(
            {
                "text": draft.text,
                "reply_to_id": str(draft.reply_to_id) if draft.reply_to_id else None,
                "attachment_ids": [str(value) for value in draft.attachment_ids],
                "updated_at": updated.isoformat(),
            }
        )
        value = await self._encryption.encrypt(
            LocalEncryptionPurpose.DRAFT,
            plaintext,
            self._context(draft.conversation_id),
        )
        await self._database.execute(
            "INSERT INTO drafts(conversation_id, ciphertext, nonce, format_version, "
            "updated_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(conversation_id) DO "
            "UPDATE SET ciphertext=excluded.ciphertext, nonce=excluded.nonce, "
            "format_version=excluded.format_version, updated_at=excluded.updated_at",
            (
                str(draft.conversation_id),
                value.ciphertext,
                value.nonce,
                value.version,
                updated.isoformat(),
            ),
        )

    async def get_draft(self, conversation_id: UUID) -> MessageDraft | None:
        """Authenticate and return one draft, or None when absent."""
        row = await self._database.fetch_one(
            "SELECT ciphertext, nonce, format_version FROM drafts "
            "WHERE conversation_id = ?",
            (str(conversation_id),),
        )
        if row is None:
            return None
        plaintext = await self._encryption.decrypt(
            LocalEncryptionPurpose.DRAFT,
            EncryptedLocalValue(int(row[2]), bytes(row[1]), bytes(row[0])),
            self._context(conversation_id),
        )
        data = decode_json(plaintext)
        reply = data.get("reply_to_id")
        attachments = data.get("attachment_ids", [])
        return MessageDraft(
            conversation_id=conversation_id,
            text=str(data["text"]),
            reply_to_id=UUID(str(reply)) if reply else None,
            attachment_ids=tuple(UUID(str(value)) for value in attachments),
            updated_at=datetime.fromisoformat(str(data["updated_at"])),
        )

    async def delete_draft(self, conversation_id: UUID) -> None:
        """Delete one draft idempotently."""
        await self._database.execute(
            "DELETE FROM drafts WHERE conversation_id = ?", (str(conversation_id),)
        )

    async def list_drafts(self) -> list[MessageDraft]:
        """Return all authenticated drafts ordered by most recent edit."""
        rows = await self._database.fetch_all(
            "SELECT conversation_id FROM drafts ORDER BY updated_at DESC"
        )
        drafts: list[MessageDraft] = []
        for row in rows:
            draft = await self.get_draft(UUID(str(row[0])))
            if draft is not None:
                drafts.append(draft)
        return drafts

    def _context(self, conversation_id: UUID) -> bytes:
        return f"{self._profile_id}:{conversation_id}:draft:1".encode("ascii")
