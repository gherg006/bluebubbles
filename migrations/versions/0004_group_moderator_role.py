"""Use the specification's moderator group-role name.

Revision ID: 0004_group_moderator
Revises: 0003_contact_nicknames
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004_group_moderator"
down_revision: str | None = "0003_contact_nicknames"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Translate existing roles and replace the validating constraint."""
    op.execute(
        "ALTER TABLE conversation_members DROP CONSTRAINT IF EXISTS "
        "ck_conversation_members_role_valid"
    )
    op.execute(
        "UPDATE conversation_members SET member_role = 'moderator' "
        "WHERE member_role = 'admin'"
    )
    op.execute(
        "ALTER TABLE conversation_members ADD CONSTRAINT "
        "ck_conversation_members_role_valid CHECK "
        "(member_role IN ('owner', 'moderator', 'member'))"
    )


def downgrade() -> None:
    """Restore the legacy persisted role spelling."""
    op.execute(
        "ALTER TABLE conversation_members DROP CONSTRAINT IF EXISTS "
        "ck_conversation_members_role_valid"
    )
    op.execute(
        "UPDATE conversation_members SET member_role = 'admin' "
        "WHERE member_role = 'moderator'"
    )
    op.execute(
        "ALTER TABLE conversation_members ADD CONSTRAINT "
        "ck_conversation_members_role_valid CHECK "
        "(member_role IN ('owner', 'admin', 'member'))"
    )
