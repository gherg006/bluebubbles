"""Conversation identity, membership, and safe event persistence mappings."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from bluebubbles.server.database.base import (
    JSON_VALUE_TYPE,
    Base,
    CreatedAtMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VersionMixin,
)


class ConversationORM(
    Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, VersionMixin
):
    """Map a direct, group, or server-controlled system conversation."""

    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint(
            "conversation_type IN ('direct', 'group', 'system')",
            name="type_valid",
        ),
        CheckConstraint(
            "conversation_type <> 'group' OR (title IS NOT NULL AND length(title) > 0)",
            name="group_title_required",
        ),
        Index("ix_conversations_activity", "last_activity_at", "id"),
    )

    conversation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(500))
    created_by: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_archived_systemwide: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )


class DirectConversationPairORM(Base):
    """Map a canonical pair that guarantees direct-conversation uniqueness."""

    __tablename__ = "direct_conversation_pairs"
    __table_args__ = (
        UniqueConstraint("lower_user_id", "higher_user_id", name="uq_direct_user_pair"),
        CheckConstraint("lower_user_id < higher_user_id", name="canonical_user_order"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    lower_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    higher_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )


class ConversationMemberORM(Base, UUIDPrimaryKeyMixin):
    """Map one current or historical conversation-membership period."""

    __tablename__ = "conversation_members"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id", "user_id", "joined_at", name="uq_membership_period"
        ),
        CheckConstraint("membership_version >= 1", name="version_positive"),
        CheckConstraint(
            "member_role IN ('owner', 'admin', 'member')", name="role_valid"
        ),
        CheckConstraint(
            "notification_level IN ('all', 'mentions', 'none')",
            name="notification_level_valid",
        ),
        CheckConstraint(
            "removed_at IS NULL OR removed_at >= joined_at", name="period_order_valid"
        ),
        Index(
            "uq_active_conversation_member",
            "conversation_id",
            "user_id",
            unique=True,
            postgresql_where=text("removed_at IS NULL"),
        ),
        Index(
            "uq_active_group_owner",
            "conversation_id",
            unique=True,
            postgresql_where=text("member_role = 'owner' AND removed_at IS NULL"),
        ),
        Index("ix_members_user_active", "user_id", "removed_at"),
        Index("ix_members_conversation_active", "conversation_id", "removed_at"),
        Index(
            "ix_members_conversation_role",
            "conversation_id",
            "member_role",
            postgresql_where=text("removed_at IS NULL"),
        ),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    member_role: Mapped[str] = mapped_column(String(20), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_read_message_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_muted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    muted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notification_level: Mapped[str] = mapped_column(
        String(30), nullable=False, default="all", server_default="all"
    )
    membership_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )


class ConversationEventORM(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """Map safe, structured server-generated conversation activity."""

    __tablename__ = "conversation_events"
    __table_args__ = (
        Index("ix_conversation_events_order", "conversation_id", "created_at", "id"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    target_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    event_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSON_VALUE_TYPE, nullable=False, default=dict
    )
