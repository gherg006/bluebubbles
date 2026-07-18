"""Administrative job repository protocol."""

from collections.abc import Mapping
from datetime import datetime
from typing import Protocol
from uuid import UUID

from bluebubbles.shared.models.administration import DataExportJobResponse


class AdministrationRepository(Protocol):
    """Define bounded administrative job persistence operations."""

    async def add_worker_execution(
        self,
        *,
        record_id: UUID,
        worker_name: str,
        started_at: datetime,
        status: str,
        details: Mapping[str, object],
    ) -> None: ...

    async def complete_worker_execution(
        self,
        record_id: UUID,
        *,
        completed_at: datetime,
        status: str,
        processed_count: int,
        failure_count: int,
        error_code: str | None = None,
    ) -> bool: ...

    async def add_export_job(
        self,
        job: DataExportJobResponse,
        *,
        requested_by: UUID,
        export_type: str,
        filters: Mapping[str, object],
        expires_at: datetime,
    ) -> None: ...

    async def get_export_job(
        self, job_id: UUID
    ) -> tuple[DataExportJobResponse, UUID, datetime, str | None] | None: ...

    async def complete_export_job(
        self,
        job_id: UUID,
        *,
        completed_at: datetime,
        storage_reference: str | None,
        failure_code: str | None,
    ) -> bool: ...
