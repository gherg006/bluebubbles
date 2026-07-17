"""Administrative announcement and acknowledgement persistence mappings."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from bluebubbles.server.database.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VersionMixin,
)


class AnnouncementORM(Base, UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin):
    """Map deliberate organisational plaintext, separate from user messages."""

    __tablename__ = "announcements"
    __table_args__ = (
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint("length(title) > 0", name="title_non_empty"),
        CheckConstraint("length(body) > 0", name="body_non_empty"),
        CheckConstraint(
            "priority IN ('normal', 'important', 'urgent')", name="priority_valid"
        ),
        CheckConstraint(
            "target_type IN ('all_users', 'department', 'group')",
            name="target_type_valid",
        ),
        Index("ix_announcements_publication", "published_at", "expires_at"),
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(String(10000), nullable=False)
    author_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    target_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_reference: Mapped[str | None] = mapped_column(String(500))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    requires_acknowledgement: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )


class AnnouncementAcknowledgementORM(Base):
    """Map one user-level acknowledgement of an announcement."""

    __tablename__ = "announcement_acknowledgements"

    announcement_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("announcements.id", ondelete="CASCADE"),
        primary_key=True,
    )
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
