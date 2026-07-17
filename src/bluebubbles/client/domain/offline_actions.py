"""Immutable client offline-action state and retry metadata."""

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class OfflineActionState(StrEnum):
    """Define durable local queue action states."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class OfflineAction:
    """Represent an idempotent local action awaiting server submission."""

    id: UUID
    action_type: str
    idempotency_key: UUID
    encrypted_payload: bytes
    created_at: datetime
    next_attempt_at: datetime | None = None
    state: OfflineActionState = OfflineActionState.PENDING
    attempts: int = 0
    last_error_code: str | None = None

    def __post_init__(self) -> None:
        if not self.action_type or not self.encrypted_payload or self.attempts < 0:
            raise ValueError("Offline action metadata is incomplete")

    def begin(self) -> "OfflineAction":
        """Return an in-progress retry attempt."""
        if self.state not in {OfflineActionState.PENDING, OfflineActionState.FAILED}:
            raise ValueError("Offline action cannot begin in its current state")
        return replace(
            self, state=OfflineActionState.IN_PROGRESS, attempts=self.attempts + 1
        )
