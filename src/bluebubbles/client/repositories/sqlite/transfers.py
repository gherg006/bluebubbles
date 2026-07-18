"""Encrypted SQLite persistence for resumable transfer snapshots."""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from uuid import UUID

from bluebubbles.client.domain.transfers import (
    FileTransfer,
    TransferDirection,
    TransferProgress,
    TransferRecovery,
    TransferState,
)
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


class SQLiteTransferStateRepository:
    """Store sensitive transfer progress in profile-bound encrypted records."""

    def __init__(
        self,
        database: LocalDatabaseManager,
        encryption: LocalEncryptionService,
        profile_id: UUID,
    ) -> None:
        self._database = database
        self._encryption = encryption
        self._profile_id = profile_id

    async def save(self, transfer: FileTransfer) -> None:
        """Encrypt and upsert one transfer snapshot."""
        now = datetime.now().astimezone()
        value = await self._encryption.encrypt(
            LocalEncryptionPurpose.TRANSFER_STATE,
            encode_json(
                {
                    "transferred_bytes": transfer.progress.transferred_bytes,
                    "total_bytes": transfer.progress.total_bytes,
                    "bytes_per_second": transfer.progress.bytes_per_second,
                    "estimated_remaining_seconds": (
                        transfer.progress.estimated_remaining_seconds
                    ),
                    "error_code": transfer.error_code,
                    "recovery": (
                        {
                            "temporary_path": str(transfer.recovery.temporary_path),
                            "upload_id": (
                                str(transfer.recovery.upload_id)
                                if transfer.recovery.upload_id
                                else None
                            ),
                            "destination_path": (
                                str(transfer.recovery.destination_path)
                                if transfer.recovery.destination_path
                                else None
                            ),
                            "confirmed_chunks": list(
                                transfer.recovery.confirmed_chunks
                            ),
                            "session_expires_at": (
                                transfer.recovery.session_expires_at.isoformat()
                                if transfer.recovery.session_expires_at
                                else None
                            ),
                            "file_key": (
                                base64.b64encode(transfer.recovery.file_key).decode(
                                    "ascii"
                                )
                                if transfer.recovery.file_key
                                else None
                            ),
                        }
                        if transfer.recovery is not None
                        else None
                    ),
                }
            ),
            self._context(transfer.id, transfer.attachment_id),
        )
        await self._database.execute(
            "INSERT INTO transfer_states(transfer_id, attachment_id, direction, "
            "ciphertext, nonce, format_version, status, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(transfer_id) DO UPDATE SET "
            "ciphertext=excluded.ciphertext, nonce=excluded.nonce, "
            "format_version=excluded.format_version, status=excluded.status, "
            "updated_at=excluded.updated_at",
            (
                str(transfer.id),
                str(transfer.attachment_id),
                transfer.direction.value,
                value.ciphertext,
                value.nonce,
                value.version,
                transfer.state.value,
                now.isoformat(),
            ),
        )

    async def get(self, transfer_id: UUID) -> FileTransfer | None:
        """Authenticate and return one transfer snapshot."""
        row = await self._database.fetch_one(
            "SELECT attachment_id, direction, ciphertext, nonce, format_version, "
            "status FROM transfer_states WHERE transfer_id = ?",
            (str(transfer_id),),
        )
        if row is None:
            return None
        attachment_id = UUID(str(row[0]))
        plaintext = await self._encryption.decrypt(
            LocalEncryptionPurpose.TRANSFER_STATE,
            EncryptedLocalValue(int(row[4]), bytes(row[3]), bytes(row[2])),
            self._context(transfer_id, attachment_id),
        )
        data = decode_json(plaintext)
        progress = TransferProgress(
            int(data["transferred_bytes"]),
            int(data["total_bytes"]),
            float(data["bytes_per_second"]),
            (
                float(data["estimated_remaining_seconds"])
                if data.get("estimated_remaining_seconds") is not None
                else None
            ),
        )
        recovery_data = data.get("recovery")
        recovery = None
        if isinstance(recovery_data, dict):
            recovery = TransferRecovery(
                temporary_path=Path(str(recovery_data["temporary_path"])),
                upload_id=(
                    UUID(str(recovery_data["upload_id"]))
                    if recovery_data.get("upload_id")
                    else None
                ),
                destination_path=(
                    Path(str(recovery_data["destination_path"]))
                    if recovery_data.get("destination_path")
                    else None
                ),
                confirmed_chunks=tuple(
                    int(item) for item in recovery_data.get("confirmed_chunks", [])
                ),
                session_expires_at=(
                    datetime.fromisoformat(str(recovery_data["session_expires_at"]))
                    if recovery_data.get("session_expires_at")
                    else None
                ),
                file_key=(
                    base64.b64decode(str(recovery_data["file_key"]), validate=True)
                    if recovery_data.get("file_key")
                    else None
                ),
            )
        return FileTransfer(
            id=transfer_id,
            attachment_id=attachment_id,
            direction=TransferDirection(str(row[1])),
            state=TransferState(str(row[5])),
            progress=progress,
            error_code=str(data["error_code"]) if data.get("error_code") else None,
            recovery=recovery,
        )

    async def list_incomplete(self) -> list[FileTransfer]:
        """Return non-terminal transfers for restart recovery."""
        rows = await self._database.fetch_all(
            "SELECT transfer_id FROM transfer_states WHERE status NOT IN (?, ?) "
            "ORDER BY updated_at ASC",
            (TransferState.COMPLETE.value, TransferState.CANCELLED.value),
        )
        transfers: list[FileTransfer] = []
        for row in rows:
            transfer = await self.get(UUID(str(row[0])))
            if transfer is not None:
                transfers.append(transfer)
        return transfers

    async def delete(self, transfer_id: UUID) -> None:
        """Delete resolved recovery state idempotently."""
        await self._database.execute(
            "DELETE FROM transfer_states WHERE transfer_id = ?", (str(transfer_id),)
        )

    def _context(self, transfer_id: UUID, attachment_id: UUID) -> bytes:
        return f"{self._profile_id}:{transfer_id}:{attachment_id}:transfer:1".encode(
            "ascii"
        )
