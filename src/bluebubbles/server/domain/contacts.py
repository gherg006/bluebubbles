"""Server-owned contact relationship domain rules."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from bluebubbles.server.domain.common import BaseEntity


@dataclass(kw_only=True)
class Contact(BaseEntity):
    """Represent one directional relationship between two distinct users."""

    owner_id: UUID
    contact_id: UUID
    nickname: str | None = None
    is_favourite: bool = False
    is_blocked: bool = False
    last_contacted: datetime | None = None
    weight_score: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.owner_id == self.contact_id or self.weight_score < 0:
            raise ValueError("Contact users must differ and weight cannot be negative")

    def set_favourite(self, favourite: bool, at: datetime) -> None:
        """Update favourite state."""
        if self.is_favourite != favourite:
            self.is_favourite = favourite
            self.touch(at)

    def set_blocked(self, blocked: bool, at: datetime) -> None:
        """Update block state; blocking also removes favourite status."""
        if self.is_blocked != blocked:
            self.is_blocked = blocked
            if blocked:
                self.is_favourite = False
            self.touch(at)

    def increase_weight(self, amount: int, at: datetime) -> None:
        """Increase interaction weight by a positive amount."""
        if amount <= 0:
            raise ValueError("Contact weight increase must be positive")
        self.weight_score += amount
        self.last_contacted = at
        self.touch(at)

    def reset_weight(self, at: datetime) -> None:
        """Reset interaction weight without deleting contact history."""
        self.weight_score = 0
        self.touch(at)
