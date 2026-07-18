"""SQLite persistence for safe synchronisation conflicts and tombstones."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from bluebubbles.client.domain.synchronisation import (
    ConflictCategory,
    LocalTombstone,
    SynchronisationConflict,
    SynchronisationScope,
)
from bluebubbles.client.storage.database import LocalDatabaseManager


class SQLiteConflictRepository:
    """Persist non-content conflict metadata for recovery and presentation."""

    def __init__(self, database: LocalDatabaseManager) -> None:
        self._database = database

    async def save(self, conflict: SynchronisationConflict) -> None:
        """Upsert one conflict without recording message or draft text."""
        await self._database.execute(
            "INSERT INTO synchronisation_conflicts(conflict_id, category, scope, "
            "scope_id, action_id, detected_at, failure_code, "
            "attempted_content_preserved, "
            "resolved_at, resolution) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(conflict_id) DO UPDATE SET resolved_at=excluded.resolved_at, "
            "resolution=excluded.resolution",
            (
                str(conflict.conflict_id),
                conflict.category.value,
                conflict.scope.value,
                str(conflict.scope_id) if conflict.scope_id else None,
                str(conflict.action_id) if conflict.action_id else None,
                conflict.detected_at.isoformat(),
                conflict.failure_code,
                int(conflict.attempted_content_preserved),
                conflict.resolved_at.isoformat() if conflict.resolved_at else None,
                conflict.resolution.value if conflict.resolution else None,
            ),
        )

    async def list_unresolved(self) -> list[SynchronisationConflict]:
        """Return unresolved conflicts oldest first."""
        rows = await self._database.fetch_all(
            "SELECT conflict_id, category, scope, scope_id, action_id, detected_at, "
            "failure_code, attempted_content_preserved FROM synchronisation_conflicts "
            "WHERE resolved_at IS NULL ORDER BY detected_at, conflict_id"
        )
        return [
            SynchronisationConflict(
                UUID(str(row[0])),
                ConflictCategory(str(row[1])),
                SynchronisationScope(str(row[2])),
                UUID(str(row[3])) if row[3] else None,
                UUID(str(row[4])) if row[4] else None,
                datetime.fromisoformat(str(row[5])),
                str(row[6]),
                bool(row[7]),
            )
            for row in rows
        ]


class SQLiteTombstoneRepository:
    """Persist authoritative unavailability markers by resource and version."""

    def __init__(self, database: LocalDatabaseManager) -> None:
        self._database = database

    async def save(self, tombstone: LocalTombstone) -> None:
        """Upsert a tombstone without allowing an older version to replace it."""
        await self._database.execute(
            "INSERT INTO local_tombstones(scope, resource_id, server_version, "
            "created_at, reason_code) VALUES (?, ?, ?, ?, ?) ON CONFLICT(scope, "
            "resource_id) DO UPDATE SET server_version=excluded.server_version, "
            "created_at=excluded.created_at, reason_code=excluded.reason_code WHERE "
            "excluded.server_version IS NULL OR "
            "local_tombstones.server_version IS NULL "
            "OR excluded.server_version >= local_tombstones.server_version",
            (
                tombstone.scope.value,
                str(tombstone.resource_id),
                tombstone.server_version,
                tombstone.created_at.isoformat(),
                tombstone.reason_code,
            ),
        )

    async def get(
        self, scope: SynchronisationScope, resource_id: UUID
    ) -> LocalTombstone | None:
        """Return one tombstone for stale-event suppression."""
        row = await self._database.fetch_one(
            "SELECT server_version, created_at, reason_code FROM local_tombstones "
            "WHERE scope = ? AND resource_id = ?",
            (scope.value, str(resource_id)),
        )
        if row is None:
            return None
        return LocalTombstone(
            scope,
            resource_id,
            int(row[0]) if row[0] is not None else None,
            datetime.fromisoformat(str(row[1])),
            str(row[2]),
        )
