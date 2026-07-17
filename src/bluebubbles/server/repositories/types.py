"""Infrastructure-neutral repository query and result value objects."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from bluebubbles.shared.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


@dataclass(frozen=True, slots=True)
class CursorPage[T]:
    """Return one stable bounded page and its forward continuation cursor."""

    items: tuple[T, ...]
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class UserSearchQuery:
    """Describe a bounded case-insensitive user-directory search."""

    term: str = ""
    limit: int = DEFAULT_PAGE_SIZE
    cursor: str | None = None
    department: str | None = None
    include_deleted: bool = False

    def __post_init__(self) -> None:
        _validate_limit(self.limit)


@dataclass(frozen=True, slots=True)
class ConversationListQuery:
    """Describe a stable last-activity conversation page for one user."""

    user_id: UUID
    limit: int = DEFAULT_PAGE_SIZE
    cursor: str | None = None
    include_archived: bool = False

    def __post_init__(self) -> None:
        _validate_limit(self.limit)


@dataclass(frozen=True, slots=True)
class MessagePageQuery:
    """Describe a newest-first encrypted-message page."""

    conversation_id: UUID
    user_id: UUID | None = None
    limit: int = DEFAULT_PAGE_SIZE
    cursor: str | None = None
    include_deleted: bool = False
    membership_started_at: datetime | None = None

    def __post_init__(self) -> None:
        _validate_limit(self.limit)
        if (
            self.membership_started_at is not None
            and self.membership_started_at.tzinfo is None
        ):
            raise ValueError("Membership timestamp must be timezone-aware")


@dataclass(frozen=True, slots=True)
class AuditQuery:
    """Describe a forward audit-chain query with safe metadata filters."""

    limit: int = DEFAULT_PAGE_SIZE
    cursor: str | None = None
    category: str | None = None
    actor_user_id: UUID | None = None
    minimum_sequence: int | None = None

    def __post_init__(self) -> None:
        _validate_limit(self.limit)
        if self.minimum_sequence is not None and self.minimum_sequence < 1:
            raise ValueError("Minimum audit sequence must be positive")


@dataclass(frozen=True, slots=True)
class StoredAttachmentChunk:
    """Carry complete encrypted chunk metadata to the repository boundary."""

    id: UUID
    attachment_id: UUID
    index: int
    encrypted_size: int
    encrypted_checksum: str
    nonce: bytes
    authentication_tag: bytes
    storage_reference: str
    created_at: datetime

    def __post_init__(self) -> None:
        if self.index < 0 or self.encrypted_size < 0:
            raise ValueError("Chunk index and size cannot be negative")
        if not all(
            (
                self.encrypted_checksum,
                self.nonce,
                self.authentication_tag,
                self.storage_reference,
            )
        ):
            raise ValueError("Complete encrypted chunk metadata is required")
        if self.created_at.tzinfo is None:
            raise ValueError("Chunk timestamp must be timezone-aware")


def encode_cursor(*values: object) -> str:
    """Encode scalar ordering values into an opaque URL-safe cursor."""
    serialised = [
        (
            value.isoformat()
            if isinstance(value, datetime)
            else str(value) if isinstance(value, UUID) else value
        )
        for value in values
    ]
    raw = json.dumps(serialised, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str, expected_values: int) -> tuple[object, ...]:
    """Decode and structurally validate an opaque repository cursor."""
    try:
        padded = cursor + ("=" * (-len(cursor) % 4))
        value = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("Invalid repository cursor") from error
    if not isinstance(value, list) or len(value) != expected_values:
        raise ValueError("Invalid repository cursor")
    return tuple(value)


def _validate_limit(limit: int) -> None:
    if not 1 <= limit <= MAX_PAGE_SIZE:
        raise ValueError(f"Page limit must be between 1 and {MAX_PAGE_SIZE}")
