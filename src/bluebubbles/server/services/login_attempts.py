"""Durable per-user and per-source failed-login throttling."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from bluebubbles.server.configuration.settings import (
    AuthenticationSettings,
    RateLimitSettings,
)
from bluebubbles.server.database.unit_of_work import UnitOfWork, UnitOfWorkFactory
from bluebubbles.server.domain.users import normalise_username
from bluebubbles.shared.errors.exceptions import AccountLockedError, RateLimitError


class LoginAttemptService:
    """Enforce and record login limits without retaining submitted passwords."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        authentication_settings: AuthenticationSettings,
        rate_limit_settings: RateLimitSettings,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._authentication = authentication_settings
        self._rate_limits = rate_limit_settings
        self._clock = clock or (lambda: datetime.now(UTC))

    async def require_allowed(self, username: str, source_ip: str | None) -> None:
        """Reject a username lockout or source request-rate breach before binding."""
        now = self._clock()
        since = now - timedelta(
            seconds=self._authentication.failed_login_window_seconds
        )
        async with self._unit_of_work_factory() as unit_of_work:
            username_failures, source_failures = (
                await unit_of_work.authentication.count_recent_failures(
                    normalised_username=normalise_username(username),
                    source_ip=source_ip,
                    since=since,
                )
            )
        if username_failures >= self._authentication.failed_login_limit:
            raise AccountLockedError(
                retry_after_seconds=self._authentication.application_lockout_seconds
            )
        if source_failures >= self._rate_limits.login_requests_per_window:
            raise RateLimitError(
                retry_after_seconds=self._rate_limits.login_window_seconds
            )

    async def record_failure(
        self,
        username: str,
        source_ip: str | None,
        correlation_id: UUID,
        failure_category: str,
    ) -> None:
        """Commit a safe failure when authentication has no transaction."""
        async with self._unit_of_work_factory() as unit_of_work:
            await self.record(
                unit_of_work,
                username=username,
                source_ip=source_ip,
                correlation_id=correlation_id,
                result="failed",
                failure_category=failure_category,
            )
            await unit_of_work.commit()

    async def record(
        self,
        unit_of_work: UnitOfWork,
        *,
        username: str,
        source_ip: str | None,
        correlation_id: UUID,
        result: str,
        failure_category: str | None,
    ) -> None:
        """Stage one attempt inside a caller-owned business transaction."""
        await unit_of_work.authentication.add_login_attempt(
            attempt_id=uuid4(),
            normalised_username=normalise_username(username),
            source_ip=source_ip,
            result=result,
            failure_category=failure_category,
            attempted_at=self._clock(),
            correlation_id=correlation_id,
        )
