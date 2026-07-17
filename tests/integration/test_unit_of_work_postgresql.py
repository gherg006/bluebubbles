"""Opt-in PostgreSQL evidence for the Task 07 transaction boundary."""

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bluebubbles.server.database.models.identity import RoleORM
from bluebubbles.server.database.unit_of_work import (
    SqlAlchemyRepositoryFactory,
    UnitOfWorkFactory,
)
from bluebubbles.server.domain.users import User

_DATABASE_URL = os.environ.get("BLUEBUBBLES_TEST_DATABASE_URL")
_REQUIRES_DATABASE = pytest.mark.skipif(
    _DATABASE_URL is None,
    reason="BLUEBUBBLES_TEST_DATABASE_URL does not name a migrated PostgreSQL test DB",
)


@_REQUIRES_DATABASE
@pytest.mark.asyncio
async def test_real_unit_of_work_rolls_back_uncommitted_user() -> None:
    """All adapters share one real session and normal uncommitted exit is atomic."""
    assert _DATABASE_URL is not None
    engine = create_async_engine(_DATABASE_URL, pool_pre_ping=True)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    username = f"unit-of-work-{uuid4().hex}"
    try:
        async with sessions() as lookup_session:
            role_id = await lookup_session.scalar(select(RoleORM.id).limit(1))
        assert role_id is not None, "Task 05 seed roles must exist"

        factory = UnitOfWorkFactory(sessions, SqlAlchemyRepositoryFactory())
        async with factory() as unit_of_work:
            now = datetime.now(UTC)
            await unit_of_work.users.create(
                User(
                    id=uuid4(),
                    created_at=now,
                    updated_at=now,
                    username=username,
                    display_name="Unit of Work Test User",
                    role_id=role_id,
                )
            )
            assert (
                await unit_of_work.users.get_by_normalised_username(username)
                is not None
            )

        async with factory() as verification:
            assert await verification.users.get_by_normalised_username(username) is None
    finally:
        await engine.dispose()
