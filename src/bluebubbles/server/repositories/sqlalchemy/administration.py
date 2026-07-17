"""Async SQLAlchemy administrative job repository."""

from collections.abc import Mapping
from datetime import datetime
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.administration import WorkerExecutionRecordORM
from bluebubbles.server.repositories.sqlalchemy._common import (
    flush_changes,
    require_aware,
)


class SqlAlchemyAdministrationRepository:
    """Persist bounded worker execution summaries without sensitive values."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_worker_execution(
        self,
        *,
        record_id: UUID,
        worker_name: str,
        started_at: datetime,
        status: str,
        details: Mapping[str, object],
    ) -> None:
        """Stage one safe worker execution start record."""
        require_aware(started_at, "started_at")
        if not worker_name.strip() or not status.strip():
            raise ValueError("Worker name and status are required")
        self._session.add(
            WorkerExecutionRecordORM(
                id=record_id,
                worker_name=worker_name.strip(),
                started_at=started_at,
                completed_at=None,
                status=status.strip(),
                processed_count=0,
                failure_count=0,
                error_code=None,
                details=dict(details),
            )
        )
        await flush_changes(self._session)

    async def complete_worker_execution(
        self,
        record_id: UUID,
        *,
        completed_at: datetime,
        status: str,
        processed_count: int,
        failure_count: int,
        error_code: str | None = None,
    ) -> bool:
        """Complete one worker record with bounded counters and a safe code."""
        require_aware(completed_at, "completed_at")
        if processed_count < 0 or failure_count < 0 or not status.strip():
            raise ValueError("Valid status and non-negative counters are required")
        result = await self._session.execute(
            update(WorkerExecutionRecordORM)
            .where(
                WorkerExecutionRecordORM.id == record_id,
                WorkerExecutionRecordORM.completed_at.is_(None),
            )
            .values(
                completed_at=completed_at,
                status=status.strip(),
                processed_count=processed_count,
                failure_count=failure_count,
                error_code=error_code,
            )
        )
        return result.rowcount == 1
