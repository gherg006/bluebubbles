"""Task 17 ordered queue, retry, dependency and persistence evidence."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from bluebubbles.client.domain.offline_actions import (
    OfflineAction,
    OfflineActionExecutionResult,
    OfflineActionOutcome,
    OfflineActionState,
    OfflineActionType,
    PendingOfflineAction,
)
from bluebubbles.client.domain.synchronisation import SynchronisationScope
from bluebubbles.client.repositories.sqlite.offline_actions import (
    SQLiteOfflineActionRepository,
)
from bluebubbles.client.security.local_encryption import LocalEncryptionService
from bluebubbles.client.services.offline_queue import (
    AllowingReplayValidator,
    OfflineActionExecutor,
    OfflineQueueService,
)
from bluebubbles.client.storage.database import LocalDatabaseManager
from bluebubbles.client.storage.migrations import ClientMigrationManager
from bluebubbles.shared.errors.exceptions import LocalStorageError


class MemoryActionRepository:
    """Implement the queue repository contract deterministically for unit tests."""

    def __init__(self) -> None:
        self.items: dict[UUID, OfflineAction] = {}

    async def save(self, action: OfflineAction) -> None:
        self.items[action.id] = action

    async def get(self, action_id: UUID) -> OfflineAction | None:
        return self.items.get(action_id)

    async def list_pending(self) -> list[OfflineAction]:
        terminal = {
            OfflineActionState.COMPLETED,
            OfflineActionState.FAILED_PERMANENT,
            OfflineActionState.CANCELLED,
        }
        return [
            action
            for action in sorted(
                self.items.values(), key=lambda item: item.sequence_number
            )
            if action.state not in terminal
        ]

    async def list_by_states(
        self, states: frozenset[OfflineActionState]
    ) -> list[OfflineAction]:
        return [
            action
            for action in sorted(
                self.items.values(), key=lambda item: item.sequence_number
            )
            if action.state in states
        ]

    async def next_sequence_number(self) -> int:
        latest = max((item.sequence_number for item in self.items.values()), default=0)
        return latest + 1

    async def delete(self, action_id: UUID) -> None:
        self.items.pop(action_id, None)


class FixedKeyProvider:
    """Return one deterministic local master key."""

    def __init__(self, key: bytes) -> None:
        self.key = key

    async def get_master_key(self) -> bytes:
        return self.key


def pending(
    user_id: UUID,
    action_id: UUID,
    *,
    dependency: UUID | None = None,
) -> PendingOfflineAction:
    """Build one safe synthetic message action."""
    return PendingOfflineAction(
        user_id,
        OfflineActionType.SEND_MESSAGE,
        action_id,
        f"payload-{action_id}".encode(),
        scope_type="conversation_membership",
        scope_id=uuid4(),
        dependency_action_id=dependency,
        action_id=action_id,
    )


@pytest.mark.asyncio
async def test_actions_process_in_sequence_and_dependencies_unblock() -> None:
    repository = MemoryActionRepository()
    calls: list[UUID] = []

    async def execute(
        action: OfflineAction, payload: bytes
    ) -> OfflineActionExecutionResult:
        assert payload.startswith(b"payload-")
        calls.append(action.id)
        return OfflineActionExecutionResult(OfflineActionOutcome.SUCCEEDED)

    queue = OfflineQueueService(
        repository,
        OfflineActionExecutor(
            {OfflineActionType.SEND_MESSAGE: execute}, AllowingReplayValidator()
        ),
        jitter=lambda _low, _high: 1.0,
    )
    user_id, first_id, second_id = uuid4(), uuid4(), uuid4()
    first = await queue.enqueue(pending(user_id, first_id))
    second = await queue.enqueue(pending(user_id, second_id, dependency=first_id))

    result = await queue.process_pending()

    assert first.sequence_number < second.sequence_number
    assert calls == [first_id, second_id]
    assert result.completed == 2
    assert repository.items[second_id].state is OfflineActionState.COMPLETED


@pytest.mark.asyncio
async def test_retry_permanent_failure_cancel_and_manual_retry() -> None:
    repository = MemoryActionRepository()
    outcomes = [
        OfflineActionExecutionResult(
            OfflineActionOutcome.RETRYABLE_FAILURE, failure_code="server_unavailable"
        ),
        OfflineActionExecutionResult(
            OfflineActionOutcome.PERMANENT_FAILURE,
            failure_code="membership_removed",
            user_action_required=True,
        ),
    ]

    async def execute(
        action: OfflineAction, payload: bytes
    ) -> OfflineActionExecutionResult:
        del action, payload
        return outcomes.pop(0)

    now = datetime.now(UTC)
    queue = OfflineQueueService(
        repository,
        OfflineActionExecutor(
            {OfflineActionType.SEND_MESSAGE: execute}, AllowingReplayValidator()
        ),
        clock=lambda: now,
        jitter=lambda _low, _high: 1.0,
    )
    user_id, retry_id, cancelled_id = uuid4(), uuid4(), uuid4()
    await queue.enqueue(pending(user_id, retry_id))
    await queue.enqueue(pending(user_id, cancelled_id))
    await queue.cancel(cancelled_id)

    first = await queue.process_pending()
    assert first.retrying == 1
    assert repository.items[retry_id].state is OfflineActionState.RETRY_WAIT
    assert repository.items[cancelled_id].state is OfflineActionState.CANCELLED

    await queue.retry_now(retry_id)
    second = await queue.process_pending()
    assert second.permanently_failed == 1
    assert repository.items[retry_id].state is OfflineActionState.FAILED_PERMANENT


@pytest.mark.asyncio
async def test_single_processor_and_interrupted_processing_recovery() -> None:
    repository = MemoryActionRepository()
    started, release = asyncio.Event(), asyncio.Event()

    async def execute(
        action: OfflineAction, payload: bytes
    ) -> OfflineActionExecutionResult:
        del action, payload
        started.set()
        await release.wait()
        return OfflineActionExecutionResult(OfflineActionOutcome.SUCCEEDED)

    queue = OfflineQueueService(
        repository,
        OfflineActionExecutor(
            {OfflineActionType.SEND_MESSAGE: execute}, AllowingReplayValidator()
        ),
    )
    await queue.enqueue(pending(uuid4(), uuid4()))
    processing = asyncio.create_task(queue.process_pending())
    await started.wait()
    duplicate = await queue.process_pending()
    release.set()
    completed = await processing

    assert duplicate.already_running
    assert completed.completed == 1


@pytest.mark.asyncio
async def test_sqlite_payload_is_protected_and_wrong_key_fails(tmp_path: Path) -> None:
    path = tmp_path / "client_cache.db"
    database = LocalDatabaseManager(path, ClientMigrationManager(path, tmp_path / "r"))
    provider = FixedKeyProvider(b"q" * 32)
    await database.open(await provider.get_master_key())
    profile_id = uuid4()
    repository = SQLiteOfflineActionRepository(
        database, LocalEncryptionService(provider), profile_id
    )
    marker = b"TASK17-SECRET-OFFLINE-PAYLOAD"
    action = OfflineAction(
        uuid4(),
        OfflineActionType.SEND_MESSAGE.value,
        "stable-key",
        marker,
        datetime.now(UTC),
        sequence_number=1,
        user_id=profile_id,
        state=OfflineActionState.READY,
    )
    await repository.save(action)
    assert await repository.get(action.id) == action
    await database.close()
    assert marker not in path.read_bytes()

    wrong_provider = FixedKeyProvider(b"w" * 32)
    wrong = LocalDatabaseManager(path, ClientMigrationManager(path, tmp_path / "r"))
    with pytest.raises(LocalStorageError):
        await wrong.open(await wrong_provider.get_master_key())


def test_state_machine_rejects_terminal_replay() -> None:
    action = OfflineAction(
        uuid4(), "send_message", uuid4(), b"payload", datetime.now(UTC)
    )
    complete = (
        action.transition(OfflineActionState.READY)
        .transition(OfflineActionState.PROCESSING)
        .transition(OfflineActionState.COMPLETED)
    )
    with pytest.raises(ValueError, match="transition"):
        complete.transition(OfflineActionState.READY)


@pytest.mark.asyncio
async def test_future_retry_is_not_executed_early() -> None:
    repository = MemoryActionRepository()
    calls = 0

    async def execute(
        action: OfflineAction, payload: bytes
    ) -> OfflineActionExecutionResult:
        nonlocal calls
        del action, payload
        calls += 1
        return OfflineActionExecutionResult(OfflineActionOutcome.SUCCEEDED)

    now = datetime.now(UTC)
    action_id = uuid4()
    repository.items[action_id] = OfflineAction(
        action_id,
        "send_message",
        action_id,
        b"payload",
        now,
        now + timedelta(minutes=1),
        OfflineActionState.RETRY_WAIT,
        sequence_number=1,
    )
    queue = OfflineQueueService(
        repository,
        OfflineActionExecutor(
            {OfflineActionType.SEND_MESSAGE: execute}, AllowingReplayValidator()
        ),
        clock=lambda: now,
    )
    assert (await queue.process_pending()).processed == 0
    assert calls == 0


@pytest.mark.asyncio
async def test_executor_rejects_unknown_missing_and_preflight_blocked_actions() -> None:
    action = OfflineAction(uuid4(), "unknown", uuid4(), b"payload", datetime.now(UTC))
    executor = OfflineActionExecutor({}, AllowingReplayValidator())
    unknown = await executor.execute(action, action.encrypted_payload)
    assert unknown.outcome is OfflineActionOutcome.PERMANENT_FAILURE

    missing = await executor.execute(
        OfflineAction(uuid4(), "send_message", uuid4(), b"payload", datetime.now(UTC)),
        b"payload",
    )
    assert missing.failure_code == "offline_action_handler_unavailable"

    class BlockingValidator:
        async def validate(
            self, selected: OfflineAction
        ) -> OfflineActionExecutionResult | None:
            del selected
            return OfflineActionExecutionResult(
                OfflineActionOutcome.BLOCKED, failure_code="membership_stale"
            )

    async def unused_handler(
        selected: OfflineAction, payload: bytes
    ) -> OfflineActionExecutionResult:
        del selected, payload
        raise AssertionError("blocked actions must not reach their handler")

    blocked_executor = OfflineActionExecutor(
        {OfflineActionType.SEND_MESSAGE: unused_handler},
        BlockingValidator(),
    )
    blocked = await blocked_executor.execute(
        OfflineAction(uuid4(), "send_message", uuid4(), b"payload", datetime.now(UTC)),
        b"payload",
    )
    assert blocked.outcome is OfflineActionOutcome.BLOCKED


@pytest.mark.asyncio
async def test_queue_validation_dependency_unblock_and_visible_summary() -> None:
    repository = MemoryActionRepository()

    async def succeed(
        action: OfflineAction, payload: bytes
    ) -> OfflineActionExecutionResult:
        del action, payload
        return OfflineActionExecutionResult(OfflineActionOutcome.SUCCEEDED)

    queue = OfflineQueueService(
        repository,
        OfflineActionExecutor(
            {OfflineActionType.SEND_MESSAGE: succeed}, AllowingReplayValidator()
        ),
    )
    user_id = uuid4()
    with pytest.raises(ValueError, match="empty"):
        await queue.enqueue(
            PendingOfflineAction(user_id, OfflineActionType.SEND_MESSAGE, uuid4(), b"")
        )
    action_id = uuid4()
    with pytest.raises(ValueError, match="itself"):
        await queue.enqueue(pending(user_id, action_id, dependency=action_id))

    blocked_id = uuid4()
    await queue.enqueue(pending(user_id, blocked_id, dependency=uuid4()))
    result = await queue.process_pending()
    assert result.blocked == 1
    summaries = await queue.list_visible()
    assert summaries[0].failure_code == "offline_dependency_incomplete"
    assert (
        await queue.unblock_after_sync(SynchronisationScope.CONVERSATION_MEMBERSHIP)
        == 1
    )
    await queue.cancel(blocked_id)
    with pytest.raises(ValueError, match="cancelled"):
        await queue.cancel(blocked_id)
    with pytest.raises(ValueError, match="retried"):
        await queue.retry_now(blocked_id)
    with pytest.raises(KeyError):
        await queue.cancel(uuid4())


@pytest.mark.asyncio
async def test_dependency_cycle_and_executor_exception_become_retry() -> None:
    repository = MemoryActionRepository()
    first_id, second_id = uuid4(), uuid4()
    repository.items[first_id] = OfflineAction(
        first_id,
        "send_message",
        first_id,
        b"payload",
        datetime.now(UTC),
        state=OfflineActionState.BLOCKED,
        sequence_number=1,
        dependency_action_id=second_id,
    )

    async def crash(
        action: OfflineAction, payload: bytes
    ) -> OfflineActionExecutionResult:
        del action, payload
        raise RuntimeError("synthetic")

    queue = OfflineQueueService(
        repository,
        OfflineActionExecutor(
            {OfflineActionType.SEND_MESSAGE: crash}, AllowingReplayValidator()
        ),
        jitter=lambda _low, _high: 1.0,
    )
    with pytest.raises(ValueError, match="cycle"):
        await queue.enqueue(pending(uuid4(), second_id, dependency=first_id))

    independent = await queue.enqueue(pending(uuid4(), uuid4()))
    result = await queue.process_pending()
    assert result.retrying == 1
    assert (
        repository.items[independent.id].last_error_code == "offline_executor_failure"
    )
