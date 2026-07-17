"""Version-safe SQLite cache for visible user profiles."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from bluebubbles.client.repositories.models import CachedUserRecord
from bluebubbles.client.storage.database import LocalDatabaseManager


class SQLiteCachedUserRepository:
    """Reject delayed profile versions while caching display-only fields."""

    def __init__(self, database: LocalDatabaseManager) -> None:
        self._database = database

    async def save(self, user: CachedUserRecord) -> bool:
        """Upsert a user only when its server version is not older."""
        if user.profile_version < 1:
            raise ValueError("Profile version must be positive")
        changed = await self._database.execute(
            "INSERT INTO local_users(user_id, username, display_name, department, "
            "job_title, presence_state, profile_version, cached_at, expires_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET "
            "username=excluded.username, display_name=excluded.display_name, "
            "department=excluded.department, job_title=excluded.job_title, "
            "presence_state=excluded.presence_state, "
            "profile_version=excluded.profile_version, cached_at=excluded.cached_at, "
            "expires_at=excluded.expires_at "
            "WHERE excluded.profile_version >= local_users.profile_version",
            (
                str(user.user_id),
                user.username,
                user.display_name,
                user.department,
                user.job_title,
                user.presence_state,
                user.profile_version,
                user.cached_at.isoformat(),
                user.expires_at.isoformat() if user.expires_at else None,
            ),
        )
        return changed > 0

    async def get(self, user_id: UUID) -> CachedUserRecord | None:
        """Return one cached profile without treating it as server authority."""
        row = await self._database.fetch_one(
            "SELECT username, display_name, department, job_title, presence_state, "
            "profile_version, cached_at, expires_at FROM local_users WHERE user_id = ?",
            (str(user_id),),
        )
        if row is None:
            return None
        return CachedUserRecord(
            user_id,
            str(row[0]),
            str(row[1]),
            int(row[5]),
            datetime.fromisoformat(str(row[6])),
            datetime.fromisoformat(str(row[7])) if row[7] else None,
            str(row[2]) if row[2] else None,
            str(row[3]) if row[3] else None,
            str(row[4]) if row[4] else None,
        )

    async def delete(self, user_id: UUID) -> None:
        """Invalidate one disabled or inaccessible user profile."""
        await self._database.execute(
            "DELETE FROM local_users WHERE user_id = ?", (str(user_id),)
        )

