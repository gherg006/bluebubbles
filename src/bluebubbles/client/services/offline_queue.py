"""Serial, dependency-aware and idempotent offline action replay."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4

from bluebubbles.client.domain.offline_actions import (
    OfflineAction,
    OfflineActionExecutionResult,
    OfflineActionOutcome,
    OfflineActionState,
    OfflineActionSummary,
    OfflineActionType,
    PendingOfflineAction,
    QueueProcessingResult,
)
from bluebubbles.client.domain.synchronisation import SynchronisationScope
from bluebubbles.client.repositories.interfaces import OfflineActionRepository

ActionHandler = Callable[
    [OfflineAction, bytes], Awaitable[OfflineActionExecutionResult]
]


class OfflineReplayValidator(Protocol):
    """Refresh authoritative security state before one protected replay."""

    async def validate(
        self, action: OfflineAction
    ) -> OfflineActionExecutionResult | None: ...


class AllowingReplayValidator:
    """Allow replay when a caller has already completed the required security sync."""

    async def validate(
        self, action: OfflineAction
    ) -> OfflineActionExecutionResult | None:
        """Return no failure after the enclosing sync gate has succeeded."""
        del action
        return None


class OfflineActionExecutor:
    """Dispatch validated action types through explicitly injected handlers."""

    def __init__(
        self,
        handlers: Mapping[OfflineActionType, ActionHandler],
        validator: OfflineReplayValidator,
    ) -> None:
        self._handlers = dict(handlers)
        self._validator = validator

    async def execute(
        self, action: OfflineAction, payload: bytes
    ) -> OfflineActionExecutionResult:
        """Validate server authority and dispatch without dynamic imports."""
        try:
            action_type = OfflineActionType(action.action_type)
        except ValueError:
            return OfflineActionExecutionResult(
                OfflineActionOutcome.PERMANENT_FAILURE,
                failure_code="unsupported_offline_action",
                user_action_required=True,
            )
        preflight = await self._validator.validate(action)
        if preflight is not None:
            return preflight
        handler = self._handlers.get(action_type)
        if handler is None:
            return OfflineActionExecutionResult(
                OfflineActionOutcome.PERMANENT_FAILURE,
                failure_code="offline_action_handler_unavailable",
                user_action_required=True,
            )
        return await handler(action, payload)


class OfflineQueueService:
    """Own queue creation, crash recovery, dependencies, retries and cancellation."""

    _BACKOFF_SECONDS = (1, 2, 5, 10, 30, 60, 300)

    def __init__(
        self,
        repository: OfflineActionRepository,
        executor: OfflineActionExecutor,
        *,
        clock: Callable[[], datetime] | None = None,
        jitter: Callable[[float, float], float] | None = None,
    ) -> None:
        self._repository = repository
        self._executor = executor
        self._clock = clock or (lambda: datetime.now(UTC))
        self._jitter = jitter or random.SystemRandom().uniform
        self._processing_lock = asyncio.Lock()
        self._enqueue_lock = asyncio.Lock()

    async def enqueue(self, action: PendingOfflineAction) -> OfflineAction:
        """Assign stable action identity and monotonic profile-local ordering."""
        if not action.encrypted_payload:
            raise ValueError("Offline action payload cannot be empty")
        async with self._enqueue_lock:
            action_id = action.action_id or uuid4()
            if action.dependency_action_id == action_id:
                raise ValueError("Offline action cannot depend on itself")
            await self._reject_dependency_cycle(action_id, action.dependency_action_id)
            created = self._clock()
            stored = OfflineAction(
                id=action_id,
                action_type=action.action_type.value,
                idempotency_key=action.idempotency_key,
                encrypted_payload=action.encrypted_payload,
                created_at=created,
                next_attempt_at=created,
                state=OfflineActionState.READY,
                user_id=action.user_id,
                scope_type=action.scope_type,
                scope_id=action.scope_id,
                sequence_number=await self._repository.next_sequence_number(),
                updated_at=created,
                dependency_action_id=action.dependency_action_id,
            )
            await self._repository.save(stored)
            return stored

    async def process_pending(self) -> QueueProcessingResult:
        """Process each eligible action once under the profile processor lock."""
        if self._processing_lock.locked():
            return QueueProcessingResult(already_running=True)
        async with self._processing_lock:
            await self._recover_interrupted()
            counts = QueueProcessingResult()
            actions = await self._repository.list_pending()
            for action in actions:
                current = await self._repository.get(action.id)
                if current is None or current.state in {
                    OfflineActionState.CANCELLED,
                    OfflineActionState.COMPLETED,
                    OfflineActionState.FAILED_PERMANENT,
                }:
                    continue
                if current.state is OfflineActionState.PENDING:
                    current = current.transition(
                        OfflineActionState.READY, now=self._clock()
                    )
                    await self._repository.save(current)
                if current.state is OfflineActionState.RETRY_WAIT:
                    if (
                        current.next_attempt_at
                        and current.next_attempt_at > self._clock()
                    ):
                        continue
                    current = current.transition(
                        OfflineActionState.READY, now=self._clock()
                    )
                    await self._repository.save(current)
                if current.state is OfflineActionState.BLOCKED:
                    continue
                dependency_ready = await self._dependency_ready(current)
                if not dependency_ready:
                    if current.state is OfflineActionState.READY:
                        current = current.transition(
                            OfflineActionState.PROCESSING, now=self._clock()
                        ).transition(
                            OfflineActionState.BLOCKED,
                            now=self._clock(),
                            failure_code="offline_dependency_incomplete",
                        )
                        await self._repository.save(current)
                    counts = self._increment(counts, processed=1, blocked=1)
                    continue
                processing = current.transition(
                    OfflineActionState.PROCESSING, now=self._clock()
                )
                await self._repository.save(processing)
                try:
                    result = await self._executor.execute(
                        processing, processing.encrypted_payload
                    )
                except asyncio.CancelledError:
                    await self._schedule_retry(processing, "processing_interrupted")
                    raise
                except Exception:
                    result = OfflineActionExecutionResult(
                        OfflineActionOutcome.RETRYABLE_FAILURE,
                        failure_code="offline_executor_failure",
                    )
                counts = await self._apply_result(processing, result, counts)
            return counts

    async def unblock_after_sync(self, scope: SynchronisationScope) -> int:
        """Make matching blocked actions ready after authoritative scope refresh."""
        actions = await self._repository.list_by_states(
            frozenset({OfflineActionState.BLOCKED})
        )
        count = 0
        for action in actions:
            if action.scope_type not in {scope.value, "global"}:
                continue
            await self._repository.save(
                action.transition(OfflineActionState.READY, now=self._clock())
            )
            count += 1
        return count

    async def retry_now(self, action_id: UUID) -> None:
        """Promote a retryable or blocked action for an immediate manual attempt."""
        action = await self._require(action_id)
        if action.state not in {
            OfflineActionState.PENDING,
            OfflineActionState.RETRY_WAIT,
            OfflineActionState.BLOCKED,
        }:
            raise ValueError("Offline action cannot be retried")
        await self._repository.save(
            action.transition(OfflineActionState.READY, now=self._clock())
        )

    async def cancel(self, action_id: UUID) -> None:
        """Cancel an action only before a server acknowledgement exists."""
        action = await self._require(action_id)
        if action.state not in {
            OfflineActionState.PENDING,
            OfflineActionState.READY,
            OfflineActionState.RETRY_WAIT,
            OfflineActionState.BLOCKED,
        }:
            raise ValueError("Offline action cannot be cancelled")
        await self._repository.save(
            action.transition(OfflineActionState.CANCELLED, now=self._clock())
        )

    async def list_visible(self) -> list[OfflineActionSummary]:
        """Return queue-safe summaries without decrypted payload data."""
        actions = await self._repository.list_by_states(frozenset(OfflineActionState))
        return [
            OfflineActionSummary(
                action.id,
                OfflineActionType(action.action_type),
                action.state,
                action.created_at,
                action.attempts,
                action.last_error_code,
                action.scope_id,
            )
            for action in actions
        ]

    async def _apply_result(
        self,
        action: OfflineAction,
        result: OfflineActionExecutionResult,
        counts: QueueProcessingResult,
    ) -> QueueProcessingResult:
        if result.outcome is OfflineActionOutcome.SUCCEEDED:
            updated = action.transition(
                OfflineActionState.COMPLETED,
                now=self._clock(),
                server_reference=result.server_reference,
            )
            values = {"completed": 1}
        elif result.outcome is OfflineActionOutcome.RETRYABLE_FAILURE:
            updated = await self._schedule_retry(
                action, result.failure_code or "temporary_failure", result.retry_after
            )
            values = {"retrying": 1}
        elif result.outcome is OfflineActionOutcome.BLOCKED:
            updated = action.transition(
                OfflineActionState.BLOCKED,
                now=self._clock(),
                failure_code=result.failure_code or "action_blocked",
            )
            values = {"blocked": 1}
        else:
            updated = action.transition(
                OfflineActionState.FAILED_PERMANENT,
                now=self._clock(),
                failure_code=result.failure_code or "permanent_failure",
            )
            values = {"permanently_failed": 1}
        await self._repository.save(updated)
        return self._increment(counts, processed=1, **values)

    async def _schedule_retry(
        self,
        action: OfflineAction,
        failure_code: str,
        retry_after: datetime | None = None,
    ) -> OfflineAction:
        index = min(max(action.attempts - 1, 0), len(self._BACKOFF_SECONDS) - 1)
        seconds = self._jitter(0.8, 1.2) * self._BACKOFF_SECONDS[index]
        updated = action.transition(
            OfflineActionState.RETRY_WAIT,
            now=self._clock(),
            next_attempt_at=retry_after or self._clock() + timedelta(seconds=seconds),
            failure_code=failure_code,
        )
        await self._repository.save(updated)
        return updated

    async def _recover_interrupted(self) -> None:
        actions = await self._repository.list_by_states(
            frozenset({OfflineActionState.PROCESSING})
        )
        for action in actions:
            await self._schedule_retry(action, "processing_interrupted", self._clock())

    async def _dependency_ready(self, action: OfflineAction) -> bool:
        if action.dependency_action_id is None:
            return True
        dependency = await self._repository.get(action.dependency_action_id)
        return (
            dependency is not None and dependency.state is OfflineActionState.COMPLETED
        )

    async def _reject_dependency_cycle(
        self, action_id: UUID, dependency_id: UUID | None
    ) -> None:
        seen = {action_id}
        current = dependency_id
        while current is not None:
            if current in seen:
                raise ValueError("Offline action dependency cycle detected")
            seen.add(current)
            dependency = await self._repository.get(current)
            current = dependency.dependency_action_id if dependency else None

    async def _require(self, action_id: UUID) -> OfflineAction:
        action = await self._repository.get(action_id)
        if action is None:
            raise KeyError(action_id)
        return action

    @staticmethod
    def _increment(
        result: QueueProcessingResult, **increments: int
    ) -> QueueProcessingResult:
        values = {
            field: getattr(result, field) for field in result.__dataclass_fields__
        }
        for name, amount in increments.items():
            values[name] = int(values[name]) + amount
        return QueueProcessingResult(**values)
