"""Persist owner-specific contact nicknames.

Revision ID: 0003_contact_nicknames
Revises: 0002_refresh_reuse
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003_contact_nicknames"
down_revision: str | None = "0002_refresh_reuse"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add bounded owner-private contact display metadata."""
    op.execute(
        "ALTER TABLE contact_relationships "
        "ADD COLUMN IF NOT EXISTS nickname VARCHAR(100)"
    )


def downgrade() -> None:
    """Remove nicknames without changing contact relationships."""
    op.execute("ALTER TABLE contact_relationships DROP COLUMN IF EXISTS nickname")
