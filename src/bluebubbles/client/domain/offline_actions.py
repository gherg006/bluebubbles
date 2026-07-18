"""Validated client offline-action state, execution results and summaries."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID


class OfflineActionType(StrEnum):
    """Define the bounded set of writes that Version 1 may replay."""

    SEND_MESSAGE = "send_message"
    EDIT_PENDING_MESSAGE = "edit_pending_message"
    CANCEL_PENDING_MESSAGE = "cancel_pending_message"
    MARK_READ = "mark_read"
    UPDATE_CONVERSATION_PREFERENCE = "update_conversation_preference"
    ACKNOWLEDGE_ANNOUNCEMENT = "acknowledge_announcement"
    RESUME_ATTACHMENT_UPLOAD = "resume_attachment_upload"
    DELIVERY_ACKNOWLEDGEMENT = "delivery_acknowledgement"
    ADD_REACTION = "add_reaction"
    REMOVE_REACTION = "remove_reaction"


class OfflineActionState(StrEnum):
    """Define explicit durable queue states and legacy-compatible aliases."""

    PENDING = "pending"
    READY = "ready"
    PROCESSING = "processing"
    RETRY_WAIT = "retry_wait"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED_PERMANENT = "failed_permanent"
    CANCELLED = "cancelled"
    # Task 16 compatibility names. Enum aliases preserve old callers and rows.
    IN_PROGRESS = "processing"
    COMPLETE = "completed"
    FAILED = "retry_wait"


class OfflineActionOutcome(StrEnum):
    """Classify executor results without parsing human-readable error text."""

    SUCCEEDED = "succeeded"
    RETRYABLE_FAILURE = "retryable_failure"
    BLOCKED = "blocked"
    PERMANENT_FAILURE = "permanent_failure"


_ALLOWED_TRANSITIONS: dict[OfflineActionState, frozenset[OfflineActionState]] = {
    OfflineActionState.PENDING: frozenset(
        {OfflineActionState.READY, OfflineActionState.CANCELLED}
    ),
    OfflineActionState.READY: frozenset(
        {OfflineActionState.PROCESSING, OfflineActionState.CANCELLED}
    ),
    OfflineActionState.PROCESSING: frozenset(
        {
            OfflineActionState.COMPLETED,
            OfflineActionState.RETRY_WAIT,
            OfflineActionState.BLOCKED,
            OfflineActionState.FAILED_PERMANENT,
        }
    ),
    OfflineActionState.RETRY_WAIT: frozenset(
        {OfflineActionState.READY, OfflineActionState.CANCELLED}
    ),
    OfflineActionState.BLOCKED: frozenset(
        {
            OfflineActionState.READY,
            OfflineActionState.FAILED_PERMANENT,
            OfflineActionState.CANCELLED,
        }
    ),
}


@dataclass(frozen=True, slots=True)
class OfflineAction:
    """Represent one locally protected, stable and idempotent queued write."""

    id: UUID
    action_type: str
    idempotency_key: UUID | str
    encrypted_payload: bytes
    created_at: datetime
    next_attempt_at: datetime | None = None
    state: OfflineActionState = OfflineActionState.PENDING
    attempts: int = 0
    last_error_code: str | None = None
    user_id: UUID | None = None
    scope_type: str = "global"
    scope_id: UUID | None = None
    sequence_number: int = 0
    updated_at: datetime | None = None
    dependency_action_id: UUID | None = None
    server_reference: UUID | None = None

    def __post_init__(self) -> None:
        """Reject malformed scheduling metadata before it reaches storage."""
        if (
            not self.action_type
            or not self.encrypted_payload
            or not str(self.idempotency_key)
            or not self.scope_type
            or self.attempts < 0
            or self.sequence_number < 0
        ):
            raise ValueError("Offline action metadata is incomplete")

    def transition(
        self,
        state: OfflineActionState,
        *,
        now: datetime | None = None,
        next_attempt_at: datetime | None = None,
        failure_code: str | None = None,
        server_reference: UUID | None = None,
    ) -> OfflineAction:
        """Return a validated state transition with updated retry metadata."""
        if state not in _ALLOWED_TRANSITIONS.get(self.state, frozenset()):
            raise ValueError("Offline action transition is not allowed")
        attempts = self.attempts + (state is OfflineActionState.PROCESSING)
        return replace(
            self,
            state=state,
            attempts=attempts,
            updated_at=now or datetime.now(UTC),
            next_attempt_at=next_attempt_at,
            last_error_code=failure_code,
            server_reference=server_reference or self.server_reference,
        )

    def begin(self) -> OfflineAction:
        """Return a processing attempt, promoting legacy pending records first."""
        action = self
        if action.state in {OfflineActionState.PENDING, OfflineActionState.RETRY_WAIT}:
            action = action.transition(OfflineActionState.READY)
        return action.transition(OfflineActionState.PROCESSING)


@dataclass(frozen=True, slots=True)
class PendingOfflineAction:
    """Describe a new action before sequence and timestamps are assigned."""

    user_id: UUID
    action_type: OfflineActionType
    idempotency_key: UUID | str
    encrypted_payload: bytes
    scope_type: str = "global"
    scope_id: UUID | None = None
    dependency_action_id: UUID | None = None
    action_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class OfflineActionExecutionResult:
    """Return the executor's safe, machine-readable action classification."""

    outcome: OfflineActionOutcome
    server_reference: UUID | None = None
    failure_code: str | None = None
    retry_after: datetime | None = None
    replacement_required: bool = False
    user_action_required: bool = False


@dataclass(frozen=True, slots=True)
class OfflineActionSummary:
    """Expose queue metadata to presentation without revealing its payload."""

    action_id: UUID
    action_type: OfflineActionType
    state: OfflineActionState
    created_at: datetime
    attempt_count: int
    failure_code: str | None
    scope_id: UUID | None


@dataclass(frozen=True, slots=True)
class QueueProcessingResult:
    """Summarise one serial queue pass."""

    processed: int = 0
    completed: int = 0
    retrying: int = 0
    blocked: int = 0
    permanently_failed: int = 0
    already_running: bool = False
