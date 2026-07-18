"""Lifecycle-owned durable outbox publication worker."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4

from bluebubbles.server.configuration.settings import WorkerSettings
from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.websocket.publisher import EventPublisher


class WorkerState(StrEnum):
    STOPPED = "stopped"
    RUNNING = "running"
    IDLE = "idle"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class WorkerRunResult:
    claimed: int
    published: int
    failed: int


@dataclass(frozen=True, slots=True)
class WorkerStatus:
    name: str
    state: WorkerState
    last_started_at: datetime | None
    last_completed_at: datetime | None
    failure_count: int


class OutboxPublisherWorker:
    """Claim bounded batches and publish each poison-isolated event."""

    name = "outbox_publisher"
    manually_runnable = True
    pausable = False

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        event_publisher: EventPublisher,
        settings: WorkerSettings,
        logger: logging.Logger,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._event_publisher = event_publisher
        self._settings = settings
        self._logger = logger
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._run_lock = asyncio.Lock()
        self._last_started_at: datetime | None = None
        self._last_completed_at: datetime | None = None
        self._failure_count = 0
        self._state = WorkerState.STOPPED

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stop_event.clear()
        self._state = WorkerState.IDLE
        self._task = asyncio.create_task(self._run_loop(), name=self.name)

    async def stop(self) -> None:
        self._stop_event.set()
        task = self._task
        self._task = None
        if task is not None:
            await task
        self._state = WorkerState.STOPPED

    async def run_now(self) -> WorkerRunResult:
        return await self.run_once()

    def pause(self) -> None:
        """Reject pausing the critical durable-delivery worker."""
        raise ValueError("Critical worker cannot be paused")

    def resume(self) -> None:
        """Retain the always-enabled critical worker state."""

    def status(self) -> WorkerStatus:
        return WorkerStatus(
            self.name,
            self._state,
            self._last_started_at,
            self._last_completed_at,
            self._failure_count,
        )

    async def run_once(self) -> WorkerRunResult:
        async with self._run_lock:
            self._state = WorkerState.RUNNING
            self._last_started_at = datetime.now(UTC)
            now = self._last_started_at
            async with self._unit_of_work_factory() as uow:
                await uow.outbox.release_expired_locks(
                    now - timedelta(seconds=self._settings.outbox_lock_timeout_seconds)
                )
                events = await uow.outbox.claim_batch(
                    str(uuid4()), self._settings.outbox_batch_size, now
                )
                await uow.commit()
            published = failed = 0
            for event in events:
                try:
                    await self._event_publisher.publish(event)
                    async with self._unit_of_work_factory() as uow:
                        await uow.outbox.mark_published(event.id, datetime.now(UTC))
                        await uow.commit()
                    published += 1
                except Exception as error:
                    failed += 1
                    self._failure_count += 1
                    delay = min(
                        self._settings.outbox_retry_maximum_seconds,
                        self._settings.outbox_retry_base_seconds * 2**event.attempts,
                    )
                    async with self._unit_of_work_factory() as uow:
                        await uow.outbox.mark_failed(
                            event.id,
                            "publication_failed",
                            datetime.now(UTC) + timedelta(seconds=delay),
                        )
                        await uow.commit()
                    self._logger.warning(
                        "Outbox publication failed",
                        extra={
                            "event_id": str(event.id),
                            "failure_category": type(error).__name__,
                            "attempt": event.attempts + 1,
                        },
                    )
            self._last_completed_at = datetime.now(UTC)
            self._state = WorkerState.FAILED if failed else WorkerState.IDLE
            return WorkerRunResult(len(events), published, failed)

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.run_once()
            except Exception as error:
                self._failure_count += 1
                self._state = WorkerState.FAILED
                self._logger.error(
                    "Outbox worker run failed",
                    extra={"failure_category": type(error).__name__},
                )
            with suppress(TimeoutError):
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self._settings.outbox_interval_seconds,
                )
