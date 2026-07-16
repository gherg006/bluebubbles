"""Client-only conversation snapshots for presentation and local caching."""

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from bluebubbles.shared.models.conversations import ConversationType


@dataclass(frozen=True, slots=True)
class ClientConversation:
    """Represent client-visible conversation metadata."""

    id: UUID
    conversation_type: ConversationType
    participant_ids: tuple[UUID, ...]
    last_activity: datetime
    title: str | None = None
    unread_count: int = 0
    archived: bool = False

    def __post_init__(self) -> None:
        if not self.participant_ids or len(self.participant_ids) != len(
            set(self.participant_ids)
        ):
            raise ValueError("Conversation participants must be non-empty and unique")
        if self.unread_count < 0:
            raise ValueError("Unread count cannot be negative")

    def mark_read(self) -> "ClientConversation":
        """Return a read conversation snapshot."""
        return replace(self, unread_count=0)
