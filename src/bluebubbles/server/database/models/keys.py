"""Versioned public cryptographic key persistence mapping."""

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
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from bluebubbles.server.database.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class UserPublicKeyORM(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """Map public-only, versioned encryption and signing key material."""

    __tablename__ = "user_public_keys"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "key_type", "key_version", name="uq_user_key_version"
        ),
        CheckConstraint("key_version >= 1", name="key_version_positive"),
        CheckConstraint("key_type IN ('encryption', 'signing')", name="key_type_valid"),
        Index(
            "uq_primary_user_key",
            "user_id",
            "key_type",
            unique=True,
            postgresql_where=text("is_primary = true AND revoked_at IS NULL"),
        ),
        Index("ix_user_public_keys_user", "user_id", "revoked_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    key_type: Mapped[str] = mapped_column(String(20), nullable=False)
    key_version: Mapped[int] = mapped_column(Integer, nullable=False)
    public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str | None] = mapped_column(String(500))
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
