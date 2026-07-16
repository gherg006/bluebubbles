"""Common, infrastructure-free building blocks for server domain entities."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from typing import Any, Self
from uuid import UUID, uuid4


def utc_now() -> datetime:
    """Return an aware UTC timestamp for domain state transitions."""
    return datetime.now(UTC)


@dataclass(kw_only=True)
class BaseEntity:
    """Provide identity, timestamps, soft deletion, and optimistic versioning."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    version: int = 1

    @classmethod
    def create(cls, **values: Any) -> Self:
        """Create an entity with a generated identity and consistent timestamps."""
        now = utc_now()
        return cls(id=uuid4(), created_at=now, updated_at=now, **values)

    def __post_init__(self) -> None:
        """Reject invalid persisted entity state."""
        if self.version < 1:
            raise ValueError("Entity version must be at least one")
        for value in (self.created_at, self.updated_at, self.deleted_at):
            if value is not None and value.tzinfo is None:
                raise ValueError("Entity timestamps must be timezone-aware")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at")

    @property
    def is_deleted(self) -> bool:
        """Return whether this entity has been soft deleted."""
        return self.deleted_at is not None

    def touch(self, at: datetime | None = None) -> None:
        """Advance the update timestamp and optimistic-lock version."""
        timestamp = at or utc_now()
        if timestamp.tzinfo is None or timestamp < self.updated_at:
            raise ValueError("Touch timestamp must be aware and monotonic")
        self.updated_at = timestamp
        self.version += 1

    def mark_deleted(self, at: datetime | None = None) -> None:
        """Soft delete this entity without destroying its persisted history."""
        if self.deleted_at is not None:
            return
        self.deleted_at = at or utc_now()
        self.touch(self.deleted_at)

    def restore(self, at: datetime | None = None) -> None:
        """Restore a soft-deleted entity and advance its version."""
        if self.deleted_at is None:
            return
        self.deleted_at = None
        self.touch(at)

    def to_dict(self) -> dict[str, Any]:
        """Return a repository-friendly copy of the entity fields."""
        return asdict(self)

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> Self:
        """Construct an entity from fields previously returned by ``to_dict``."""
        allowed = {field.name for field in fields(cls)}
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"Unknown {cls.__name__} fields: {sorted(unknown)}")
        return cls(**values)


@dataclass(kw_only=True)
class DomainEvent:
    """Represent immutable facts raised by domain behaviour."""

    event_id: UUID
    event_type: str
    occurred_at: datetime
    aggregate_id: UUID
    payload: dict[str, object]

    def __post_init__(self) -> None:
        """Require safe event identity and time metadata."""
        if not self.event_type.strip():
            raise ValueError("Domain event type is required")
        if self.occurred_at.tzinfo is None:
            raise ValueError("Domain event timestamp must be timezone-aware")
