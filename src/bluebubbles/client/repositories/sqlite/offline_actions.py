"""Encrypted durable repository for ciphertext-only offline actions."""

from __future__ import annotations

import base64
from datetime import datetime
from uuid import UUID

from bluebubbles.client.domain.offline_actions import OfflineAction, OfflineActionState
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


class SQLiteOfflineActionRepository:
    """Persist retry state while hiding prepared envelopes and metadata at rest."""

    def __init__(
        self,
        database: LocalDatabaseManager,
        encryption: LocalEncryptionService,
        profile_id: UUID,
    ) -> None:
        self._database = database
        self._encryption = encryption
        self._profile_id = profile_id

    async def save(self, action: OfflineAction) -> None:
        """Encrypt and upsert one stable idempotent action."""
        value = await self._encryption.encrypt(
            LocalEncryptionPurpose.OFFLINE_QUEUE,
            encode_json(
                {
                    "payload": base64.b64encode(action.encrypted_payload).decode(
                        "ascii"
                    ),
                    "last_error_code": action.last_error_code,
                }
            ),
            self._context(action.id, action.action_type),
        )
        await self._database.execute(
            "INSERT INTO offline_actions(action_id, action_type, ciphertext, nonce, "
            "format_version, created_at, attempt_count, next_attempt_at, "
            "last_error_code, status, idempotency_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?) ON CONFLICT(action_id) DO UPDATE SET "
            "ciphertext=excluded.ciphertext, "
            "nonce=excluded.nonce, format_version=excluded.format_version, "
            "attempt_count=excluded.attempt_count, "
            "next_attempt_at=excluded.next_attempt_at, "
            "last_error_code=excluded.last_error_code, "
            "status=excluded.status",
            (
                str(action.id),
                action.action_type,
                value.ciphertext,
                value.nonce,
                value.version,
                action.created_at.isoformat(),
                action.attempts,
                action.next_attempt_at.isoformat() if action.next_attempt_at else None,
                action.last_error_code,
                action.state.value,
                str(action.idempotency_key),
            ),
        )

    async def get(self, action_id: UUID) -> OfflineAction | None:
        """Authenticate one queued action by identifier."""
        row = await self._database.fetch_one(
            "SELECT action_type, ciphertext, nonce, format_version, created_at, "
            "attempt_count, next_attempt_at, last_error_code, status, idempotency_key "
            "FROM offline_actions WHERE action_id = ?",
            (str(action_id),),
        )
        if row is None:
            return None
        action_type = str(row[0])
        plaintext = await self._encryption.decrypt(
            LocalEncryptionPurpose.OFFLINE_QUEUE,
            EncryptedLocalValue(int(row[3]), bytes(row[2]), bytes(row[1])),
            self._context(action_id, action_type),
        )
        data = decode_json(plaintext)
        return OfflineAction(
            id=action_id,
            action_type=action_type,
            idempotency_key=UUID(str(row[9])),
            encrypted_payload=base64.b64decode(str(data["payload"]), validate=True),
            created_at=datetime.fromisoformat(str(row[4])),
            next_attempt_at=(
                datetime.fromisoformat(str(row[6])) if row[6] is not None else None
            ),
            state=OfflineActionState(str(row[8])),
            attempts=int(row[5]),
            last_error_code=str(row[7]) if row[7] is not None else None,
        )

    async def list_pending(self) -> list[OfflineAction]:
        """Return recoverable actions in stable creation order."""
        rows = await self._database.fetch_all(
            "SELECT action_id FROM offline_actions WHERE status IN (?, ?) "
            "ORDER BY created_at ASC, action_id ASC",
            (OfflineActionState.PENDING.value, OfflineActionState.FAILED.value),
        )
        actions: list[OfflineAction] = []
        for row in rows:
            action = await self.get(UUID(str(row[0])))
            if action is not None:
                actions.append(action)
        return actions

    async def delete(self, action_id: UUID) -> None:
        """Delete a resolved or explicitly cancelled action."""
        await self._database.execute(
            "DELETE FROM offline_actions WHERE action_id = ?", (str(action_id),)
        )

    def _context(self, action_id: UUID, action_type: str) -> bytes:
        return f"{self._profile_id}:{action_id}:{action_type}:1".encode()
