"""Immutable values shared by the local client storage subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from uuid import UUID


class CacheEntryType(StrEnum):
    """Classify managed cache objects for bounded eviction."""

    TEMPORARY = "temporary"
    THUMBNAIL = "thumbnail"
    TRANSFER = "transfer"
    ATTACHMENT = "attachment"
    MESSAGE_DISPLAY = "message_display"
    MESSAGE_ENCRYPTED = "message_encrypted"
    PROFILE = "profile"


@dataclass(frozen=True, slots=True)
class CacheEntry:
    """Describe one database or filesystem cache object."""

    cache_key: str
    cache_type: CacheEntryType
    size_bytes: int
    created_at: datetime
    last_accessed_at: datetime
    storage_reference: str | None = None
    expires_at: datetime | None = None
    is_pinned: bool = False

    def __post_init__(self) -> None:
        if not self.cache_key or self.size_bytes < 0:
            raise ValueError("Cache entry metadata is invalid")


@dataclass(frozen=True, slots=True)
class LocalStorageUsage:
    """Report managed local storage consumption."""

    database_bytes: int
    filesystem_bytes: int
    entries: int

    @property
    def total_bytes(self) -> int:
        """Return combined database and managed filesystem bytes."""
        return self.database_bytes + self.filesystem_bytes


@dataclass(frozen=True, slots=True)
class CacheCleanupResult:
    """Report one cache maintenance operation."""

    removed_entries: int
    removed_bytes: int
    remaining_bytes: int


@dataclass(frozen=True, slots=True)
class LocalDatabaseIntegrityResult:
    """Report SQLite's integrity result without exposing record data."""

    healthy: bool
    detail: str


@dataclass(frozen=True, slots=True)
class MigrationResult:
    """Report an applied client schema migration range."""

    previous_version: int
    current_version: int
    applied_versions: tuple[int, ...]
    backup_path: Path | None = None


@dataclass(frozen=True, slots=True)
class CachedPublicKey:
    """Store one versioned public key safe for recipient selection."""

    user_id: UUID
    key_type: str
    key_version: int
    public_key: bytes = field(repr=False)
    fingerprint: str
    retrieved_at: datetime
    expires_at: datetime
    is_revoked: bool = False


@dataclass(frozen=True, slots=True)
class SynchronisationState:
    """Store an opaque server cursor or version for one cache scope."""

    scope: str
    scope_identifier: str | None
    cursor: str | None
    version: int | None
    synchronised_at: datetime
