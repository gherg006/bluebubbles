"""Versioned, secret-free server configuration persistence mapping."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from bluebubbles.server.database.base import JSON_VALUE_TYPE, Base, UUIDPrimaryKeyMixin


class ConfigurationVersionORM(Base, UUIDPrimaryKeyMixin):
    """Map one validated public configuration revision without secrets."""

    __tablename__ = "configuration_versions"
    __table_args__ = (Index("ix_configuration_versions_changed_at", "changed_at"),)

    version_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    configuration: Mapped[dict[str, object]] = mapped_column(
        JSON_VALUE_TYPE, nullable=False
    )
    changed_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    change_reason: Mapped[str] = mapped_column(String(1000), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    previous_version_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("configuration_versions.id", ondelete="SET NULL"),
    )
    restart_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
