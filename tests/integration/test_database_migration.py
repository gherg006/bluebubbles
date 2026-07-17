"""Alembic initial-migration integration checks without external state."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_initial_migration_renders_complete_postgresql_sql() -> None:
    """The migration renders valid PostgreSQL DDL, seeds, and audit protection."""
    repository_root = Path(__file__).parents[2]
    result = subprocess.run(  # noqa: S603 - repository-owned executable path
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    sql = result.stdout
    assert "CREATE TABLE users" in sql
    assert "CREATE TABLE messages" in sql
    assert "CREATE TABLE audit_events" in sql
    assert "CREATE TRIGGER audit_events_no_update_delete" in sql
    assert "INSERT INTO roles" in sql
    assert "SuperAdministrator" in sql
    assert "0001_initial_schema" in sql
