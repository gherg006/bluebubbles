"""Encrypted durable repository for ordered offline actions."""

from __future__ import annotations

import base64
from dataclasses import replace
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
    """Persist protected queue payloads and non-sensitive scheduling metadata."""

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
        """Encrypt and upsert one action without changing its idempotency identity."""
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
            self._context(action),
        )
        await self._database.execute(
            "INSERT INTO offline_actions(action_id, action_type, ciphertext, nonce, "
            "format_version, created_at, attempt_count, next_attempt_at, "
            "last_error_code, status, idempotency_key, user_id, scope_type, scope_id, "
            "sequence_number, updated_at, dependency_action_id, server_reference) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(action_id) DO UPDATE SET ciphertext=excluded.ciphertext, "
            "nonce=excluded.nonce, format_version=excluded.format_version, "
            "attempt_count=excluded.attempt_count, "
            "next_attempt_at=excluded.next_attempt_at, "
            "last_error_code=excluded.last_error_code, status=excluded.status, "
            "updated_at=excluded.updated_at, "
            "dependency_action_id=excluded.dependency_action_id, "
            "server_reference=excluded.server_reference",
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
                str(action.user_id) if action.user_id else None,
                action.scope_type,
                str(action.scope_id) if action.scope_id else None,
                action.sequence_number,
                action.updated_at.isoformat() if action.updated_at else None,
                (
                    str(action.dependency_action_id)
                    if action.dependency_action_id
                    else None
                ),
                str(action.server_reference) if action.server_reference else None,
            ),
        )

    async def get(self, action_id: UUID) -> OfflineAction | None:
        """Authenticate and return one queued action by identifier."""
        row = await self._database.fetch_one(
            "SELECT action_type, ciphertext, nonce, format_version, created_at, "
            "attempt_count, next_attempt_at, last_error_code, status, idempotency_key, "
            "user_id, scope_type, scope_id, sequence_number, updated_at, "
            "dependency_action_id, server_reference FROM offline_actions "
            "WHERE action_id = ?",
            (str(action_id),),
        )
        if row is None:
            return None
        action = OfflineAction(
            id=action_id,
            action_type=str(row[0]),
            idempotency_key=self._parse_idempotency_key(str(row[9])),
            encrypted_payload=b"protected",
            created_at=datetime.fromisoformat(str(row[4])),
            next_attempt_at=(
                datetime.fromisoformat(str(row[6])) if row[6] is not None else None
            ),
            state=OfflineActionState(str(row[8])),
            attempts=int(row[5]),
            last_error_code=str(row[7]) if row[7] is not None else None,
            user_id=UUID(str(row[10])) if row[10] else None,
            scope_type=str(row[11]),
            scope_id=UUID(str(row[12])) if row[12] else None,
            sequence_number=int(row[13]),
            updated_at=datetime.fromisoformat(str(row[14])) if row[14] else None,
            dependency_action_id=UUID(str(row[15])) if row[15] else None,
            server_reference=UUID(str(row[16])) if row[16] else None,
        )
        plaintext = await self._encryption.decrypt(
            LocalEncryptionPurpose.OFFLINE_QUEUE,
            EncryptedLocalValue(int(row[3]), bytes(row[2]), bytes(row[1])),
            self._context(action),
        )
        data = decode_json(plaintext)
        return replace(
            action,
            encrypted_payload=base64.b64decode(str(data["payload"]), validate=True),
        )

    async def list_pending(self) -> list[OfflineAction]:
        """Return every non-terminal recoverable action in deterministic order."""
        return await self.list_by_states(
            frozenset(
                {
                    OfflineActionState.PENDING,
                    OfflineActionState.READY,
                    OfflineActionState.PROCESSING,
                    OfflineActionState.RETRY_WAIT,
                    OfflineActionState.BLOCKED,
                }
            )
        )

    async def list_by_states(
        self, states: frozenset[OfflineActionState]
    ) -> list[OfflineAction]:
        """Return matching actions by monotonic sequence and creation fallback."""
        if not states:
            return []
        rows = await self._database.fetch_all(
            "SELECT action_id, status FROM offline_actions "
            "ORDER BY CASE WHEN sequence_number = 0 THEN 1 ELSE 0 END, "
            "sequence_number ASC, created_at ASC, action_id ASC",
        )
        actions: list[OfflineAction] = []
        for row in rows:
            if OfflineActionState(str(row[1])) not in states:
                continue
            action = await self.get(UUID(str(row[0])))
            if action is not None:
                actions.append(action)
        return actions

    async def next_sequence_number(self) -> int:
        """Allocate the next profile-local monotonic queue sequence."""
        row = await self._database.fetch_one(
            "SELECT COALESCE(MAX(sequence_number), 0) + 1 FROM offline_actions"
        )
        return 1 if row is None else int(row[0])

    async def delete(self, action_id: UUID) -> None:
        """Delete only an explicitly removed queue record."""
        await self._database.execute(
            "DELETE FROM offline_actions WHERE action_id = ?", (str(action_id),)
        )

    def _context(self, action: OfflineAction) -> bytes:
        if action.sequence_number == 0:
            return f"{self._profile_id}:{action.id}:{action.action_type}:1".encode()
        user = action.user_id or self._profile_id
        return (
            f"{user}:{action.id}:{action.action_type}:{action.sequence_number}:1"
        ).encode("ascii")

    @staticmethod
    def _parse_idempotency_key(value: str) -> UUID | str:
        try:
            return UUID(value)
        except ValueError:
            return value
