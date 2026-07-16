"""Client file-transfer state machine and encrypted chunk value objects."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum
from pathlib import Path
from uuid import UUID


class TransferState(StrEnum):
    """Define the local lifecycle for an upload or download."""

    QUEUED = "queued"
    PREPARING = "preparing"
    TRANSFERRING = "transferring"
    PAUSED = "paused"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransferDirection(StrEnum):
    """Distinguish client upload and download operations."""

    UPLOAD = "upload"
    DOWNLOAD = "download"


@dataclass(frozen=True, slots=True)
class TransferProgress:
    """Represent bounded progress without mutable cross-thread state."""

    transferred_bytes: int
    total_bytes: int
    bytes_per_second: float = 0.0
    estimated_remaining_seconds: float | None = None

    def __post_init__(self) -> None:
        if self.total_bytes <= 0 or not 0 <= self.transferred_bytes <= self.total_bytes:
            raise ValueError("Transfer progress is outside its valid range")
        if self.bytes_per_second < 0:
            raise ValueError("Transfer speed cannot be negative")


@dataclass(frozen=True, slots=True)
class EncryptedChunk:
    """Hold one ciphertext chunk ready for network transfer."""

    index: int
    ciphertext: bytes = field(repr=False)
    nonce: bytes = field(repr=False)
    checksum: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if self.index < 0 or not self.ciphertext or not self.nonce or not self.checksum:
            raise ValueError("Encrypted chunk data is incomplete")


@dataclass(frozen=True, slots=True)
class PreparedUpload:
    """Describe locally encrypted upload material and safe display metadata."""

    attachment_id: UUID
    encrypted_path: Path
    display_filename: str
    encrypted_size: int
    original_size: int
    chunk_size: int
    checksum: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if (
            not self.display_filename
            or self.encrypted_size <= 0
            or self.chunk_size <= 0
        ):
            raise ValueError("Prepared upload metadata is incomplete")


@dataclass(frozen=True, slots=True)
class FileTransfer:
    """Represent one immutable client transfer-state snapshot."""

    id: UUID
    attachment_id: UUID
    direction: TransferDirection
    state: TransferState
    progress: TransferProgress
    error_code: str | None = None

    def transition(self, target: TransferState) -> FileTransfer:
        """Return a new state after validating the transition graph."""
        allowed = {
            TransferState.QUEUED: {TransferState.PREPARING, TransferState.CANCELLED},
            TransferState.PREPARING: {
                TransferState.TRANSFERRING,
                TransferState.FAILED,
                TransferState.CANCELLED,
            },
            TransferState.TRANSFERRING: {
                TransferState.PAUSED,
                TransferState.VERIFYING,
                TransferState.FAILED,
                TransferState.CANCELLED,
            },
            TransferState.PAUSED: {TransferState.TRANSFERRING, TransferState.CANCELLED},
            TransferState.VERIFYING: {TransferState.COMPLETE, TransferState.FAILED},
            TransferState.COMPLETE: set(),
            TransferState.FAILED: {TransferState.QUEUED, TransferState.CANCELLED},
            TransferState.CANCELLED: set(),
        }
        if target not in allowed[self.state]:
            raise ValueError(f"Invalid transfer transition: {self.state} -> {target}")
        error_code = self.error_code if target is TransferState.FAILED else None
        return replace(self, state=target, error_code=error_code)

    def update_progress(self, progress: TransferProgress) -> FileTransfer:
        """Return a new transfer snapshot with monotonic progress."""
        if progress.total_bytes != self.progress.total_bytes:
            raise ValueError("Transfer total cannot change")
        if progress.transferred_bytes < self.progress.transferred_bytes:
            raise ValueError("Transfer progress cannot move backwards")
        return replace(self, progress=progress)
