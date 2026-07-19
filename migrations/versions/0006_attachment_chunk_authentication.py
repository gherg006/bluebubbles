"""Persist resumable attachment chunk authentication metadata.

Revision ID: 0006_attachment_chunk_auth
Revises: 0005_text_with_attachment
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006_attachment_chunk_auth"
down_revision: str | None = "0005_text_with_attachment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Store nonce and GCM tag alongside recoverable temporary chunk state."""
    # The initial revision deliberately renders the current ORM metadata so a
    # new installation already has these columns. Existing pre-Task-15
    # databases do not. PostgreSQL's IF NOT EXISTS makes this revision safe for
    # both paths instead of failing a fresh CI migration with DuplicateColumn.
    op.execute(
        "ALTER TABLE upload_session_chunks " "ADD COLUMN IF NOT EXISTS nonce BYTEA"
    )
    op.execute(
        "ALTER TABLE upload_session_chunks "
        "ADD COLUMN IF NOT EXISTS authentication_tag BYTEA"
    )
    op.execute(
        "DELETE FROM upload_session_chunks WHERE nonce IS NULL "
        "OR authentication_tag IS NULL"
    )
    op.alter_column("upload_session_chunks", "nonce", nullable=False)
    op.alter_column("upload_session_chunks", "authentication_tag", nullable=False)


def downgrade() -> None:
    """Remove temporary chunk authentication metadata."""
    op.drop_column("upload_session_chunks", "authentication_tag")
    op.drop_column("upload_session_chunks", "nonce")
