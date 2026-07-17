"""Application-owned PostgreSQL engine lifecycle and health checks."""

from __future__ import annotations

import logging
from time import perf_counter

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bluebubbles.server.configuration.settings import DatabaseSettings
from bluebubbles.server.database.migrations import (
    SchemaRevisionMismatchError,
    verify_revision,
)
from bluebubbles.server.database.session import create_session_factory
from bluebubbles.shared.errors.exceptions import DatabaseUnavailableError
from bluebubbles.shared.models.health import ComponentHealth, HealthState


class DatabaseManager:
    """Own the SQLAlchemy engine, pool, session factory, and schema readiness."""

    def __init__(
        self,
        settings: DatabaseSettings,
        logger: logging.Logger,
        *,
        engine: AsyncEngine | None = None,
    ) -> None:
        """Create an unconnected engine without opening a database connection.

        Args:
            settings: Validated PostgreSQL connection and pool settings.
            logger: Sanitised application logger.
            engine: Optional test or deployment-specific async engine.
        """
        self._settings = settings
        self._logger = logger
        self._engine = engine or self._build_engine()
        self._session_factory: async_sessionmaker[AsyncSession] = (
            create_session_factory(self._engine)
        )
        self._started = False

    @property
    def started(self) -> bool:
        """Return whether connectivity and schema compatibility were verified."""
        return self._started

    async def start(self) -> None:
        """Verify PostgreSQL connectivity and the exact Alembic revision.

        Raises:
            DatabaseUnavailableError: If PostgreSQL cannot be reached or verified.
            SchemaRevisionMismatchError: If the installed schema is incompatible.
        """
        if self._started:
            return
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                await verify_revision(connection)
        except SchemaRevisionMismatchError:
            await self._engine.dispose()
            raise
        except SQLAlchemyError as error:
            await self._engine.dispose()
            raise DatabaseUnavailableError(
                user_message="The database is unavailable.",
                technical_message="PostgreSQL startup verification failed.",
                retryable=True,
            ) from error
        self._started = True

    async def stop(self) -> None:
        """Dispose every pooled connection; repeated calls are safe."""
        try:
            await self._engine.dispose()
        except SQLAlchemyError as error:
            self._logger.error(
                "Database pool disposal failed",
                extra={"failure_category": type(error).__name__},
            )
        finally:
            self._started = False

    async def check_health(self) -> ComponentHealth:
        """Return a credential-free PostgreSQL connectivity measurement."""
        if not self._started:
            return ComponentHealth(name="database", state=HealthState.UNHEALTHY)
        started_at = perf_counter()
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return ComponentHealth(name="database", state=HealthState.UNHEALTHY)
        return ComponentHealth(
            name="database",
            state=HealthState.HEALTHY,
            latency_ms=(perf_counter() - started_at) * 1000,
        )

    def create_session(self) -> AsyncSession:
        """Create one request-scoped session after successful startup.

        Raises:
            DatabaseUnavailableError: If called before database readiness.
        """
        if not self._started:
            raise DatabaseUnavailableError(
                user_message="The database is unavailable.",
                technical_message="A database session was requested before startup.",
                retryable=True,
            )
        return self._session_factory()

    def _build_engine(self) -> AsyncEngine:
        return create_async_engine(
            self._settings.url.get_secret_value(),
            echo=self._settings.echo_sql,
            pool_pre_ping=True,
            pool_size=self._settings.pool_size,
            max_overflow=self._settings.maximum_overflow,
            pool_timeout=self._settings.connection_timeout_seconds,
            pool_recycle=self._settings.pool_recycle_seconds,
            connect_args={
                "command_timeout": self._settings.statement_timeout_seconds,
                "timeout": self._settings.connection_timeout_seconds,
            },
        )
