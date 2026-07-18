"""Run asynchronous service work outside the Qt GUI thread."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, Protocol

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class TaskSignals(QObject):
    """Marshal background results back to the owning Qt thread."""

    succeeded = Signal(object)
    failed = Signal(str)


class TaskRunner(Protocol):
    """Schedule one coroutine and marshal its result to callbacks."""

    def submit(
        self,
        operation: Callable[[], Coroutine[Any, Any, object]],
        success: Callable[[object], None],
        failure: Callable[[str], None],
    ) -> None: ...


class AsyncTask(QRunnable):
    """Execute one coroutine in a worker-owned event loop."""

    def __init__(self, operation: Callable[[], Coroutine[Any, Any, object]]) -> None:
        super().__init__()
        self._operation = operation
        self.signals = TaskSignals()

    def run(self) -> None:
        """Run the coroutine and emit only a safe user-facing failure string."""
        try:
            result: object = asyncio.run(self._operation())
        except Exception as error:
            self.signals.failed.emit(
                str(error) or "The operation could not be completed."
            )
        else:
            self.signals.succeeded.emit(result)


class BackgroundTaskRunner:
    """Own active Qt worker references until their completion signals arrive."""

    def __init__(self, pool: QThreadPool | None = None) -> None:
        self._pool = pool or QThreadPool.globalInstance()
        self._active: set[AsyncTask] = set()

    def submit(
        self,
        operation: Callable[[], Coroutine[Any, Any, object]],
        success: Callable[[object], None],
        failure: Callable[[str], None],
    ) -> None:
        """Schedule work and release task ownership after either result."""
        task = AsyncTask(operation)
        self._active.add(task)

        def succeeded(value: object) -> None:
            self._active.discard(task)
            success(value)

        def failed(message: str) -> None:
            self._active.discard(task)
            failure(message)

        task.signals.succeeded.connect(succeeded)
        task.signals.failed.connect(failed)
        self._pool.start(task)
