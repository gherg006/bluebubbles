"""JSON local preference repository for non-secret validated settings."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from bluebubbles.client.storage.database import LocalDatabaseManager


class SQLiteLocalSettingsRepository:
    """Persist user preferences separately from server-controlled policy."""

    def __init__(self, database: LocalDatabaseManager) -> None:
        self._database = database

    async def set(self, key: str, value: object) -> None:
        """Store one bounded JSON-compatible non-secret preference."""
        selected = self._validate_key(key)
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
        if len(encoded.encode()) > 64 * 1024:
            raise ValueError("Local setting is too large")
        await self._database.execute(
            "INSERT INTO local_settings(setting_key, value_json, updated_at) "
            "VALUES (?, ?, ?) ON CONFLICT(setting_key) DO UPDATE SET "
            "value_json=excluded.value_json, updated_at=excluded.updated_at",
            (selected, encoded, datetime.now(UTC).isoformat()),
        )

    async def get(self, key: str) -> object | None:
        """Return one decoded preference or None when absent."""
        row = await self._database.fetch_one(
            "SELECT value_json FROM local_settings WHERE setting_key = ?",
            (self._validate_key(key),),
        )
        return None if row is None else json.loads(str(row[0]))

    async def delete(self, key: str) -> None:
        """Delete one preference idempotently."""
        await self._database.execute(
            "DELETE FROM local_settings WHERE setting_key = ?",
            (self._validate_key(key),),
        )

    @staticmethod
    def _validate_key(key: str) -> str:
        selected = key.strip()
        if (
            not selected
            or len(selected) > 128
            or any(c in selected for c in "\r\n\x00")
        ):
            raise ValueError("Local setting key is invalid")
        return selected
