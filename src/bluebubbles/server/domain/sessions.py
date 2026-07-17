"""Server-side authentication session domain rules."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from bluebubbles.server.domain.common import BaseEntity


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """Carry immutable identity and authority through one authenticated request."""

    user_id: UUID
    session_id: UUID
    username: str
    role_id: UUID
    permissions: frozenset[str]


@dataclass(kw_only=True)
class Session(BaseEntity):
    """Represent an opaque-token session without retaining raw token values."""

    user_id: UUID
    refresh_token_hash: str
    expires_at: datetime
    idle_expires_at: datetime
    ip_address: str
    device_name: str
    platform: str
    login_time: datetime
    device_id: UUID | None = None
    previous_refresh_token_hash: str | None = None
    invalidated_at: datetime | None = None
    invalidation_reason: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.refresh_token_hash:
            raise ValueError("Refresh-token hash is required")
        if self.expires_at.tzinfo is None or self.idle_expires_at.tzinfo is None:
            raise ValueError("Session expiry timestamps must be timezone-aware")

    def is_expired(self, at: datetime) -> bool:
        """Return whether either the access or absolute session limit has passed."""
        return at >= min(self.expires_at, self.idle_expires_at)

    def is_access_expired(self, at: datetime) -> bool:
        """Return whether the current short-lived access period has passed."""
        return at >= self.idle_expires_at

    def is_active(self, at: datetime) -> bool:
        """Return whether this non-deleted session remains usable."""
        return (
            not self.is_deleted
            and self.invalidated_at is None
            and not self.is_expired(at)
        )

    def can_refresh(self, at: datetime) -> bool:
        """Return whether protected refresh rotation may proceed."""
        return (
            not self.is_deleted and self.invalidated_at is None and at < self.expires_at
        )

    def invalidate(self, at: datetime, reason: str) -> None:
        """Irreversibly invalidate the session with an auditable reason."""
        if at.tzinfo is None or not reason.strip():
            raise ValueError("An aware timestamp and reason are required")
        if self.invalidated_at is None:
            self.invalidated_at = at
            self.invalidation_reason = reason.strip()
            self.touch(at)

    @property
    def access_expires_at(self) -> datetime:
        """Return the access-token expiry retained by the persistence schema."""
        return self.idle_expires_at

    @property
    def refresh_expires_at(self) -> datetime:
        """Return the absolute refresh expiry retained by the persistence schema."""
        return self.expires_at


@dataclass(kw_only=True)
class LoginAttempt(BaseEntity):
    """Record safe metadata about an authentication attempt."""

    username_fingerprint: str
    source_address: str
    attempted_at: datetime
    succeeded: bool
    failure_code: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.username_fingerprint or self.attempted_at.tzinfo is None:
            raise ValueError(
                "Login attempt fingerprint and aware timestamp are required"
            )
