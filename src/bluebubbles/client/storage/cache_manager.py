"""Bounded LRU maintenance for database and managed filesystem cache entries."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from bluebubbles.client.storage.database import LocalDatabaseManager
from bluebubbles.client.storage.models import (
    CacheCleanupResult,
    CacheEntry,
    CacheEntryType,
    LocalStorageUsage,
)
from bluebubbles.client.storage.paths import ProfilePaths

_EVICTION_PRIORITY = {
    CacheEntryType.TEMPORARY: 0,
    CacheEntryType.THUMBNAIL: 1,
    CacheEntryType.TRANSFER: 2,
    CacheEntryType.ATTACHMENT: 3,
    CacheEntryType.MESSAGE_DISPLAY: 4,
    CacheEntryType.MESSAGE_ENCRYPTED: 5,
    CacheEntryType.PROFILE: 6,
}


class CacheManager:
    """Account for local cache use and evict unpinned least-recent entries."""

    def __init__(
        self,
        database: LocalDatabaseManager,
        paths: ProfilePaths,
        maximum_bytes: int,
        cleanup_target_ratio: float = 0.9,
    ) -> None:
        if maximum_bytes <= 0 or not 0.5 <= cleanup_target_ratio < 1:
            raise ValueError("Cache limit or cleanup target is invalid")
        self._database = database
        self._paths = paths
        self._maximum_bytes = maximum_bytes
        self._cleanup_target_ratio = cleanup_target_ratio

    async def register(self, entry: CacheEntry) -> None:
        """Upsert accounting metadata for one managed cache object."""
        await self._database.execute(
            "INSERT INTO cache_entries(cache_key, cache_type, storage_reference, "
            "size_bytes, created_at, last_accessed_at, expires_at, is_pinned) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(cache_key) DO UPDATE SET "
            "cache_type=excluded.cache_type, "
            "storage_reference=excluded.storage_reference, "
            "size_bytes=excluded.size_bytes, "
            "last_accessed_at=excluded.last_accessed_at, "
            "expires_at=excluded.expires_at, is_pinned=excluded.is_pinned",
            (
                entry.cache_key,
                entry.cache_type.value,
                entry.storage_reference,
                entry.size_bytes,
                entry.created_at.isoformat(),
                entry.last_accessed_at.isoformat(),
                entry.expires_at.isoformat() if entry.expires_at else None,
                int(entry.is_pinned),
            ),
        )

    async def mark_accessed(self, cache_key: str) -> None:
        """Refresh LRU state without changing the cached object."""
        await self._database.execute(
            "UPDATE cache_entries SET last_accessed_at = ? WHERE cache_key = ?",
            (datetime.now(UTC).isoformat(), cache_key),
        )

    async def calculate_usage(self) -> LocalStorageUsage:
        """Calculate actual database bytes and accounted external bytes."""
        page_count = await self._database.fetch_one("PRAGMA page_count")
        page_size = await self._database.fetch_one("PRAGMA page_size")
        row = await self._database.fetch_one(
            "SELECT COALESCE(SUM(size_bytes), 0), COUNT(*) FROM cache_entries "
            "WHERE storage_reference IS NOT NULL"
        )
        database_bytes = (
            int(page_count[0]) * int(page_size[0]) if page_count and page_size else 0
        )
        return LocalStorageUsage(
            database_bytes,
            int(row[0]) if row else 0,
            int(row[1]) if row else 0,
        )

    async def remove_expired_entries(self) -> CacheCleanupResult:
        """Remove every expired unpinned record and its managed file."""
        now = datetime.now(UTC).isoformat()
        rows = await self._database.fetch_all(
            "SELECT cache_key, storage_reference, size_bytes FROM cache_entries "
            "WHERE is_pinned = 0 AND expires_at IS NOT NULL AND expires_at <= ?",
            (now,),
        )
        removed = await self._remove_rows(rows)
        usage = await self.calculate_usage()
        return CacheCleanupResult(len(rows), removed, usage.total_bytes)

    async def enforce_limits(self) -> CacheCleanupResult:
        """Evict by type priority and LRU until usage reaches the 90% target."""
        await self.remove_expired_entries()
        usage = await self.calculate_usage()
        if usage.total_bytes <= self._maximum_bytes:
            return CacheCleanupResult(0, 0, usage.total_bytes)
        rows = await self._database.fetch_all(
            "SELECT cache_key, storage_reference, size_bytes, cache_type, "
            "last_accessed_at FROM cache_entries WHERE is_pinned = 0"
        )
        ordered = sorted(
            rows,
            key=lambda row: (
                _EVICTION_PRIORITY[CacheEntryType(str(row[3]))],
                str(row[4]),
            ),
        )
        target = int(self._maximum_bytes * self._cleanup_target_ratio)
        selected = []
        projected = usage.total_bytes
        for row in ordered:
            if projected <= target:
                break
            selected.append(row)
            projected -= int(row[2])
        removed = await self._remove_rows(selected)
        remaining = (await self.calculate_usage()).total_bytes
        return CacheCleanupResult(len(selected), removed, remaining)

    async def _remove_rows(self, rows: list[sqlite3.Row]) -> int:
        removed = 0
        for row in rows:
            reference = row[1]
            if reference:
                path = self._paths.managed_path(str(reference))
                if path.is_file():
                    path.unlink()
            removed += int(row[2])
            await self._database.execute(
                "DELETE FROM cache_entries WHERE cache_key = ?",
                (str(row[0]),),
            )
        return removed
