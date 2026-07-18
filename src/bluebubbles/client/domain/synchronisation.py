"""Connectivity, synchronisation, tombstone and conflict value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ConnectivityState(StrEnum):
    """Define user-visible client connectivity states."""

    STARTING = "starting"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SYNCHRONISING = "synchronising"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    REAUTHENTICATION_REQUIRED = "reauthentication_required"
    SHUTTING_DOWN = "shutting_down"


class SynchronisationScope(StrEnum):
    """Define authoritative server scopes that may be reconciled."""

    PROTOCOL = "protocol"
    CURRENT_USER = "current_user"
    POLICIES = "policies"
    CONVERSATIONS = "conversations"
    CONVERSATION_MEMBERSHIP = "conversation_membership"
    MESSAGES = "messages"
    PUBLIC_KEYS = "public_keys"
    ANNOUNCEMENTS = "announcements"
    SESSIONS = "sessions"
    ADMIN_CAPABILITIES = "admin_capabilities"
    TRANSFERS = "transfers"


class ConflictCategory(StrEnum):
    """Classify conflicts with an explicit recovery policy."""

    VERSION_CONFLICT = "version_conflict"
    MEMBERSHIP_CONFLICT = "membership_conflict"
    PERMISSION_CONFLICT = "permission_conflict"
    KEY_CONFLICT = "key_conflict"
    DELETION_CONFLICT = "deletion_conflict"
    ATTACHMENT_CONFLICT = "attachment_conflict"
    PROTOCOL_CONFLICT = "protocol_conflict"
    DUPLICATE_ID_CONFLICT = "duplicate_id_conflict"
    POLICY_CONFLICT = "policy_conflict"


class ConflictResolution(StrEnum):
    """Describe whether a conflict was safely resolved or needs a person."""

    EQUIVALENT_SUCCESS = "equivalent_success"
    SERVER_STATE_ACCEPTED = "server_state_accepted"
    ACTION_BLOCKED = "action_blocked"
    REBUILD_REQUIRED = "rebuild_required"
    USER_INPUT_REQUIRED = "user_input_required"


@dataclass(frozen=True, slots=True)
class SynchronisationConflict:
    """Persist safe conflict metadata without plaintext user content."""

    conflict_id: UUID
    category: ConflictCategory
    scope: SynchronisationScope
    scope_id: UUID | None
    action_id: UUID | None
    detected_at: datetime
    failure_code: str
    attempted_content_preserved: bool = False
    resolved_at: datetime | None = None
    resolution: ConflictResolution | None = None


@dataclass(frozen=True, slots=True)
class LocalTombstone:
    """Prevent confirmed unavailable server state from being recreated stale."""

    scope: SynchronisationScope
    resource_id: UUID
    server_version: int | None
    created_at: datetime
    reason_code: str


@dataclass(frozen=True, slots=True)
class SynchronisationResult:
    """Summarise a completed or degraded synchronisation run."""

    started_at: datetime
    completed_at: datetime
    scopes_succeeded: tuple[str, ...]
    scopes_failed: tuple[str, ...]
    conversations_updated: int = 0
    messages_added: int = 0
    messages_updated: int = 0
    tombstones_applied: int = 0
    queue_actions_unblocked: int = 0
    requires_reauthentication: bool = False
    degraded: bool = False


@dataclass(frozen=True, slots=True)
class ScopeSynchronisationResult:
    """Return validated records and checkpoint metadata from one scope adapter."""

    scope: SynchronisationScope
    scope_id: UUID | None = None
    cursor: str | None = None
    version: int | None = None
    conversations_updated: int = 0
    messages_added: int = 0
    messages_updated: int = 0
    tombstones_applied: int = 0


@dataclass(slots=True)
class CancellationToken:
    """Provide cooperative cancellation at synchronisation page boundaries."""

    cancelled: bool = False

    def cancel(self) -> None:
        """Request cancellation before the next safe boundary."""
        self.cancelled = True
