"""Async SQLAlchemy configuration-version repository."""

from collections.abc import Mapping
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.configuration import ConfigurationVersionORM
from bluebubbles.server.domain.configuration import ConfigurationRevision
from bluebubbles.server.repositories.sqlalchemy._common import flush_changes


class SqlAlchemyConfigurationRepository:
    """Persist append-only validated public configuration revisions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        revision: ConfigurationRevision,
        *,
        reason: str,
        restart_required: bool,
    ) -> ConfigurationRevision:
        """Stage one secret-free configuration revision."""
        if not reason.strip():
            raise ValueError("Configuration change reason is required")
        latest = await self._latest_record()
        self._session.add(
            ConfigurationVersionORM(
                id=uuid4(),
                version_number=revision.revision,
                configuration=dict(revision.public_values),
                changed_by=revision.changed_by,
                change_reason=reason.strip(),
                changed_at=revision.changed_at,
                previous_version_id=latest.id if latest is not None else None,
                restart_required=restart_required,
            )
        )
        await flush_changes(self._session)
        return revision

    async def get_latest(self) -> ConfigurationRevision | None:
        """Return the latest secret-free configuration revision."""
        record = await self._latest_record()
        if record is None:
            return None
        return ConfigurationRevision(
            revision=record.version_number,
            changed_at=record.changed_at,
            changed_by=record.changed_by,
            changed_keys=frozenset(record.configuration),
            public_values=record.configuration,
        )

    async def get_public_values(self) -> Mapping[str, object] | None:
        """Return a detached copy of the latest public configuration values."""
        record = await self._latest_record()
        return dict(record.configuration) if record is not None else None

    async def list_history(self, *, limit: int) -> tuple[ConfigurationRevision, ...]:
        """Return a bounded newest-first public configuration history."""
        if not 1 <= limit <= 200:
            raise ValueError("Configuration history limit must be between 1 and 200")
        records = (
            await self._session.scalars(
                select(ConfigurationVersionORM)
                .order_by(ConfigurationVersionORM.version_number.desc())
                .limit(limit)
            )
        ).all()
        return tuple(
            ConfigurationRevision(
                revision=record.version_number,
                changed_at=record.changed_at,
                changed_by=record.changed_by,
                changed_keys=frozenset(record.configuration),
                public_values=record.configuration,
            )
            for record in records
        )

    async def _latest_record(self) -> ConfigurationVersionORM | None:
        statement = (
            select(ConfigurationVersionORM)
            .order_by(ConfigurationVersionORM.version_number.desc())
            .limit(1)
        )
        return (await self._session.execute(statement)).scalar_one_or_none()
