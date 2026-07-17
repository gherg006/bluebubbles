"""Directional contact relationship persistence mapping."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from bluebubbles.server.database.base import Base, TimestampMixin


class ContactRelationshipORM(Base, TimestampMixin):
    """Map one user's independent relationship settings for another user."""

    __tablename__ = "contact_relationships"
    __table_args__ = (
        CheckConstraint("owner_user_id <> contact_user_id", name="users_differ"),
        CheckConstraint("weight >= 0", name="weight_non_negative"),
        Index("ix_contacts_owner", "owner_user_id"),
        Index("ix_contacts_contact", "contact_user_id"),
    )

    owner_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    contact_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_favourite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# Domain terminology uses ``Contact`` while the schema makes direction explicit.
ContactORM = ContactRelationshipORM
