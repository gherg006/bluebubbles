"""Declarative database metadata and shared persistence column helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, MetaData, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

JSON_VALUE_TYPE = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    """Provide one deterministic metadata registry for all server ORM models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {dict[str, Any]: JSON_VALUE_TYPE}


class UUIDPrimaryKeyMixin:
    """Provide a UUID application-entity primary key."""

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)


class CreatedAtMixin:
    """Provide an explicit UTC-aware creation timestamp."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class TimestampMixin(CreatedAtMixin):
    """Provide explicit UTC-aware creation and update timestamps."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class SoftDeleteMixin:
    """Provide the shared retained-record deletion marker."""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VersionMixin:
    """Provide optimistic concurrency state for mutable entities."""

    version: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
