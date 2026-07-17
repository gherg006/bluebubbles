"""Permit encrypted text messages carrying attachment references.

Revision ID: 0005_text_with_attachment
Revises: 0004_group_moderator
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_text_with_attachment"
down_revision: str | None = "0004_group_moderator"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Replace the exact convention-generated message-type constraint."""
    op.execute(
        "ALTER TABLE messages DROP CONSTRAINT IF EXISTS "
        "ck_messages_message_type_valid"
    )
    op.execute(
        "ALTER TABLE messages ADD CONSTRAINT ck_messages_message_type_valid "
        "CHECK (message_type IN "
        "('text', 'system', 'attachment', 'text_with_attachment'))"
    )


def downgrade() -> None:
    """Restore the previous Version 1 message-type constraint."""
    op.execute(
        "ALTER TABLE messages DROP CONSTRAINT IF EXISTS "
        "ck_messages_message_type_valid"
    )
    op.execute(
        "ALTER TABLE messages ADD CONSTRAINT ck_messages_message_type_valid "
        "CHECK (message_type IN ('text', 'system', 'attachment'))"
    )
