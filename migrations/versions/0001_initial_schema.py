"""Create the complete BlueBubbles Version 1.0 PostgreSQL schema.

Revision ID: 0001_initial_schema
Revises: None
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import cast

from alembic import op
from sqlalchemy import Table

from bluebubbles.server.database.base import Base
from bluebubbles.server.database.models import AuditChainStateORM  # noqa: F401
from bluebubbles.server.database.models.identity import (
    PermissionORM,
    RoleORM,
    RolePermissionORM,
)
from bluebubbles.server.database.seed import (
    PERMISSION_DESCRIPTIONS,
    ROLE_SEEDS,
    stable_seed_id,
)

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

AUDIT_TRIGGER_FUNCTION = """
CREATE FUNCTION reject_audit_modification()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_events are append-only';
END;
$$ LANGUAGE plpgsql
"""

AUDIT_TRIGGER = """
CREATE TRIGGER audit_events_no_update_delete
BEFORE UPDATE OR DELETE ON audit_events
FOR EACH ROW EXECUTE FUNCTION reject_audit_modification()
"""


def upgrade() -> None:
    """Create tables, indexes, audit protection, and fixed catalogue rows."""
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=False)

    timestamp = datetime(2026, 7, 17, tzinfo=UTC)
    op.bulk_insert(
        cast(Table, RoleORM.__table__),
        [
            {
                "id": stable_seed_id("role", seed.name),
                "name": seed.name,
                "description": seed.description,
                "priority": seed.priority,
                "is_system_role": True,
                "created_at": timestamp,
                "updated_at": timestamp,
            }
            for seed in ROLE_SEEDS
        ],
    )
    op.bulk_insert(
        cast(Table, PermissionORM.__table__),
        [
            {
                "id": stable_seed_id("permission", permission.value),
                "name": permission.value,
                "description": description,
                "created_at": timestamp,
            }
            for permission, description in PERMISSION_DESCRIPTIONS.items()
        ],
    )
    op.bulk_insert(
        cast(Table, RolePermissionORM.__table__),
        [
            {
                "role_id": stable_seed_id("role", seed.name),
                "permission_id": stable_seed_id("permission", permission.value),
                "created_at": timestamp,
            }
            for seed in ROLE_SEEDS
            for permission in sorted(seed.permissions, key=lambda item: item.value)
        ],
    )
    op.bulk_insert(
        cast(Table, AuditChainStateORM.__table__),
        [
            {
                "id": 1,
                "latest_sequence_number": 0,
                "latest_hash": None,
                "updated_at": timestamp,
            }
        ],
    )

    if bind.dialect.name == "postgresql":
        op.execute(AUDIT_TRIGGER_FUNCTION)
        op.execute(AUDIT_TRIGGER)


def downgrade() -> None:
    """Remove the initial empty schema; production rollback requires a backup."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS audit_events_no_update_delete ON audit_events"
        )
        op.execute("DROP FUNCTION IF EXISTS reject_audit_modification()")
    Base.metadata.drop_all(bind=bind, checkfirst=False)
