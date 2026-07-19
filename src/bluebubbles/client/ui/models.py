"""Presentation-only immutable records for the PySide6 desktop interface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from uuid import UUID


class NavigationSection(StrEnum):
    """Define every Version 1 navigation destination."""

    CHATS = "chats"
    CONTACTS = "contacts"
    GROUPS = "groups"
    TRANSFERS = "transfers"
    SEARCH = "search"
    ANNOUNCEMENTS = "announcements"
    SETTINGS = "settings"
    SESSIONS = "sessions"
    DIAGNOSTICS = "diagnostics"
    ADMINISTRATION = "administration"
    ADMIN_USERS = "users"
    ADMIN_CONNECTIONS = "connections"
    ADMIN_AUDIT = "audit"
    ADMIN_ALERTS = "alerts"
    ADMIN_WORKERS = "workers"
    ADMIN_CONFIGURATION = "configuration"
    ADMIN_EXPORTS = "exports"


class ThemeName(StrEnum):
    """Define supported, contrast-reviewed application themes."""

    LIGHT = "light"
    DARK = "dark"
    HIGH_CONTRAST = "high_contrast"


class ConversationSort(StrEnum):
    """Define every user-list ordering exposed by the desktop shell."""

    MOST_RECENT = "most_recent"
    FORENAME = "forename"
    SURNAME = "surname"
    FREQUENCY = "frequency"
    DATE_ADDED = "date_added"
    NEW_MESSAGES = "new_messages"


class UiMessageState(StrEnum):
    """Define colour-independent message delivery labels."""

    PENDING = "pending"
    STORED = "stored"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True)
class ConversationListItem:
    """Represent one bounded conversation-list projection."""

    conversation_id: UUID
    title: str
    preview: str
    last_activity_at: datetime
    unread_count: int = 0
    is_group: bool = False
    is_muted: bool = False
    is_pinned: bool = False
    composer_enabled: bool = True
    message_frequency: int = 0
    date_added_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class MessageListItem:
    """Represent authorised display content and safe delivery metadata."""

    message_id: UUID
    conversation_id: UUID
    sender_name: str
    text: str
    sent_at: datetime
    state: UiMessageState
    is_own: bool = False
    edited: bool = False
    reply_preview: str | None = None
    attachment_name: str | None = None
    verification_warning: str | None = None


@dataclass(frozen=True, slots=True)
class TransferListItem:
    """Represent transfer progress without exposing local filesystem paths."""

    transfer_id: UUID
    file_name: str
    direction: str
    transferred_bytes: int
    total_bytes: int
    state: str

    @property
    def percentage(self) -> int:
        """Return bounded whole-number progress for an accessible progress bar."""
        if self.total_bytes <= 0:
            return 0
        return min(100, int(self.transferred_bytes * 100 / self.total_bytes))


@dataclass(frozen=True, slots=True)
class SearchListItem:
    """Represent one local authorised search result."""

    message_id: UUID
    conversation_id: UUID
    conversation_title: str
    sender_name: str
    excerpt: str
    sent_at: datetime


@dataclass(frozen=True, slots=True)
class SessionListItem:
    """Represent one server session safe for display and revocation."""

    session_id: UUID
    device_name: str
    created_at: datetime
    last_seen_at: datetime
    current: bool = False


@dataclass(frozen=True, slots=True)
class AttachmentSelection:
    """Represent validated composer attachment selection without auto-sending."""

    path: Path
    size_bytes: int
