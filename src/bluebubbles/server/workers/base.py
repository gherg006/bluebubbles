"""Cancellation-safe recurring background-worker foundation."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class ManagedWorkerState(StrEnum):
    """Represent the lifecycle state of a managed recurring worker."""

    STOPPED = "stopped"
    IDLE = "idle"
    RUNNING = "running"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass(frozen=True, slots=True)
class ManagedWorkerStatus:
    """Return safe worker state and failure metadata."""

    name: str
    state: ManagedWorkerState
    last_started_at: datetime | None = None
    last_completed_at: datetime | None = None
    failure_count: int = 0
    last_error_code: str | None = None


class BackgroundWorker:
    """Own one bounded recurring callback and cooperative stop/pause state."""

    def __init__(
        self,
        name: str,
        interval_seconds: float,
        operation: Callable[[], Awaitable[int]],
        *,
        manually_runnable: bool = True,
        pausable: bool = True,
    ) -> None:
        if not name.strip() or interval_seconds <= 0:
            raise ValueError("Worker name and positive interval are required")
        self.name = name
        self.manually_runnable = manually_runnable
        self.pausable = pausable
        self._interval = interval_seconds
        self._operation = operation
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()
        self._run_lock = asyncio.Lock()
        self._paused = False
        self._state = ManagedWorkerState.STOPPED
        self._last_started_at: datetime | None = None
        self._last_completed_at: datetime | None = None
        self._failure_count = 0
        self._last_error_code: str | None = None

    async def start(self) -> None:
        """Start the owned loop once."""
        if self._task is not None and not self._task.done():
            return
        self._stop.clear()
        self._state = (
            ManagedWorkerState.PAUSED if self._paused else ManagedWorkerState.IDLE
        )
        self._task = asyncio.create_task(self._loop(), name=self.name)

    async def stop(self) -> None:
        """Request stop and await the owned task without leaking it."""
        self._stop.set()
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        self._state = ManagedWorkerState.STOPPED

    async def run_now(self) -> int:
        """Execute one serialised batch and retain only a safe failure code."""
        async with self._run_lock:
            self._state = ManagedWorkerState.RUNNING
            self._last_started_at = datetime.now(UTC)
            try:
                processed = await self._operation()
            except Exception:
                self._failure_count += 1
                self._last_error_code = "worker_run_failed"
                self._state = ManagedWorkerState.FAILED
                raise
            self._last_completed_at = datetime.now(UTC)
            self._last_error_code = None
            self._state = (
                ManagedWorkerState.PAUSED if self._paused else ManagedWorkerState.IDLE
            )
            return processed

    def pause(self) -> None:
        """Pause future scheduled runs for an optional worker."""
        if not self.pausable:
            raise ValueError("Critical worker cannot be paused")
        self._paused = True
        if self._state is not ManagedWorkerState.RUNNING:
            self._state = ManagedWorkerState.PAUSED

    def resume(self) -> None:
        """Resume future scheduled runs."""
        self._paused = False
        if self._state is ManagedWorkerState.PAUSED:
            self._state = ManagedWorkerState.IDLE

    def status(self) -> ManagedWorkerStatus:
        """Return immutable worker state for monitoring and administration."""
        return ManagedWorkerStatus(
            name=self.name,
            state=self._state,
            last_started_at=self._last_started_at,
            last_completed_at=self._last_completed_at,
            failure_count=self._failure_count,
            last_error_code=self._last_error_code,
        )

    async def _loop(self) -> None:
        while not self._stop.is_set():
            if not self._paused:
                with suppress(Exception):
                    await self.run_now()
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self._interval)
            except TimeoutError:
                continue
