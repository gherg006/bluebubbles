"""Server-owned user, role, permission, and public-key domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from bluebubbles.server.domain.common import BaseEntity
from bluebubbles.shared.models.users import PresenceState


class Permission(StrEnum):
    """Define stable authority names used by server policy checks."""

    SEND_MESSAGE = "send_message"
    DELETE_MESSAGE = "delete_message"
    CREATE_GROUP = "create_group"
    DELETE_GROUP = "delete_group"
    UPLOAD_FILE = "upload_file"
    DOWNLOAD_FILE = "download_file"
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOG = "view_audit_log"
    SEND_ANNOUNCEMENTS = "send_announcements"
    MANAGE_SERVER = "manage_server"
    ADMIN_DASHBOARD = "admin.dashboard"
    USER_VIEW = "user.view"
    USER_SEARCH = "user.search"
    USER_ENABLE = "user.enable"
    USER_DISABLE = "user.disable"
    USER_ASSIGN_ROLE = "user.assign_role"
    USER_ASSIGN_SUPER_ROLE = "user.assign_super_role"
    SESSION_VIEW = "session.view"
    SESSION_REVOKE = "session.revoke"
    CONNECTION_VIEW = "connection.view"
    CONNECTION_DISCONNECT = "connection.disconnect"
    AUDIT_VIEW = "audit.view"
    AUDIT_VIEW_LIMITED = "audit.view_limited"
    AUDIT_EXPORT = "audit.export"
    AUDIT_VERIFY = "audit.verify"
    ALERT_VIEW = "alert.view"
    ALERT_ACKNOWLEDGE = "alert.acknowledge"
    ALERT_RESOLVE = "alert.resolve"
    ANNOUNCEMENT_MANAGE = "announcement.manage"
    HEALTH_VIEW_DETAILED = "health.view_detailed"
    WORKER_VIEW = "worker.view"
    WORKER_RUN = "worker.run"
    WORKER_CONTROL = "worker.control"
    CONFIGURATION_VIEW = "configuration.view"
    CONFIGURATION_MODIFY = "configuration.modify"
    EXPORT_MANAGE = "export.manage"
    SYSTEM_MAINTENANCE = "system.maintenance"
    DIAGNOSTIC_RUN = "diagnostic.run"


@dataclass(frozen=True, slots=True)
class Role:
    """Group a named, immutable set of permissions."""

    id: UUID
    name: str
    permissions: frozenset[Permission] = frozenset()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Role name is required")

    def has_permission(self, permission: Permission) -> bool:
        """Return whether the role grants ``permission``."""
        return permission in self.permissions


@dataclass(kw_only=True)
class PublicKeyRecord(BaseEntity):
    """Store only one versioned public encryption or signing key."""

    user_id: UUID
    key_version: int
    algorithm: str
    public_key: bytes
    fingerprint: str
    key_type: str = "encryption"
    expires_at: datetime | None = None
    is_primary: bool = True
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.key_type not in {"encryption", "signing"}:
            raise ValueError("Public key type must be encryption or signing")
        if self.key_version < 1 or not self.public_key or not self.fingerprint:
            raise ValueError("Public key material and a positive version are required")


@dataclass(kw_only=True)
class LocalCredential(BaseEntity):
    """Represent a server-managed password verifier, never a plaintext password."""

    user_id: UUID
    password_hash: str = field(repr=False)
    requires_reset: bool = False
    failed_attempts: int = 0
    locked_until: datetime | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.password_hash or self.failed_attempts < 0:
            raise ValueError(
                "A password hash and non-negative failure count are required"
            )


@dataclass(kw_only=True)
class User(BaseEntity):
    """Represent authoritative server-side user identity and profile metadata."""

    username: str
    display_name: str
    role_id: UUID
    email: str | None = None
    department: str | None = None
    job_title: str | None = None
    active_directory_guid: UUID | None = None
    profile_picture_reference: str | None = None
    status_message: str | None = None
    presence: PresenceState = PresenceState.OFFLINE
    is_enabled: bool = True
    last_login: datetime | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.username = normalise_username(self.username)
        self.display_name = self.display_name.strip()
        if not self.display_name:
            raise ValueError("Display name is required")

    def update_profile(
        self,
        *,
        display_name: str,
        status_message: str | None,
        at: datetime | None = None,
    ) -> None:
        """Update client-editable profile fields while enforcing invariants."""
        display_name = display_name.strip()
        if not display_name:
            raise ValueError("Display name is required")
        self.display_name = display_name
        self.status_message = status_message.strip() if status_message else None
        self.touch(at)

    def change_presence(
        self, presence: PresenceState, at: datetime | None = None
    ) -> None:
        """Set current presence metadata."""
        self.presence = presence
        self.touch(at)

    def disable(self, at: datetime | None = None) -> None:
        """Disable logins for this user."""
        if self.is_enabled:
            self.is_enabled = False
            self.touch(at)


def normalise_username(username: str) -> str:
    """Return the canonical, case-insensitive username representation."""
    normalised = username.strip().casefold()
    if not normalised or len(normalised) > 128:
        raise ValueError("Username must contain between 1 and 128 characters")
    return normalised


def can_assign_role(actor: Role, target: Role) -> bool:
    """Require user management authority and prevent self-created super roles."""
    return actor.has_permission(Permission.MANAGE_USERS) and (
        target.permissions <= actor.permissions
    )


def can_disable_target(actor: User, target: User, actor_role: Role) -> bool:
    """Return whether an actor may disable another enabled user."""
    return (
        actor.id != target.id
        and target.is_enabled
        and actor_role.has_permission(Permission.MANAGE_USERS)
    )
