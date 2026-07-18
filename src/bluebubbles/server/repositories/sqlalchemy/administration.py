"""Async SQLAlchemy administrative job repository."""

from collections.abc import Mapping
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.administration import (
    DataExportJobORM,
    WorkerExecutionRecordORM,
)
from bluebubbles.server.repositories.sqlalchemy._common import (
    flush_changes,
    require_aware,
)
from bluebubbles.shared.models.administration import DataExportJobResponse, JobState


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

    async def add_export_job(
        self,
        job: DataExportJobResponse,
        *,
        requested_by: UUID,
        export_type: str,
        filters: Mapping[str, object],
        expires_at: datetime,
    ) -> None:
        """Stage one protected audit-export job."""
        require_aware(job.requested_at, "requested_at")
        require_aware(expires_at, "expires_at")
        self._session.add(
            DataExportJobORM(
                id=job.id,
                requested_by=requested_by,
                export_type=export_type,
                filters=dict(filters),
                status=job.state.value,
                storage_reference=None,
                created_at=job.requested_at,
                started_at=None,
                completed_at=None,
                expires_at=expires_at,
                failure_code=None,
            )
        )
        await flush_changes(self._session)

    async def get_export_job(
        self, job_id: UUID
    ) -> tuple[DataExportJobResponse, UUID, datetime, str | None] | None:
        """Return safe job state plus ownership and protected internal reference."""
        record = await self._session.scalar(
            select(DataExportJobORM).where(DataExportJobORM.id == job_id)
        )
        if record is None or record.expires_at is None:
            return None
        state = JobState(record.status)
        return (
            DataExportJobResponse(
                id=record.id,
                state=state,
                requested_at=record.created_at,
                completed_at=record.completed_at,
                progress_percent=100 if state is JobState.SUCCEEDED else 0,
                download_url=(
                    f"/api/v1/admin/exports/{record.id}/download"
                    if state is JobState.SUCCEEDED
                    else None
                ),
            ),
            record.requested_by,
            record.expires_at,
            record.storage_reference,
        )

    async def complete_export_job(
        self,
        job_id: UUID,
        *,
        completed_at: datetime,
        storage_reference: str | None,
        failure_code: str | None,
    ) -> bool:
        """Finish one queued/running export with a safe result code."""
        require_aware(completed_at, "completed_at")
        result = await self._session.execute(
            update(DataExportJobORM)
            .where(
                DataExportJobORM.id == job_id,
                DataExportJobORM.completed_at.is_(None),
            )
            .values(
                status="failed" if failure_code else "succeeded",
                completed_at=completed_at,
                storage_reference=storage_reference,
                failure_code=failure_code,
            )
        )
        return result.rowcount == 1
