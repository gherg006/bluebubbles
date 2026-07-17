"""Opaque synchronisation cursor persistence for later reconnect orchestration."""

from __future__ import annotations

from datetime import datetime

from bluebubbles.client.storage.database import LocalDatabaseManager
from bluebubbles.client.storage.models import SynchronisationState


class SQLiteSynchronisationStateRepository:
    """Store one newest known cursor/version per server-owned scope."""

    def __init__(self, database: LocalDatabaseManager) -> None:
        self._database = database

    async def save(self, state: SynchronisationState) -> bool:
        """Store state unless an existing numeric version is newer."""
        identifier = state.scope_identifier or ""
        existing = await self.get(state.scope, state.scope_identifier)
        if (
            existing is not None
            and existing.version is not None
            and state.version is not None
            and existing.version > state.version
        ):
            return False
        await self._database.execute(
            "INSERT INTO synchronisation_state(scope, scope_identifier, cursor, "
            "version, synchronised_at) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(scope, scope_identifier) DO UPDATE SET "
            "cursor=excluded.cursor, "
            "version=excluded.version, synchronised_at=excluded.synchronised_at",
            (
                state.scope,
                identifier,
                state.cursor,
                state.version,
                state.synchronised_at.isoformat(),
            ),
        )
        return True

    async def get(
        self, scope: str, scope_identifier: str | None = None
    ) -> SynchronisationState | None:
        """Return one opaque synchronization position."""
        row = await self._database.fetch_one(
            "SELECT cursor, version, synchronised_at FROM synchronisation_state "
            "WHERE scope = ? AND scope_identifier = ?",
            (scope, scope_identifier or ""),
        )
        if row is None:
            return None
        return SynchronisationState(
            scope,
            scope_identifier,
            str(row[0]) if row[0] is not None else None,
            int(row[1]) if row[1] is not None else None,
            datetime.fromisoformat(str(row[2])),
        )
