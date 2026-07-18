"""Lifecycle ownership and authorised control of registered background workers."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.audit import AuditSeverity
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission
from bluebubbles.server.services.audit import AuditWriter
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.server.workers.base import ManagedWorkerState
from bluebubbles.shared.errors.exceptions import (
    AuthorisationError,
    ConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from bluebubbles.shared.models.administration import (
    JobState,
    WorkerListResponse,
    WorkerStatusResponse,
)


class ManagedWorker(Protocol):
    """Define the small lifecycle and control surface used by the manager."""

    name: str
    manually_runnable: bool
    pausable: bool

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def run_now(self) -> object: ...
    def pause(self) -> None: ...
    def resume(self) -> None: ...
    def status(self) -> object: ...


class WorkerManager:
    """Start, stop, observe, and safely run a fixed worker registry."""

    def __init__(
        self,
        workers: Sequence[ManagedWorker],
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        audit_writer: AuditWriter | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        registry = {worker.name: worker for worker in workers}
        if len(registry) != len(workers):
            raise ValueError("Worker names must be unique")
        self._workers = registry
        self._uow_factory = unit_of_work_factory
        self._permissions = permission_service
        self._audit = audit_writer or AuditWriter()
        self._clock = clock
        self._manual_running: set[str] = set()
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start every worker in stable registration order."""
        started: list[ManagedWorker] = []
        try:
            for worker in self._workers.values():
                await worker.start()
                started.append(worker)
        except BaseException:
            for worker in reversed(started):
                await worker.stop()
            raise

    async def stop(self) -> None:
        """Stop every worker in reverse order and continue after failures."""
        for worker in reversed(tuple(self._workers.values())):
            try:
                await worker.stop()
            except Exception:  # noqa: S112 - cleanup must attempt every worker
                continue

    async def list_workers(self, requester: AuthenticatedUser) -> WorkerListResponse:
        """Return safe state for every registered worker."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.WORKER_VIEW
        )
        return WorkerListResponse(
            workers=tuple(self._response(worker) for worker in self._workers.values()),
            generated_at=self._clock(),
        )

    def health_statuses(self) -> tuple[object, ...]:
        """Return internal status snapshots without requiring an administrator."""
        return tuple(worker.status() for worker in self._workers.values())

    async def run_worker_now(
        self, requester: AuthenticatedUser, worker_name: str, reason: str
    ) -> WorkerStatusResponse:
        """Reject duplicate/disallowed manual runs and audit the durable request."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.WORKER_RUN
        )
        reason = reason.strip()
        if not reason or len(reason) > 1000:
            raise ValidationError(
                user_message="A manual worker-run reason is required."
            )
        worker = self._workers.get(worker_name)
        if worker is None:
            raise ResourceNotFoundError()
        if not worker.manually_runnable:
            raise AuthorisationError(user_message="This worker cannot be run manually.")
        async with self._lock:
            if worker_name in self._manual_running:
                raise ConflictError(user_message="This worker is already running.")
            self._manual_running.add(worker_name)
        record_id = uuid4()
        now = self._clock()
        try:
            async with self._uow_factory() as uow:
                await uow.administration.add_worker_execution(
                    record_id=record_id,
                    worker_name=worker_name,
                    started_at=now,
                    status="running",
                    details={"manual": True},
                )
                await self._audit.append(
                    uow.audit,
                    event_type="worker.manual_run_requested",
                    occurred_at=now,
                    actor_id=requester.user_id,
                    source_ip=None,
                    severity=AuditSeverity.WARNING,
                    details={"worker_name": worker_name, "reason": reason},
                )
                await uow.commit()
            failed = False
            try:
                await worker.run_now()
            except Exception:
                failed = True
            async with self._uow_factory() as uow:
                await uow.administration.complete_worker_execution(
                    record_id,
                    completed_at=self._clock(),
                    status="failed" if failed else "succeeded",
                    processed_count=0,
                    failure_count=1 if failed else 0,
                    error_code="worker_run_failed" if failed else None,
                )
                await uow.commit()
        finally:
            async with self._lock:
                self._manual_running.discard(worker_name)
        return self._response(worker)

    async def pause_worker(
        self, requester: AuthenticatedUser, worker_name: str
    ) -> WorkerStatusResponse:
        """Pause an optional worker after server-side permission and policy checks."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.WORKER_CONTROL
        )
        worker = self._workers.get(worker_name)
        if worker is None:
            raise ResourceNotFoundError()
        worker.pause()
        return self._response(worker)

    async def resume_worker(
        self, requester: AuthenticatedUser, worker_name: str
    ) -> WorkerStatusResponse:
        """Resume a previously paused optional worker."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.WORKER_CONTROL
        )
        worker = self._workers.get(worker_name)
        if worker is None:
            raise ResourceNotFoundError()
        worker.resume()
        return self._response(worker)

    @staticmethod
    def _response(worker: ManagedWorker) -> WorkerStatusResponse:
        status = worker.status()
        state_value = getattr(status, "state", "idle")
        state_text = getattr(state_value, "value", str(state_value))
        state = {
            "running": JobState.RUNNING,
            "failed": JobState.FAILED,
            "stopped": JobState.CANCELLED,
        }.get(state_text, JobState.SUCCEEDED)
        return WorkerStatusResponse(
            name=worker.name,
            state=state,
            last_started_at=getattr(status, "last_started_at", None),
            last_completed_at=getattr(status, "last_completed_at", None),
            last_error_code=getattr(status, "last_error_code", None),
            manually_runnable=worker.manually_runnable,
            pausable=worker.pausable,
            paused=state_text == ManagedWorkerState.PAUSED.value,
        )
