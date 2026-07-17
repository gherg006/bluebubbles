"""Administrative job repository protocol."""

from collections.abc import Mapping
from datetime import datetime
from typing import Protocol
from uuid import UUID


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
