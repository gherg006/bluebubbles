"""Retain the immediately previous refresh digest for reuse detection.

Revision ID: 0002_refresh_reuse
Revises: 0001_initial_schema
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_refresh_reuse"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add a one-way previous-token digest without exposing raw tokens."""
    # The original baseline renders live metadata. IF NOT EXISTS keeps both an
    # existing Task 08 database and a newly rendered baseline upgrade safe.
    op.execute(
        "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS "
        "previous_refresh_token_hash BYTEA"
    )


def downgrade() -> None:
    """Remove reuse history while retaining the current refresh digest."""
    op.execute("ALTER TABLE sessions DROP COLUMN IF EXISTS previous_refresh_token_hash")
