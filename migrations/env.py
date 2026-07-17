"""Alembic environment for the asynchronous PostgreSQL server database."""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from bluebubbles.server.database import models  # noqa: F401
from bluebubbles.server.database.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def configure_protected_database_url() -> None:
    """Apply a protected migration URL without printing or retaining its source."""
    secret_file = os.environ.get("BLUEBUBBLES_DATABASE_URL_FILE")
    database_url = (
        Path(secret_file).read_text(encoding="utf-8").strip()
        if secret_file
        else os.environ.get("BLUEBUBBLES_DATABASE_URL")
    )
    if database_url:
        config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))


configure_protected_database_url()

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate PostgreSQL migration SQL without opening a connection."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=False,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_sync_migrations(connection: Connection) -> None:
    """Run configured migrations on an established synchronous facade."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Open the async engine and run migrations through its sync facade."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(run_sync_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
