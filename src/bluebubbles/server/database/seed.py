"""Idempotent fixed-role and permission catalogue seeding."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.identity import (
    PermissionORM,
    RoleORM,
    RolePermissionORM,
)
from bluebubbles.server.domain.users import Permission

SEED_NAMESPACE = UUID("f646f4ee-a91c-56d0-a66e-172a75944939")


@dataclass(frozen=True, slots=True)
class RoleSeed:
    """Describe one fixed role without embedding persistence behaviour."""

    name: str
    description: str
    priority: int
    permissions: frozenset[Permission]


PERMISSION_DESCRIPTIONS: Mapping[Permission, str] = {
    Permission.SEND_MESSAGE: "Send encrypted messages",
    Permission.DELETE_MESSAGE: "Delete messages according to policy",
    Permission.CREATE_GROUP: "Create group conversations",
    Permission.DELETE_GROUP: "Delete group conversations according to policy",
    Permission.UPLOAD_FILE: "Upload encrypted attachments",
    Permission.DOWNLOAD_FILE: "Download authorised encrypted attachments",
    Permission.MANAGE_USERS: "Administer user account state and roles",
    Permission.VIEW_AUDIT_LOG: "View authorised audit records",
    Permission.SEND_ANNOUNCEMENTS: "Publish organisational announcements",
    Permission.MANAGE_SERVER: "Administer server configuration and operations",
    Permission.ADMIN_DASHBOARD: "View the administrative dashboard",
    Permission.USER_VIEW: "View administrative user summaries",
    Permission.USER_SEARCH: "Search administrative user records",
    Permission.USER_ENABLE: "Enable user accounts",
    Permission.USER_DISABLE: "Disable user accounts",
    Permission.USER_ASSIGN_ROLE: "Assign non-super-administrator roles",
    Permission.USER_ASSIGN_SUPER_ROLE: "Assign the SuperAdministrator role",
    Permission.SESSION_VIEW: "View token-free session metadata",
    Permission.SESSION_REVOKE: "Revoke server sessions",
    Permission.CONNECTION_VIEW: "View active connection metadata",
    Permission.CONNECTION_DISCONNECT: "Disconnect active connections",
    Permission.AUDIT_VIEW: "View full authorised audit metadata",
    Permission.AUDIT_VIEW_LIMITED: "View privacy-filtered audit metadata",
    Permission.AUDIT_EXPORT: "Create protected audit exports",
    Permission.AUDIT_VERIFY: "Verify the audit hash chain",
    Permission.ALERT_VIEW: "View security alerts",
    Permission.ALERT_ACKNOWLEDGE: "Acknowledge security alerts",
    Permission.ALERT_RESOLVE: "Resolve security alerts",
    Permission.ANNOUNCEMENT_MANAGE: "Publish and withdraw announcements",
    Permission.HEALTH_VIEW_DETAILED: "View detailed component health",
    Permission.WORKER_VIEW: "View managed worker state",
    Permission.WORKER_RUN: "Run approved workers manually",
    Permission.WORKER_CONTROL: "Pause and resume optional workers",
    Permission.CONFIGURATION_VIEW: "View public configuration history",
    Permission.CONFIGURATION_MODIFY: "Modify approved public settings",
    Permission.EXPORT_MANAGE: "Manage protected export jobs",
    Permission.SYSTEM_MAINTENANCE: "Control server maintenance mode",
    Permission.DIAGNOSTIC_RUN: "Run privacy-safe server diagnostics",
}

STANDARD_PERMISSIONS = frozenset(
    {
        Permission.SEND_MESSAGE,
        Permission.CREATE_GROUP,
        Permission.UPLOAD_FILE,
        Permission.DOWNLOAD_FILE,
    }
)

ROLE_SEEDS: tuple[RoleSeed, ...] = (
    RoleSeed("Employee", "Standard organisational user", 10, STANDARD_PERMISSIONS),
    RoleSeed(
        "Helpdesk",
        "Support operator with delegated user administration",
        20,
        STANDARD_PERMISSIONS
        | {
            Permission.MANAGE_USERS,
            Permission.USER_VIEW,
            Permission.USER_SEARCH,
            Permission.SESSION_VIEW,
            Permission.SESSION_REVOKE,
            Permission.CONNECTION_VIEW,
            Permission.AUDIT_VIEW_LIMITED,
            Permission.DIAGNOSTIC_RUN,
        },
    ),
    RoleSeed(
        "HR",
        "Human-resources operator with delegated user administration",
        30,
        STANDARD_PERMISSIONS
        | {
            Permission.MANAGE_USERS,
            Permission.SEND_ANNOUNCEMENTS,
            Permission.USER_VIEW,
            Permission.USER_SEARCH,
            Permission.USER_ENABLE,
            Permission.USER_DISABLE,
            Permission.SESSION_VIEW,
            Permission.SESSION_REVOKE,
            Permission.AUDIT_VIEW_LIMITED,
        },
    ),
    RoleSeed(
        "Administrator",
        "Application administrator",
        40,
        frozenset(Permission)
        - {
            Permission.MANAGE_SERVER,
            Permission.USER_ASSIGN_SUPER_ROLE,
            Permission.SYSTEM_MAINTENANCE,
        },
    ),
    RoleSeed(
        "SuperAdministrator",
        "Highest fixed application administrator role",
        50,
        frozenset(Permission),
    ),
)


def stable_seed_id(category: str, name: str) -> UUID:
    """Return a repeatable UUID for a fixed catalogue item."""
    return uuid5(SEED_NAMESPACE, f"{category}:{name}")


async def seed_system_catalogue(
    session: AsyncSession, *, created_at: datetime | None = None
) -> None:
    """Insert missing fixed roles, permissions, and grants without overwriting rows.

    The caller owns the transaction and must commit explicitly. Existing descriptions,
    priorities, and grants are retained so administrator customisation is never silently
    replaced.
    """
    timestamp = created_at or datetime.now(UTC)
    roles = {
        role.name: role
        for role in (
            await session.scalars(
                select(RoleORM).where(
                    RoleORM.name.in_(seed.name for seed in ROLE_SEEDS)
                )
            )
        ).all()
    }
    for seed in ROLE_SEEDS:
        if seed.name not in roles:
            role = RoleORM(
                id=stable_seed_id("role", seed.name),
                name=seed.name,
                description=seed.description,
                priority=seed.priority,
                is_system_role=True,
                created_at=timestamp,
                updated_at=timestamp,
            )
            session.add(role)
            roles[seed.name] = role

    permissions = {
        permission.name: permission
        for permission in (
            await session.scalars(
                select(PermissionORM).where(
                    PermissionORM.name.in_(item.value for item in Permission)
                )
            )
        ).all()
    }
    for permission, description in PERMISSION_DESCRIPTIONS.items():
        if permission.value not in permissions:
            record = PermissionORM(
                id=stable_seed_id("permission", permission.value),
                name=permission.value,
                description=description,
                created_at=timestamp,
            )
            session.add(record)
            permissions[permission.value] = record

    await session.flush()
    existing_grants = set(
        await session.execute(
            select(RolePermissionORM.role_id, RolePermissionORM.permission_id)
        )
    )
    for seed in ROLE_SEEDS:
        role_id = roles[seed.name].id
        for permission in seed.permissions:
            permission_id = permissions[permission.value].id
            if (role_id, permission_id) not in existing_grants:
                session.add(
                    RolePermissionORM(
                        role_id=role_id,
                        permission_id=permission_id,
                        created_at=timestamp,
                    )
                )
