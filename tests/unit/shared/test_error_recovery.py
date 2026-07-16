"""Tests for safe error translation, retry, and circuit breaking."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from bluebubbles.client.errors import ErrorDisplayContext, ErrorMessageCatalog
from bluebubbles.shared.errors import (
    AuthorisationError,
    CircuitBreaker,
    CircuitBreakerSettings,
    CircuitOpenError,
    CircuitState,
    DatabaseUnavailableError,
    ErrorCode,
    InvalidCredentialsError,
    RetryContext,
    RetryExecutor,
    RetryPolicy,
    StateTransitionValidator,
    to_api_error_response,
    unexpected_api_error_response,
)


def test_application_error_context_is_redacted_and_translates_safely() -> None:
    error = InvalidCredentialsError(
        technical_message="LDAP rejected bind",
        context={"operation": "login", "password": "secret", "raw_token": "token"},
    )
    assert error.code is ErrorCode.INVALID_CREDENTIALS
    assert error.context == {"operation": "login"}
    response = to_api_error_response(error, uuid4())
    assert response.error.code is ErrorCode.INVALID_CREDENTIALS
    assert "LDAP" not in response.error.message
    unexpected = unexpected_api_error_response(uuid4())
    assert unexpected.error.code is ErrorCode.INTERNAL_SERVER_ERROR


def test_client_error_catalogue_handles_known_and_unknown_codes() -> None:
    catalogue = ErrorMessageCatalog()
    known = catalogue.get_message(
        ErrorCode.PERMISSION_DENIED, ErrorDisplayContext(correlation_id=uuid4())
    )
    unknown = catalogue.get_message("FUTURE_CODE", ErrorDisplayContext())
    assert known.title == "Access denied" and known.technical_details_available
    assert unknown.code == "FUTURE_CODE" and "FUTURE_CODE" not in unknown.message


@pytest.mark.asyncio
async def test_retry_executor_retries_idempotent_dependency_failure() -> None:
    delays: list[float] = []

    async def sleep(delay: float) -> None:
        delays.append(delay)

    policy = RetryPolicy(
        maximum_attempts=3,
        initial_delay_seconds=1,
        maximum_delay_seconds=5,
        multiplier=2,
        jitter_ratio=0,
        retryable_codes=frozenset({ErrorCode.DATABASE_UNAVAILABLE}),
    )
    executor = RetryExecutor({"database": policy}, sleep=sleep)
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise DatabaseUnavailableError()
        return "ok"

    assert await executor.execute(operation, RetryContext("database", True)) == "ok"
    assert attempts == 3 and delays == [1, 2]
    assert policy.delay_for(1, 0.5) == 1
    with pytest.raises(ValueError, match="Unknown"):
        await executor.execute(operation, RetryContext("missing", True))


@pytest.mark.asyncio
async def test_retry_does_not_repeat_non_idempotent_or_permanent_error() -> None:
    policy = RetryPolicy(3, 0, 1, 2, 0, frozenset({ErrorCode.DATABASE_UNAVAILABLE}))
    executor = RetryExecutor({"test": policy})

    async def dependency_failure() -> None:
        raise DatabaseUnavailableError()

    async def denied() -> None:
        raise AuthorisationError()

    with pytest.raises(DatabaseUnavailableError):
        await executor.execute(dependency_failure, RetryContext("test", False))
    with pytest.raises(AuthorisationError):
        await executor.execute(denied, RetryContext("test", True))


@pytest.mark.asyncio
async def test_circuit_opens_fails_fast_and_recovers_half_open() -> None:
    now = datetime(2026, 7, 16, tzinfo=UTC)

    def clock() -> datetime:
        return now

    circuit = CircuitBreaker(CircuitBreakerSettings(2, timedelta(seconds=10)), clock)

    async def fail() -> None:
        raise DatabaseUnavailableError()

    with pytest.raises(DatabaseUnavailableError):
        await circuit.execute(fail)
    with pytest.raises(DatabaseUnavailableError):
        await circuit.execute(fail)
    assert circuit.state is CircuitState.OPEN
    with pytest.raises(CircuitOpenError):
        await circuit.execute(fail)
    now += timedelta(seconds=11)

    async def succeed() -> str:
        return "recovered"

    assert await circuit.execute(succeed) == "recovered"
    assert circuit.state.value == CircuitState.CLOSED.value


def test_generic_state_transition_validator() -> None:
    validator = StateTransitionValidator({"new": {"running"}, "running": {"done"}})
    validator.require_transition("new", "running")
    with pytest.raises(ValueError, match="Invalid state"):
        validator.require_transition("new", "done")
