"""Server announcement publication domain model."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from bluebubbles.server.domain.common import BaseEntity
from bluebubbles.shared.models.announcements import (
    AnnouncementPriority,
    AnnouncementTargetType,
)


@dataclass(kw_only=True)
class Announcement(BaseEntity):
    """Represent administrator-authored plaintext intended for recipients."""

    author_id: UUID
    title: str
    body: str
    priority: AnnouncementPriority
    target_type: AnnouncementTargetType
    target_ids: tuple[UUID, ...] = ()
    published_at: datetime | None = None
    expires_at: datetime | None = None
    withdrawn_at: datetime | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.title.strip() or not self.body.strip():
            raise ValueError("Announcement title and body are required")
        if self.expires_at is not None and self.expires_at.tzinfo is None:
            raise ValueError("Announcement expiry must be timezone-aware")

    def publish(self, at: datetime) -> None:
        """Publish a draft announcement exactly once."""
        if self.published_at is not None or self.withdrawn_at is not None:
            raise ValueError("Announcement cannot be published in its current state")
        self.published_at = at
        self.touch(at)

    def withdraw(self, at: datetime) -> None:
        """Withdraw a published announcement."""
        if self.published_at is None or self.withdrawn_at is not None:
            raise ValueError("Only a current published announcement can be withdrawn")
        self.withdrawn_at = at
        self.touch(at)
