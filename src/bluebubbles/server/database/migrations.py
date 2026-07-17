"""Read-only Alembic revision compatibility checks for server readiness."""

from __future__ import annotations

from alembic.runtime.migration import MigrationContext
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncConnection

EXPECTED_REVISION = "0004_group_moderator"


class SchemaRevisionMismatchError(RuntimeError):
    """Report an unsafe difference between installed and application schemas."""

    def __init__(self, current: str | None, expected: str) -> None:
        """Build a redacted error containing revision identifiers only."""
        self.current = current
        self.expected = expected
        super().__init__(
            f"Database schema revision {current or '<unversioned>'} does not match "
            f"expected revision {expected}"
        )


def get_expected_revision() -> str:
    """Return the only Alembic head compatible with this application build."""
    return EXPECTED_REVISION


def _read_current_revision(connection: Connection) -> str | None:
    """Read the revision using Alembic's supported migration context."""
    revision: str | None = MigrationContext.configure(connection).get_current_revision()
    return revision


async def get_current_revision(connection: AsyncConnection) -> str | None:
    """Return the installed Alembic revision without changing database state."""
    return await connection.run_sync(_read_current_revision)


async def verify_revision(connection: AsyncConnection) -> None:
    """Reject startup compatibility when the database is not at the expected head.

    Raises:
        SchemaRevisionMismatchError: If the schema is unversioned, behind, or ahead.
    """
    current = await get_current_revision(connection)
    expected = get_expected_revision()
    if current != expected:
        raise SchemaRevisionMismatchError(current, expected)
