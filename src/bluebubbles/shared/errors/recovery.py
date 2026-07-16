"""Bounded retry and dependency circuit-breaker primitives shared by both programs."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Collection, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from random import SystemRandom
from typing import Generic, TypeVar

from bluebubbles.shared.errors.codes import ErrorCode
from bluebubbles.shared.errors.exceptions import BlueBubblesError, DependencyError

T = TypeVar("T")
StateType = TypeVar("StateType")


class CircuitState(StrEnum):
    """Define the current state of a dependency circuit."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Define bounded exponential retry behaviour for one operation category."""

    maximum_attempts: int
    initial_delay_seconds: float
    maximum_delay_seconds: float
    multiplier: float
    jitter_ratio: float
    retryable_codes: frozenset[ErrorCode]

    def __post_init__(self) -> None:
        if self.maximum_attempts < 1:
            raise ValueError("A retry policy requires at least one attempt")
        if (
            self.initial_delay_seconds < 0
            or self.maximum_delay_seconds < self.initial_delay_seconds
        ):
            raise ValueError("Retry delay bounds are invalid")
        if self.multiplier < 1 or not 0 <= self.jitter_ratio <= 1:
            raise ValueError("Retry multiplier or jitter ratio is invalid")

    def delay_for(self, failed_attempt: int, random_fraction: float) -> float:
        """Calculate one bounded delay with proportional jitter."""
        if failed_attempt < 1 or not 0 <= random_fraction <= 1:
            raise ValueError("Retry attempt and random fraction are invalid")
        base = min(
            self.maximum_delay_seconds,
            self.initial_delay_seconds * self.multiplier ** (failed_attempt - 1),
        )
        jitter = base * self.jitter_ratio
        return max(
            0.0,
            min(
                self.maximum_delay_seconds,
                base - jitter + (2 * jitter * random_fraction),
            ),
        )


@dataclass(frozen=True, slots=True)
class RetryContext:
    """Describe the safety and policy identity of one retryable operation."""

    policy_name: str
    idempotent: bool
    cancellation_event: asyncio.Event | None = None


class RetryExecutor:
    """Execute idempotent operations under a named bounded retry policy."""

    def __init__(
        self,
        policies: Mapping[str, RetryPolicy],
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        random: SystemRandom | None = None,
    ) -> None:
        self._policies = dict(policies)
        self._sleep = sleep
        self._random = random or SystemRandom()

    async def execute(
        self, operation: Callable[[], Awaitable[T]], context: RetryContext
    ) -> T:
        """Run an operation, preserving its final exception after bounded retries."""
        policy = self._policies.get(context.policy_name)
        if policy is None:
            raise ValueError(f"Unknown retry policy: {context.policy_name}")
        attempt = 1
        while True:
            self._check_cancelled(context)
            try:
                return await operation()
            except BlueBubblesError as error:
                should_retry = (
                    context.idempotent
                    and error.retryable
                    and error.code in policy.retryable_codes
                    and attempt < policy.maximum_attempts
                )
                if not should_retry:
                    raise
                delay = policy.delay_for(attempt, self._random.random())
                if error.retry_after_seconds is not None:
                    delay = min(
                        policy.maximum_delay_seconds, float(error.retry_after_seconds)
                    )
                await self._wait(delay, context)
                attempt += 1

    @staticmethod
    def _check_cancelled(context: RetryContext) -> None:
        if (
            context.cancellation_event is not None
            and context.cancellation_event.is_set()
        ):
            raise asyncio.CancelledError

    async def _wait(self, delay: float, context: RetryContext) -> None:
        if context.cancellation_event is None:
            await self._sleep(delay)
            return
        sleep_task: asyncio.Future[None] = asyncio.ensure_future(self._sleep(delay))
        cancel_task: asyncio.Task[bool] = asyncio.create_task(
            context.cancellation_event.wait()
        )
        done, pending = await asyncio.wait(
            (sleep_task, cancel_task), return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        if cancel_task in done and cancel_task.result():
            sleep_task.cancel()
            await asyncio.gather(sleep_task, return_exceptions=True)
            raise asyncio.CancelledError


@dataclass(frozen=True, slots=True)
class CircuitBreakerSettings:
    """Configure dependency failure threshold and recovery probing."""

    failure_threshold: int
    open_duration: timedelta
    half_open_test_count: int = 1

    def __post_init__(self) -> None:
        if self.failure_threshold < 1 or self.open_duration.total_seconds() <= 0:
            raise ValueError("Circuit threshold and duration must be positive")
        if self.half_open_test_count < 1:
            raise ValueError("Half-open test count must be positive")


class CircuitOpenError(DependencyError):
    """Fail quickly while a dependency circuit remains open."""


class CircuitBreaker:
    """Prevent repeated calls to a failing dependency with async-safe state."""

    def __init__(
        self,
        settings: CircuitBreakerSettings,
        clock: Callable[[], datetime],
    ) -> None:
        self._settings = settings
        self._clock = clock
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at: datetime | None = None
        self._half_open_attempts = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Return the latest circuit state."""
        return self._state

    async def execute(self, operation: Callable[[], Awaitable[T]]) -> T:
        """Run a dependency operation or fail quickly while the circuit is open."""
        await self._require_call_allowed()
        try:
            result = await operation()
        except DependencyError:
            await self.record_failure()
            raise
        except BaseException:
            raise
        else:
            await self.record_success()
            return result

    async def _require_call_allowed(self) -> None:
        async with self._lock:
            if self._state is CircuitState.OPEN:
                assert self._opened_at is not None
                if self._clock() - self._opened_at < self._settings.open_duration:
                    raise CircuitOpenError()
                self._state = CircuitState.HALF_OPEN
                self._half_open_attempts = 0
            if self._state is CircuitState.HALF_OPEN:
                if self._half_open_attempts >= self._settings.half_open_test_count:
                    raise CircuitOpenError()
                self._half_open_attempts += 1

    async def record_success(self) -> None:
        """Close the circuit after a successful dependency operation."""
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._opened_at = None
            self._half_open_attempts = 0

    async def record_failure(self) -> None:
        """Increment dependency failures and open at the configured threshold."""
        async with self._lock:
            if self._state is CircuitState.HALF_OPEN:
                self._open()
                return
            self._failure_count += 1
            if self._failure_count >= self._settings.failure_threshold:
                self._open()

    def _open(self) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = self._clock()
        self._half_open_attempts = 0


class StateTransitionValidator(Generic[StateType]):  # noqa: UP046 - Python 3.12 runtime
    """Validate reusable finite-state transitions."""

    def __init__(
        self, allowed_transitions: Mapping[StateType, Collection[StateType]]
    ) -> None:
        self._allowed = {
            state: frozenset(targets) for state, targets in allowed_transitions.items()
        }

    def require_transition(self, current: StateType, target: StateType) -> None:
        """Raise when ``target`` is not allowed from ``current``."""
        if target not in self._allowed.get(current, frozenset()):
            raise ValueError(f"Invalid state transition: {current} -> {target}")
