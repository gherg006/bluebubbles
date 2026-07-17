"""Unit of Work session ownership, composition, and state-transition tests."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from bluebubbles.server.database.session import create_session_factory, session_scope
from bluebubbles.server.database.unit_of_work import (
    ServerRepositories,
    SqlAlchemyRepositoryFactory,
    UnitOfWork,
    UnitOfWorkFactory,
    UnitOfWorkStateError,
)
from bluebubbles.shared.errors.exceptions import ConflictError


def _repositories() -> ServerRepositories:
    repository = cast(Any, object())
    return ServerRepositories(
        users=repository,
        sessions=repository,
        authentication=repository,
        contacts=repository,
        public_keys=repository,
        conversations=repository,
        messages=repository,
        attachments=repository,
        audit=repository,
        announcements=repository,
        administration=repository,
        configuration=repository,
        outbox=repository,
    )


def _session() -> tuple[AsyncSession, MagicMock]:
    mock = MagicMock(spec=AsyncSession)
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.flush = AsyncMock()
    mock.close = AsyncMock()
    return cast(AsyncSession, mock), mock


@pytest.mark.asyncio
async def test_explicit_commit_is_retained_and_session_is_closed() -> None:
    """A successful explicit commit is not followed by an exit rollback."""
    session, mock = _session()
    unit_of_work = UnitOfWork(session, _repositories())

    async with unit_of_work as active:
        assert active is unit_of_work
        assert active.users is active.repositories.users
        await active.flush()
        await active.commit()
        await active.commit()

    mock.flush.assert_awaited_once()
    mock.commit.assert_awaited_once()
    mock.rollback.assert_not_awaited()
    mock.close.assert_awaited_once()
    assert unit_of_work.committed
    assert not unit_of_work.rolled_back
    assert unit_of_work.closed


@pytest.mark.asyncio
async def test_normal_uncommitted_exit_rolls_back_and_closes() -> None:
    """Leaving without the required explicit commit cannot persist partial work."""
    session, mock = _session()
    unit_of_work = UnitOfWork(session, _repositories())

    async with unit_of_work:
        pass

    mock.rollback.assert_awaited_once()
    mock.commit.assert_not_awaited()
    mock.close.assert_awaited_once()
    assert unit_of_work.rolled_back


@pytest.mark.asyncio
async def test_body_error_is_preserved_when_cleanup_also_fails() -> None:
    """A cleanup failure cannot conceal the transaction's original cause."""
    session, mock = _session()
    mock.rollback.side_effect = RuntimeError("cleanup details")
    unit_of_work = UnitOfWork(session, _repositories())

    with pytest.raises(ValueError, match="business failure"):
        async with unit_of_work:
            raise ValueError("business failure")

    mock.close.assert_awaited_once()
    assert unit_of_work.closed
    assert unit_of_work.rolled_back


@pytest.mark.asyncio
async def test_cancellation_rolls_back_closes_and_remains_cancellation() -> None:
    """Cooperative task cancellation retains its identity after safe cleanup."""
    session, mock = _session()
    unit_of_work = UnitOfWork(session, _repositories())

    with pytest.raises(asyncio.CancelledError):
        async with unit_of_work:
            raise asyncio.CancelledError

    mock.rollback.assert_awaited_once()
    mock.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_completion_states_reject_conflicting_or_closed_operations() -> None:
    """Commit and rollback cannot contradict one another or outlive the session."""
    session, _ = _session()
    committed = UnitOfWork(session, _repositories())
    await committed.commit()
    with pytest.raises(UnitOfWorkStateError):
        await committed.rollback()

    rolled_session, _ = _session()
    rolled_back = UnitOfWork(rolled_session, _repositories())
    await rolled_back.rollback()
    await rolled_back.rollback()
    with pytest.raises(UnitOfWorkStateError):
        await rolled_back.commit()

    closed_session, _ = _session()
    closed = UnitOfWork(closed_session, _repositories())
    async with closed:
        pass
    with pytest.raises(UnitOfWorkStateError):
        await closed.flush()
    with pytest.raises(UnitOfWorkStateError):
        async with closed:
            pass


@pytest.mark.asyncio
async def test_failed_commit_rolls_back_and_redacts_integrity_details() -> None:
    """Commit conflicts complete by rollback without exposing SQL or parameters."""
    session, mock = _session()
    mock.commit.side_effect = IntegrityError(
        "INSERT secret SQL", {"password": "secret"}, Exception("constraint detail")
    )
    unit_of_work = UnitOfWork(session, _repositories())

    with pytest.raises(ConflictError) as error:
        await unit_of_work.commit()

    mock.rollback.assert_awaited_once()
    assert unit_of_work.rolled_back
    assert "secret" not in error.value.user_message
    assert "password" not in str(error.value)


def test_factory_creates_fresh_sessions_and_repository_bundles() -> None:
    """Every factory call isolates both its session and repository collection."""
    first, _ = _session()
    second, _ = _session()
    sessions: Iterator[AsyncSession] = iter((first, second))
    session_factory = MagicMock(side_effect=lambda: next(sessions))
    seen: list[AsyncSession] = []

    def repositories(session: AsyncSession) -> ServerRepositories:
        seen.append(session)
        return _repositories()

    factory = UnitOfWorkFactory(
        cast(async_sessionmaker[AsyncSession], session_factory), repositories
    )
    first_unit = factory()
    second_unit = factory()

    assert first_unit is not second_unit
    assert first_unit.repositories is not second_unit.repositories
    assert seen == [first, second]


def test_sqlalchemy_repository_factory_shares_exactly_one_session() -> None:
    """Every production adapter in a bundle receives the caller-owned session."""
    session, _ = _session()
    repositories = SqlAlchemyRepositoryFactory()(session)

    assert all(
        vars(repository)["_session"] is session
        for repository in (
            repositories.users,
            repositories.sessions,
            repositories.contacts,
            repositories.public_keys,
            repositories.conversations,
            repositories.messages,
            repositories.attachments,
            repositories.audit,
            repositories.announcements,
            repositories.administration,
            repositories.configuration,
            repositories.outbox,
        )
    )


@pytest.mark.asyncio
async def test_session_scope_never_auto_commits_and_always_cleans_up() -> None:
    """The lower-level session helper preserves explicit completion semantics."""
    session, mock = _session()
    factory = cast(async_sessionmaker[AsyncSession], lambda: session)

    async with session_scope(factory) as active:
        assert active is session

    mock.commit.assert_not_awaited()
    mock.rollback.assert_awaited_once()
    mock.close.assert_awaited_once()


def test_session_factory_uses_safe_transaction_defaults() -> None:
    """Created sessions retain state after commit and never flush implicitly."""
    engine = cast(AsyncEngine, MagicMock(spec=AsyncEngine))

    factory = create_session_factory(engine)

    assert factory.kw["bind"] is engine
    assert factory.kw["expire_on_commit"] is False
    assert factory.kw["autoflush"] is False
