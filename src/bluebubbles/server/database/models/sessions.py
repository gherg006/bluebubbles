"""Authentication session, login-attempt, and policy persistence mappings."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from bluebubbles.server.database.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

IP_ADDRESS_TYPE = String(45).with_variant(INET(), "postgresql")


class SessionORM(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """Map one device-scoped opaque-token session."""

    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint(
            "access_expires_at <= refresh_expires_at", name="expiry_order_valid"
        ),
        CheckConstraint("token_version >= 1", name="token_version_positive"),
        CheckConstraint(
            "is_active OR invalidated_at IS NOT NULL", name="inactive_has_timestamp"
        ),
        Index("ix_sessions_user_active", "user_id", "is_active"),
        Index("ix_sessions_refresh_expiry", "refresh_expires_at"),
        Index("ix_sessions_device", "user_id", "device_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    device_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    device_name: Mapped[str] = mapped_column(String(200), nullable=False)
    client_version: Mapped[str] = mapped_column(String(50), nullable=False)
    source_ip: Mapped[str | None] = mapped_column(IP_ADDRESS_TYPE)
    refresh_token_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    access_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    refresh_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invalidation_reason: Mapped[str | None] = mapped_column(String(200))
    token_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )


class LoginAttemptORM(Base, UUIDPrimaryKeyMixin):
    """Map password-free authentication-attempt metadata."""

    __tablename__ = "login_attempts"
    __table_args__ = (
        Index("ix_login_attempts_username_time", "normalised_username", "attempted_at"),
        Index("ix_login_attempts_source_time", "source_ip", "attempted_at"),
    )

    normalised_username: Mapped[str] = mapped_column(String(150), nullable=False)
    source_ip: Mapped[str | None] = mapped_column(IP_ADDRESS_TYPE)
    result: Mapped[str] = mapped_column(String(30), nullable=False)
    failure_category: Mapped[str | None] = mapped_column(String(100))
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    correlation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)


class PolicyAcknowledgementORM(Base):
    """Map one user's acknowledgement of an organisational policy version."""

    __tablename__ = "policy_acknowledgements"

    policy_version: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    session_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL")
    )
    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
