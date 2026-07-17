"""Serialized asynchronous ownership of one keyed client SQLite database."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import secrets
import sqlite3
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import TypeVar

from bluebubbles.client.storage.migrations import ClientMigrationManager
from bluebubbles.client.storage.models import LocalDatabaseIntegrityResult
from bluebubbles.shared.errors.exceptions import LocalStorageError

ResultType = TypeVar("ResultType")


class LocalDatabaseManager:
    """Own one SQLite connection and serialize every database operation."""

    def __init__(
        self,
        database_path: Path,
        migration_manager: ClientMigrationManager,
    ) -> None:
        self._database_path = database_path
        self._migration_manager = migration_manager
        self._connection: sqlite3.Connection | None = None
        self._operation_lock = asyncio.Lock()
        self._key_buffer: bytearray | None = None

    @property
    def is_open(self) -> bool:
        """Report whether a verified SQLite connection is available."""
        return self._connection is not None

    async def open(self, key: bytes) -> None:
        """Open, key-verify and migrate the database exactly once."""
        if len(key) != 32:
            raise LocalStorageError(user_message="The local cache key is invalid.")
        async with self._operation_lock:
            if self._connection is not None:
                return
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                connection = await asyncio.to_thread(self._open_sync, bytes(key))
            except (sqlite3.Error, OSError) as error:
                raise LocalStorageError(
                    user_message="The local cache could not be opened."
                ) from error
            self._connection = connection
            self._key_buffer = bytearray(key)

    async def close(self) -> None:
        """Close the connection and overwrite the mutable key copy where possible."""
        async with self._operation_lock:
            connection = self._connection
            self._connection = None
            if connection is not None:
                await asyncio.to_thread(connection.close)
            if self._key_buffer is not None:
                self._key_buffer[:] = b"\x00" * len(self._key_buffer)
                self._key_buffer = None

    async def execute(self, statement: str, parameters: Sequence[object] = ()) -> int:
        """Execute one parameterized write and return its affected-row count."""

        def operation(connection: sqlite3.Connection) -> int:
            cursor = connection.execute(statement, tuple(parameters))
            connection.commit()
            return cursor.rowcount

        return await self.run_transaction(operation)

    async def executemany(
        self, statement: str, parameter_rows: Iterable[Sequence[object]]
    ) -> int:
        """Execute one parameterized statement for a bounded group of rows."""
        rows = [tuple(row) for row in parameter_rows]

        def operation(connection: sqlite3.Connection) -> int:
            cursor = connection.executemany(statement, rows)
            connection.commit()
            return cursor.rowcount

        return await self.run_transaction(operation)

    async def fetch_one(
        self, statement: str, parameters: Sequence[object] = ()
    ) -> sqlite3.Row | None:
        """Return one row from a parameterized read."""
        return await self.run_transaction(
            lambda connection: connection.execute(
                statement, tuple(parameters)
            ).fetchone()
        )

    async def fetch_all(
        self, statement: str, parameters: Sequence[object] = ()
    ) -> list[sqlite3.Row]:
        """Return all rows from a parameterized bounded read."""
        return await self.run_transaction(
            lambda connection: list(
                connection.execute(statement, tuple(parameters)).fetchall()
            )
        )

    async def run_transaction(
        self, operation: Callable[[sqlite3.Connection], ResultType]
    ) -> ResultType:
        """Run caller logic under the single write/read ownership lock."""
        async with self._operation_lock:
            connection = self._require_connection()
            try:
                return await asyncio.to_thread(operation, connection)
            except sqlite3.Error as error:
                connection.rollback()
                raise LocalStorageError(
                    user_message="The local cache operation failed."
                ) from error

    async def verify_integrity(self) -> LocalDatabaseIntegrityResult:
        """Run SQLite's full integrity check on the owned connection."""
        row = await self.fetch_one("PRAGMA integrity_check")
        detail = "unavailable" if row is None else str(row[0])
        return LocalDatabaseIntegrityResult(detail == "ok", detail)

    async def vacuum(self) -> None:
        """Compact the database outside an active transaction."""
        await self.run_transaction(lambda connection: connection.execute("VACUUM"))

    def _require_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            raise LocalStorageError(user_message="The local cache is not open.")
        return self._connection

    def _open_sync(self, key: bytes) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        connection.execute("PRAGMA secure_delete = ON")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS local_key_verifier "
            "(singleton INTEGER PRIMARY KEY CHECK(singleton = 1), "
            "salt BLOB NOT NULL, verifier BLOB NOT NULL)"
        )
        row = connection.execute(
            "SELECT salt, verifier FROM local_key_verifier WHERE singleton = 1"
        ).fetchone()
        if row is None:
            salt = secrets.token_bytes(32)
            verifier = hmac.digest(key, b"bluebubbles-local-db-v1\x00" + salt, "sha256")
            connection.execute(
                "INSERT INTO local_key_verifier(singleton, salt, verifier) "
                "VALUES (1, ?, ?)",
                (salt, verifier),
            )
            connection.commit()
        else:
            expected = hmac.digest(
                key, b"bluebubbles-local-db-v1\x00" + bytes(row[0]), hashlib.sha256
            )
            if not hmac.compare_digest(expected, bytes(row[1])):
                connection.close()
                raise LocalStorageError(user_message="The local cache key is invalid.")
        self._migration_manager.migrate_connection(connection)
        return connection
