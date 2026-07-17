"""Immutable cache records used by client repository protocols."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CachedUserRecord:
    """Represent one versioned server-owned user profile cache record."""

    user_id: UUID
    username: str
    display_name: str
    profile_version: int
    cached_at: datetime
    expires_at: datetime | None = None
    department: str | None = None
    job_title: str | None = None
    presence_state: str | None = None


@dataclass(frozen=True, slots=True)
class CachedConversationRecord:
    """Represent one versioned server-owned conversation summary."""

    conversation_id: UUID
    conversation_type: str
    last_activity_at: datetime
    server_version: int
    cached_at: datetime
    title: str | None = None
    latest_message_id: UUID | None = None
    unread_count: int = 0
    is_muted: bool = False
    is_pinned: bool = False
    is_archived: bool = False

