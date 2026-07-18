"""Activate the administrative permission catalogue and alert deduplication.

Revision ID: 0007_admin_monitoring
Revises: 0006_attachment_chunk_auth
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from bluebubbles.server.database.seed import (
    PERMISSION_DESCRIPTIONS,
    ROLE_SEEDS,
    stable_seed_id,
)

revision: str = "0007_admin_monitoring"
down_revision: str | None = "0006_attachment_chunk_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Insert new stable permissions/grants and enforce alert-type deduplication."""
    for permission, description in PERMISSION_DESCRIPTIONS.items():
        op.execute(
            sa.text(
                "INSERT INTO permissions (id, name, description, created_at) "
                "VALUES (:id, :name, :description, CURRENT_TIMESTAMP) "
                "ON CONFLICT (name) DO NOTHING"
            ).bindparams(
                id=stable_seed_id("permission", permission.value),
                name=permission.value,
                description=description,
            )
        )
    for role in ROLE_SEEDS:
        for permission in role.permissions:
            op.execute(
                sa.text(
                    "INSERT INTO role_permissions (role_id, permission_id, created_at) "
                    "VALUES (:role_id, :permission_id, CURRENT_TIMESTAMP) "
                    "ON CONFLICT (role_id, permission_id) DO NOTHING"
                ).bindparams(
                    role_id=stable_seed_id("role", role.name),
                    permission_id=stable_seed_id("permission", permission.value),
                )
            )
    op.create_index(
        "uq_security_alerts_type", "security_alerts", ["alert_type"], unique=True
    )


def downgrade() -> None:
    """Drop only the alert index; catalogue rows remain for audit-safe downgrade."""
    op.drop_index("uq_security_alerts_type", table_name="security_alerts")
