"""Lifecycle-owned protected asynchronous audit export generation."""

from __future__ import annotations

import asyncio
import csv
import json
import os
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.audit import AuditEvent, AuditSeverity
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission
from bluebubbles.server.services.audit import AuditWriter, sanitise_audit_details
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.shared.errors.exceptions import ConflictError, ResourceNotFoundError
from bluebubbles.shared.models.administration import DataExportJobResponse, JobState


class AuditExportService:
    """Queue, generate, authorise, and expire content-free audit exports."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        export_root: Path,
        audit_writer: AuditWriter | None = None,
        *,
        lifetime: timedelta = timedelta(hours=24),
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._uow_factory = unit_of_work_factory
        self._permissions = permission_service
        self._root = export_root.resolve()
        self._audit = audit_writer or AuditWriter()
        self._lifetime = lifetime
        self._clock = clock
        self._queue: asyncio.Queue[tuple[UUID, str]] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Create the protected export directory and start the owned worker."""
        await asyncio.to_thread(self._root.mkdir, parents=True, exist_ok=True)
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run(), name="audit_export")

    async def stop(self) -> None:
        """Cancel and await the owned worker without leaving an orphan task."""
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    async def create(
        self, requester: AuthenticatedUser, export_format: str
    ) -> DataExportJobResponse:
        """Commit one export request and audit event before queueing generation."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.AUDIT_EXPORT
        )
        export_format = export_format.casefold()
        if export_format not in {"csv", "json"}:
            raise ValueError("Audit export format must be csv or json")
        now = self._clock()
        job = DataExportJobResponse(id=uuid4(), state=JobState.QUEUED, requested_at=now)
        async with self._uow_factory() as uow:
            await uow.administration.add_export_job(
                job,
                requested_by=requester.user_id,
                export_type=f"audit_{export_format}",
                filters={},
                expires_at=now + self._lifetime,
            )
            await self._audit.append(
                uow.audit,
                event_type="audit.export_created",
                occurred_at=now,
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.WARNING,
                details={"export_job_id": str(job.id), "format": export_format},
            )
            await uow.commit()
        await self._queue.put((job.id, export_format))
        return job

    async def get(
        self, requester: AuthenticatedUser, job_id: UUID
    ) -> DataExportJobResponse:
        """Return one unexpired job only to its requesting administrator."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.AUDIT_EXPORT
        )
        job, owner, expires_at, reference = await self._load(job_id)
        if owner != requester.user_id:
            raise ResourceNotFoundError()
        if self._clock() >= expires_at:
            if reference is not None:
                await asyncio.to_thread(Path(reference).unlink, missing_ok=True)
            raise ConflictError(user_message="The export has expired.")
        return job

    async def download_path(self, requester: AuthenticatedUser, job_id: UUID) -> Path:
        """Authorise a completed export path and audit the download decision."""
        job = await self.get(requester, job_id)
        if job.state is not JobState.SUCCEEDED:
            raise ConflictError(user_message="The export is not ready.")
        _, _, _, reference = await self._load(job_id)
        if reference is None:
            raise ResourceNotFoundError()
        path = Path(reference).resolve()
        if not path.is_relative_to(self._root) or not path.is_file():
            raise ResourceNotFoundError()
        async with self._uow_factory() as uow:
            await self._audit.append(
                uow.audit,
                event_type="audit.export_downloaded",
                occurred_at=self._clock(),
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.INFORMATIONAL,
                details={"export_job_id": str(job_id)},
            )
            await uow.commit()
        return path

    async def _load(
        self, job_id: UUID
    ) -> tuple[DataExportJobResponse, UUID, datetime, str | None]:
        async with self._uow_factory() as uow:
            record = await uow.administration.get_export_job(job_id)
        if record is None:
            raise ResourceNotFoundError()
        return record

    async def _run(self) -> None:
        while True:
            job_id, export_format = await self._queue.get()
            try:
                await self._generate(job_id, export_format)
            finally:
                self._queue.task_done()

    async def _generate(self, job_id: UUID, export_format: str) -> None:
        path = self._root / f"{job_id}.{export_format}"
        temporary = self._root / f".{job_id}.{export_format}.tmp"
        failure_code: str | None = None
        try:
            async with self._uow_factory() as uow:
                state = await uow.audit.get_latest_chain_state()
                events = (
                    await uow.audit.list_range(1, state.event_count)
                    if state.event_count
                    else []
                )
            await asyncio.to_thread(
                self._write_export, temporary, path, events, export_format
            )
        except Exception:
            failure_code = "audit_export_failed"
            await asyncio.to_thread(temporary.unlink, missing_ok=True)
        async with self._uow_factory() as uow:
            await uow.administration.complete_export_job(
                job_id,
                completed_at=self._clock(),
                storage_reference=str(path) if failure_code is None else None,
                failure_code=failure_code,
            )
            await uow.commit()

    @staticmethod
    def _write_export(
        temporary: Path,
        path: Path,
        events: list[AuditEvent],
        export_format: str,
    ) -> None:
        records = [AuditExportService._record(event) for event in events]
        with temporary.open("x", encoding="utf-8", newline="") as stream:
            if export_format == "json":
                json.dump(records, stream, ensure_ascii=False, separators=(",", ":"))
            else:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=(
                        "sequence_number",
                        "event_id",
                        "event_type",
                        "occurred_at",
                        "actor_id",
                        "severity",
                        "details",
                        "entry_hash",
                    ),
                )
                writer.writeheader()
                writer.writerows(records)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        with suppress(OSError):
            path.chmod(0o600)

    @staticmethod
    def _record(event: AuditEvent) -> dict[str, object]:
        return {
            "sequence_number": event.sequence_number,
            "event_id": str(event.id),
            "event_type": AuditExportService._csv_safe(event.event_type),
            "occurred_at": event.occurred_at.isoformat(),
            "actor_id": str(event.actor_id) if event.actor_id else None,
            "severity": event.severity.value,
            "details": json.dumps(
                sanitise_audit_details(event.details),
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            "entry_hash": event.event_hash,
        }

    @staticmethod
    def _csv_safe(value: str) -> str:
        return f"'{value}" if value.startswith(("=", "+", "-", "@")) else value
