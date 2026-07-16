"""Client-local authorised search query and result models."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SearchQuery:
    """Represent a bounded local-cache search."""

    text: str
    conversation_id: UUID | None = None
    limit: int = 50

    def __post_init__(self) -> None:
        if not self.text.strip() or not 1 <= self.limit <= 250:
            raise ValueError("Search text and limit are invalid")


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Return an authorised local plaintext excerpt for display only."""

    message_id: UUID
    conversation_id: UUID
    sent_at: datetime
    excerpt: str

    def __post_init__(self) -> None:
        if not self.excerpt:
            raise ValueError("Search result excerpt is required")
