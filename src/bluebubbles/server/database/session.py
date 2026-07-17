"""Async SQLAlchemy session construction and scoped cleanup helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create the server's short-lived, non-expiring async session factory.

    Args:
        engine: Application-owned asynchronous SQLAlchemy engine.

    Returns:
        A factory that creates a distinct session for each call.
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Yield one caller-controlled session and guarantee safe cleanup.

    This helper never commits automatically. An unfinished session is rolled back
    both after an exception and after a normal exit, then closed.

    Args:
        session_factory: Factory used to create the isolated session.

    Yields:
        One asynchronous SQLAlchemy session.

    Raises:
        BaseException: Re-raises the body or cleanup error after rollback/close.
    """
    session = session_factory()
    try:
        yield session
    finally:
        try:
            await session.rollback()
        finally:
            await session.close()
