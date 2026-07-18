"""Task 18 background runner success, failure and ownership tests."""

from __future__ import annotations

from PySide6.QtCore import QThreadPool

from bluebubbles.client.ui.tasks import AsyncTask, BackgroundTaskRunner


class ImmediatePool(QThreadPool):
    """Execute QRunnables inline while retaining the production pool interface."""

    def start(  # type: ignore[no-untyped-def,override]
        self, runnable, priority: int = 0
    ) -> None:
        del priority
        runnable.run()


def test_async_task_emits_success_and_safe_failure() -> None:
    values: list[object] = []
    errors: list[str] = []

    async def succeed() -> object:
        return 42

    success_task = AsyncTask(succeed)
    success_task.signals.succeeded.connect(values.append)
    success_task.run()

    async def fail() -> object:
        raise RuntimeError()

    failure_task = AsyncTask(fail)
    failure_task.signals.failed.connect(errors.append)
    failure_task.run()
    assert values == [42]
    assert errors == ["The operation could not be completed."]


def test_background_runner_releases_success_and_failure_tasks() -> None:
    runner = BackgroundTaskRunner(ImmediatePool())
    values: list[object] = []
    errors: list[str] = []

    async def succeed() -> object:
        return "done"

    async def fail() -> object:
        raise RuntimeError("failed")

    runner.submit(succeed, values.append, errors.append)
    runner.submit(fail, values.append, errors.append)
    assert values == ["done"]
    assert errors == ["failed"]
