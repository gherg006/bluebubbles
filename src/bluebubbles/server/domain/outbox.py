"""Durable, plaintext-free application event model for later publication."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from uuid import UUID

from bluebubbles.server.domain.common import BaseEntity


@dataclass(kw_only=True)
class OutboxEvent(BaseEntity):
    """Represent a durable event written in the business transaction."""

    event_type: str
    aggregate_id: UUID
    protocol_version: int
    payload: Mapping[str, object]
    available_at: datetime
    aggregate_type: str = "domain"
    published_at: datetime | None = None
    attempts: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        if (
            not self.event_type
            or not self.aggregate_type
            or self.protocol_version < 1
            or self.attempts < 0
        ):
            raise ValueError("Outbox event metadata is invalid")
        if _contains_forbidden_field(self.payload):
            raise ValueError("Outbox payload contains forbidden sensitive fields")
        self.payload = MappingProxyType(dict(self.payload))

    def record_attempt(self, at: datetime) -> None:
        """Record an unsuccessful publication attempt."""
        if self.published_at is not None:
            raise ValueError("Published events cannot be retried")
        self.attempts += 1
        self.touch(at)

    def mark_published(self, at: datetime) -> None:
        """Mark successful durable publication idempotently."""
        if self.published_at is None:
            self.published_at = at
            self.touch(at)


def _contains_forbidden_field(value: object) -> bool:
    """Recursively reject sensitive field names in nested durable payloads."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            name = str(key).casefold()
            if any(
                marker in name for marker in ("plaintext", "password", "private_key")
            ):
                return True
            if _contains_forbidden_field(item):
                return True
    elif isinstance(value, list | tuple):
        return any(_contains_forbidden_field(item) for item in value)
    return False
