"""Real PostgreSQL workflow evidence for Task 06 repositories."""

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bluebubbles.server.database.models.identity import RoleORM
from bluebubbles.server.domain.outbox import OutboxEvent
from bluebubbles.server.domain.users import User
from bluebubbles.server.repositories.sqlalchemy.outbox import (
    SqlAlchemyOutboxRepository,
)
from bluebubbles.server.repositories.sqlalchemy.users import SqlAlchemyUserRepository
from bluebubbles.shared.errors.exceptions import ConflictError

_DATABASE_URL = os.environ.get("BLUEBUBBLES_TEST_DATABASE_URL")
_REQUIRES_DATABASE = pytest.mark.skipif(
    _DATABASE_URL is None,
    reason="BLUEBUBBLES_TEST_DATABASE_URL does not name a migrated PostgreSQL test DB",
)


@_REQUIRES_DATABASE
@pytest.mark.asyncio
async def test_real_postgresql_user_and_outbox_workflow() -> None:
    """Create/read a user, enforce uniqueness, and skip-lock claim an outbox event."""
    assert _DATABASE_URL is not None
    engine = create_async_engine(_DATABASE_URL, pool_pre_ping=True)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    try:
        async with sessions() as session:
            role_id = await session.scalar(select(RoleORM.id).limit(1))
            assert role_id is not None, "Task 05 seed roles must exist"
            unique_name = f"repository-{uuid4().hex}"
            user = User(
                id=uuid4(),
                created_at=now,
                updated_at=now,
                username=unique_name,
                display_name="Repository Test User",
                role_id=role_id,
            )
            users = SqlAlchemyUserRepository(session)
            await users.create(user)
            assert await users.get_by_normalised_username(unique_name) == user
            duplicate = User(
                id=uuid4(),
                created_at=now,
                updated_at=now,
                username=unique_name,
                display_name="Duplicate",
                role_id=role_id,
            )
            with pytest.raises(ConflictError):
                await users.create(duplicate)
            await session.rollback()

        async with sessions() as session:
            event = OutboxEvent(
                id=uuid4(),
                created_at=now,
                updated_at=now,
                event_type="repository.test",
                aggregate_type="test",
                aggregate_id=uuid4(),
                protocol_version=1,
                payload={"safe": True},
                available_at=now - timedelta(seconds=1),
            )
            outbox = SqlAlchemyOutboxRepository(session)
            await outbox.add(event)
            claimed = await outbox.claim_batch("repository-test", 1, now)
            assert [item.id for item in claimed] == [event.id]
            await session.rollback()
    finally:
        await engine.dispose()
