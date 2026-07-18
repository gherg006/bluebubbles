"""Versioned, backup-aware migrations for the client SQLite cache."""

from __future__ import annotations

import asyncio
import shutil
import sqlite3
from collections.abc import Callable
from pathlib import Path

from bluebubbles.client.storage.models import MigrationResult
from bluebubbles.shared.errors.exceptions import LocalStorageError

Migration = Callable[[sqlite3.Connection], None]


def _migration_001(connection: sqlite3.Connection) -> None:
    """Create the complete first local-cache schema."""
    connection.executescript(
        """
        BEGIN IMMEDIATE;
        CREATE TABLE local_schema_version (
            singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
            version INTEGER NOT NULL CHECK (version >= 0)
        );
        INSERT INTO local_schema_version(singleton, version) VALUES (1, 1);

        CREATE TABLE local_users (
            user_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            display_name TEXT NOT NULL,
            department TEXT,
            job_title TEXT,
            presence_state TEXT,
            profile_version INTEGER NOT NULL,
            cached_at TEXT NOT NULL,
            expires_at TEXT
        );
        CREATE TABLE cached_conversations (
            conversation_id TEXT PRIMARY KEY,
            conversation_type TEXT NOT NULL,
            title TEXT,
            last_activity_at TEXT NOT NULL,
            latest_message_id TEXT,
            unread_count INTEGER NOT NULL CHECK (unread_count >= 0),
            is_muted INTEGER NOT NULL DEFAULT 0,
            is_pinned INTEGER NOT NULL DEFAULT 0,
            is_archived INTEGER NOT NULL DEFAULT 0,
            server_version INTEGER NOT NULL,
            cached_at TEXT NOT NULL
        );
        CREATE TABLE cached_conversation_members (
            conversation_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            group_role TEXT,
            joined_at TEXT NOT NULL,
            removed_at TEXT,
            membership_version INTEGER NOT NULL,
            cached_at TEXT NOT NULL,
            PRIMARY KEY (conversation_id, user_id)
        );
        CREATE TABLE cached_messages (
            message_id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            sender_id TEXT NOT NULL,
            message_type TEXT NOT NULL,
            transport_payload BLOB NOT NULL,
            server_created_at TEXT NOT NULL,
            client_created_at TEXT NOT NULL,
            message_version INTEGER NOT NULL,
            delivery_state TEXT NOT NULL,
            display_ciphertext BLOB,
            display_nonce BLOB,
            display_format_version INTEGER,
            cached_at TEXT NOT NULL
        );
        CREATE INDEX ix_cached_messages_conversation
            ON cached_messages(conversation_id, server_created_at, message_id);

        CREATE TABLE drafts (
            conversation_id TEXT PRIMARY KEY,
            ciphertext BLOB NOT NULL,
            nonce BLOB NOT NULL,
            format_version INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE offline_actions (
            action_id TEXT PRIMARY KEY,
            action_type TEXT NOT NULL,
            conversation_id TEXT,
            ciphertext BLOB NOT NULL,
            nonce BLOB NOT NULL,
            format_version INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            next_attempt_at TEXT,
            last_attempt_at TEXT,
            last_error_code TEXT,
            status TEXT NOT NULL,
            idempotency_key TEXT NOT NULL UNIQUE
        );
        CREATE INDEX ix_offline_actions_due
            ON offline_actions(status, next_attempt_at, created_at);

        CREATE TABLE transfer_states (
            transfer_id TEXT PRIMARY KEY,
            attachment_id TEXT NOT NULL,
            direction TEXT NOT NULL,
            ciphertext BLOB NOT NULL,
            nonce BLOB NOT NULL,
            format_version INTEGER NOT NULL,
            status TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE cached_public_keys (
            user_id TEXT NOT NULL,
            key_type TEXT NOT NULL,
            key_version INTEGER NOT NULL,
            public_key BLOB NOT NULL,
            fingerprint TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            is_revoked INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, key_type, key_version)
        );
        CREATE TABLE search_documents (
            document_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL UNIQUE,
            conversation_id TEXT,
            sender_id TEXT,
            created_at TEXT NOT NULL,
            preview_ciphertext BLOB NOT NULL,
            preview_nonce BLOB NOT NULL,
            format_version INTEGER NOT NULL,
            source_version INTEGER NOT NULL,
            indexed_at TEXT NOT NULL
        );
        CREATE TABLE search_terms (
            token_digest BLOB NOT NULL,
            document_id TEXT NOT NULL REFERENCES search_documents(document_id)
                ON DELETE CASCADE,
            token_position INTEGER,
            PRIMARY KEY (token_digest, document_id, token_position)
        );
        CREATE INDEX ix_search_terms_document ON search_terms(document_id);
        CREATE TABLE local_settings (
            setting_key TEXT PRIMARY KEY,
            value_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE synchronisation_state (
            scope TEXT NOT NULL,
            scope_identifier TEXT NOT NULL DEFAULT '',
            cursor TEXT,
            version INTEGER,
            synchronised_at TEXT NOT NULL,
            PRIMARY KEY (scope, scope_identifier)
        );
        CREATE TABLE cache_entries (
            cache_key TEXT PRIMARY KEY,
            cache_type TEXT NOT NULL,
            storage_reference TEXT,
            size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
            created_at TEXT NOT NULL,
            last_accessed_at TEXT NOT NULL,
            expires_at TEXT,
            is_pinned INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX ix_cache_entries_eviction
            ON cache_entries(is_pinned, last_accessed_at);
        COMMIT;
        """
    )


def _migration_002(connection: sqlite3.Connection) -> None:
    """Add Task 17 queue orchestration, conflict and tombstone persistence."""
    connection.executescript(
        """
        ALTER TABLE offline_actions ADD COLUMN user_id TEXT;
        ALTER TABLE offline_actions
            ADD COLUMN scope_type TEXT NOT NULL DEFAULT 'global';
        ALTER TABLE offline_actions ADD COLUMN scope_id TEXT;
        ALTER TABLE offline_actions
            ADD COLUMN sequence_number INTEGER NOT NULL DEFAULT 0;
        ALTER TABLE offline_actions ADD COLUMN updated_at TEXT;
        ALTER TABLE offline_actions ADD COLUMN dependency_action_id TEXT;
        ALTER TABLE offline_actions ADD COLUMN server_reference TEXT;
        CREATE UNIQUE INDEX ux_offline_actions_sequence
            ON offline_actions(sequence_number) WHERE sequence_number > 0;
        CREATE INDEX ix_offline_actions_dependency
            ON offline_actions(dependency_action_id);

        CREATE TABLE synchronisation_conflicts (
            conflict_id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            scope TEXT NOT NULL,
            scope_id TEXT,
            action_id TEXT,
            detected_at TEXT NOT NULL,
            failure_code TEXT NOT NULL,
            attempted_content_preserved INTEGER NOT NULL DEFAULT 0,
            resolved_at TEXT,
            resolution TEXT
        );
        CREATE INDEX ix_synchronisation_conflicts_unresolved
            ON synchronisation_conflicts(resolved_at, detected_at);

        CREATE TABLE local_tombstones (
            scope TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            server_version INTEGER,
            created_at TEXT NOT NULL,
            reason_code TEXT NOT NULL,
            PRIMARY KEY (scope, resource_id)
        );
        """
    )


_MIGRATIONS: tuple[Migration, ...] = (_migration_001, _migration_002)


class ClientMigrationManager:
    """Apply explicit local schema migrations with recoverable backups."""

    def __init__(self, database_path: Path, recovery_directory: Path) -> None:
        self._database_path = database_path
        self._recovery_directory = recovery_directory

    @property
    def latest_version(self) -> int:
        """Return the newest migration version implemented by this build."""
        return len(_MIGRATIONS)

    def migrate_connection(self, connection: sqlite3.Connection) -> MigrationResult:
        """Migrate an already opened and key-verified connection atomically."""
        current = self._current_version(connection)
        if current > self.latest_version:
            raise LocalStorageError(
                user_message="The local cache was created by a newer client."
            )
        applied: list[int] = []
        try:
            for version in range(current + 1, self.latest_version + 1):
                _MIGRATIONS[version - 1](connection)
                connection.execute(
                    "UPDATE local_schema_version SET version = ? WHERE singleton = 1",
                    (version,),
                )
                applied.append(version)
            connection.commit()
        except sqlite3.Error as error:
            connection.rollback()
            raise LocalStorageError(
                user_message="The local cache could not be upgraded."
            ) from error
        return MigrationResult(current, self.latest_version, tuple(applied))

    async def get_current_version(self) -> int:
        """Read the current schema version from a closed or idle database."""
        return await asyncio.to_thread(self._read_version)

    async def create_backup(self) -> Path:
        """Create a byte-for-byte local recovery copy before destructive work."""
        return await asyncio.to_thread(self._create_backup_sync)

    async def restore_backup(self, backup_path: Path) -> None:
        """Restore a validated backup path into the configured database path."""
        await asyncio.to_thread(self._restore_backup_sync, backup_path)

    @staticmethod
    def _current_version(connection: sqlite3.Connection) -> int:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' "
            "AND name = 'local_schema_version'"
        ).fetchone()
        if table is None:
            return 0
        row = connection.execute(
            "SELECT version FROM local_schema_version WHERE singleton = 1"
        ).fetchone()
        if row is None:
            raise LocalStorageError(user_message="The local cache schema is invalid.")
        return int(row[0])

    def _read_version(self) -> int:
        if not self._database_path.exists():
            return 0
        connection = sqlite3.connect(self._database_path)
        try:
            return self._current_version(connection)
        finally:
            connection.close()

    def _create_backup_sync(self) -> Path:
        if not self._database_path.exists():
            raise LocalStorageError(user_message="There is no local cache to back up.")
        self._recovery_directory.mkdir(parents=True, exist_ok=True)
        destination = self._recovery_directory / "client_cache.backup.db"
        shutil.copy2(self._database_path, destination)
        return destination

    def _restore_backup_sync(self, backup_path: Path) -> None:
        backup = backup_path.resolve()
        recovery = self._recovery_directory.resolve()
        if recovery not in backup.parents or not backup.is_file():
            raise LocalStorageError(user_message="The local cache backup is invalid.")
        shutil.copy2(backup, self._database_path)
