"""Ciphertext-only transport and encrypted display-cache message repository."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from bluebubbles.client.security.local_encryption import (
    EncryptedLocalValue,
    LocalEncryptionPurpose,
    LocalEncryptionService,
)
from bluebubbles.client.storage.database import LocalDatabaseManager
from bluebubbles.shared.models.messages import EncryptedMessageResponse


class SQLiteCachedMessageRepository:
    """Store server ciphertext and separately protected local display plaintext."""

    def __init__(
        self,
        database: LocalDatabaseManager,
        encryption: LocalEncryptionService,
        profile_id: UUID,
    ) -> None:
        self._database = database
        self._encryption = encryption
        self._profile_id = profile_id

    async def store(self, message: EncryptedMessageResponse) -> None:
        """Upsert one transport response without decrypting it."""
        payload = message.model_dump_json().encode("utf-8")
        await self._database.execute(
            "INSERT INTO cached_messages(message_id, conversation_id, sender_id, "
            "message_type, transport_payload, server_created_at, client_created_at, "
            "message_version, delivery_state, cached_at) VALUES (?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?) ON CONFLICT(message_id) DO UPDATE SET "
            "transport_payload=CASE WHEN excluded.message_version >= message_version "
            "THEN excluded.transport_payload ELSE transport_payload END, "
            "message_version=MAX(message_version, excluded.message_version), "
            "delivery_state=excluded.delivery_state, cached_at=excluded.cached_at",
            (
                str(message.id),
                str(message.conversation_id),
                str(message.sender_id),
                message.message_type.value,
                payload,
                message.sent_at.isoformat(),
                datetime.now(UTC).isoformat(),
                message.version,
                message.delivery_status.value,
                datetime.now(UTC).isoformat(),
            ),
        )

    async def store_display_content(
        self, message_id: UUID, conversation_id: UUID, plaintext: bytes
    ) -> None:
        """Encrypt authorized display content before attaching it to a cache row."""
        value = await self._encryption.encrypt(
            LocalEncryptionPurpose.MESSAGE_CACHE,
            plaintext,
            self._context(message_id, conversation_id),
        )
        await self._database.execute(
            "UPDATE cached_messages SET display_ciphertext = ?, display_nonce = ?, "
            "display_format_version = ? WHERE message_id = ? AND conversation_id = ?",
            (
                value.ciphertext,
                value.nonce,
                value.version,
                str(message_id),
                str(conversation_id),
            ),
        )

    async def get_display_content(
        self, message_id: UUID, conversation_id: UUID
    ) -> bytes | None:
        """Authenticate cached display content, returning None when not retained."""
        row = await self._database.fetch_one(
            "SELECT display_ciphertext, display_nonce, display_format_version "
            "FROM cached_messages WHERE message_id = ? AND conversation_id = ?",
            (str(message_id), str(conversation_id)),
        )
        if row is None or row[0] is None:
            return None
        return await self._encryption.decrypt(
            LocalEncryptionPurpose.MESSAGE_CACHE,
            EncryptedLocalValue(int(row[2]), bytes(row[1]), bytes(row[0])),
            self._context(message_id, conversation_id),
        )

    def _context(self, message_id: UUID, conversation_id: UUID) -> bytes:
        return f"{self._profile_id}:{message_id}:{conversation_id}:message:1".encode(
            "ascii"
        )
