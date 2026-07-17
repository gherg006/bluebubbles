"""Database metadata, seed catalogue, and migration compatibility tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from bluebubbles.server.database.base import NAMING_CONVENTION, Base
from bluebubbles.server.database.migrations import (
    EXPECTED_REVISION,
    SchemaRevisionMismatchError,
    get_current_revision,
    get_expected_revision,
    verify_revision,
)
from bluebubbles.server.database.models import MessageORM, UserORM
from bluebubbles.server.database.seed import (
    PERMISSION_DESCRIPTIONS,
    ROLE_SEEDS,
    seed_system_catalogue,
    stable_seed_id,
)
from bluebubbles.server.domain.users import Permission

MANDATORY_TABLES = {
    "roles",
    "permissions",
    "role_permissions",
    "users",
    "local_credentials",
    "sessions",
    "login_attempts",
    "contact_relationships",
    "user_public_keys",
    "conversations",
    "direct_conversation_pairs",
    "conversation_members",
    "conversation_events",
    "messages",
    "message_recipient_keys",
    "message_deliveries",
    "attachments",
    "attachment_recipient_keys",
    "attachment_chunks",
    "upload_sessions",
    "announcements",
    "announcement_acknowledgements",
    "audit_events",
    "audit_chain_state",
    "security_alerts",
    "configuration_versions",
    "outbox_events",
    "worker_execution_records",
    "data_export_jobs",
    "data_deletion_requests",
    "policy_acknowledgements",
}


def test_metadata_contains_complete_version_one_scope() -> None:
    """All mandatory and deliberately selected optional tables are registered."""
    assert set(Base.metadata.tables) >= MANDATORY_TABLES
    assert {"message_versions", "upload_session_chunks"} <= set(Base.metadata.tables)
    assert len(Base.metadata.tables) == 33


def test_metadata_uses_deterministic_names_and_security_safe_message_columns() -> None:
    """Names are stable and the message table has no plaintext-capable field."""
    assert NAMING_CONVENTION["fk"].startswith("fk_")
    assert NAMING_CONVENTION["pk"].startswith("pk_")
    assert "plaintext" not in MessageORM.__table__.columns
    assert {
        "ciphertext",
        "nonce",
        "authentication_tag",
        "signature",
    } <= set(MessageORM.__table__.columns.keys())
    assert cast(Any, UserORM.__table__.primary_key).name == "pk_users"


def test_critical_unique_checks_and_partial_indexes_are_present() -> None:
    """Database-enforced business invariants remain discoverable by stable names."""
    constraints = {
        constraint.name
        for table in Base.metadata.tables.values()
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint | UniqueConstraint)
    }
    indexes = {
        index.name
        for table in Base.metadata.tables.values()
        for index in table.indexes
        if isinstance(index, Index)
    }
    assert {
        "uq_users_normalised_username",
        "uq_direct_user_pair",
        "uq_message_recipient",
        "uq_attachment_chunk",
        "ck_contact_relationships_users_differ",
        "ck_messages_payload_size_non_negative",
    } <= constraints
    assert {
        "uq_users_directory_guid",
        "uq_primary_user_key",
        "uq_active_conversation_member",
        "uq_active_group_owner",
        "ix_messages_conversation_order",
        "ix_outbox_unpublished",
    } <= indexes


def test_seed_catalogue_is_complete_stable_and_privilege_ordered() -> None:
    """Fixed seeds cover the domain catalogue and use reproducible identifiers."""
    assert set(PERMISSION_DESCRIPTIONS) == set(Permission)
    assert [seed.name for seed in ROLE_SEEDS] == [
        "Employee",
        "Helpdesk",
        "HR",
        "Administrator",
        "SuperAdministrator",
    ]
    assert [seed.priority for seed in ROLE_SEEDS] == [10, 20, 30, 40, 50]
    assert ROLE_SEEDS[-1].permissions == frozenset(Permission)
    assert stable_seed_id("role", "Employee") == stable_seed_id("role", "Employee")
    assert stable_seed_id("role", "Employee") != stable_seed_id(
        "permission", "Employee"
    )


class _ScalarResult:
    """Provide the narrow scalar-result surface used by the seed routine."""

    def __init__(self, values: list[object]) -> None:
        self._values = values

    def all(self) -> list[object]:
        """Return configured result values."""
        return self._values


@pytest.mark.asyncio
async def test_seed_routine_adds_missing_rows_without_committing() -> None:
    """Controlled seeding leaves transaction ownership with its caller."""
    session = MagicMock(spec=AsyncSession)
    session.scalars = AsyncMock(side_effect=[_ScalarResult([]), _ScalarResult([])])
    session.flush = AsyncMock()
    session.execute = AsyncMock(return_value=[])
    session.commit = AsyncMock()
    session.add = MagicMock()

    await seed_system_catalogue(
        cast(AsyncSession, session),
        created_at=datetime(2026, 7, 17, tzinfo=UTC),
    )

    expected_grants = sum(len(seed.permissions) for seed in ROLE_SEEDS)
    assert session.add.call_count == len(ROLE_SEEDS) + len(Permission) + expected_grants
    session.flush.assert_awaited_once()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_revision_helpers_accept_only_the_application_head() -> None:
    """Readiness accepts the expected revision and rejects all other states."""
    connection = MagicMock(spec=AsyncConnection)
    connection.run_sync = AsyncMock(return_value=EXPECTED_REVISION)
    typed_connection = cast(AsyncConnection, connection)

    assert get_expected_revision() == EXPECTED_REVISION
    assert await get_current_revision(typed_connection) == EXPECTED_REVISION
    await verify_revision(typed_connection)

    connection.run_sync.return_value = None
    with pytest.raises(SchemaRevisionMismatchError) as error:
        await verify_revision(typed_connection)
    assert error.value.current is None
    assert error.value.expected == EXPECTED_REVISION
    assert "<unversioned>" in str(error.value)


def test_stable_seed_ids_are_uuid_values() -> None:
    """Seed identities use native UUID values suitable for PostgreSQL UUID columns."""
    assert isinstance(stable_seed_id("role", "Employee"), UUID)
