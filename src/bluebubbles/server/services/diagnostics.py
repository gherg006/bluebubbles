"""Timeout-bounded privacy-safe server diagnostic aggregation."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from time import perf_counter

from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission
from bluebubbles.server.monitoring.health import HealthCheck
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.shared.models.administration import (
    DiagnosticCheckResult,
    ServerDiagnosticReport,
)


class ServerDiagnosticService:
    """Run an allowlisted set of health checks with independent timeouts."""

    def __init__(
        self,
        checks: Mapping[str, HealthCheck],
        permission_service: PermissionService,
        *,
        timeout_seconds: float = 5,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Diagnostic timeout must be positive")
        self._checks = dict(checks)
        self._permissions = permission_service
        self._timeout = timeout_seconds
        self._clock = clock

    async def run(
        self, requester: AuthenticatedUser, requested_checks: set[str] | None = None
    ) -> ServerDiagnosticReport:
        """Run selected known checks and omit exception and topology detail."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.DIAGNOSTIC_RUN
        )
        names = set(self._checks) if requested_checks is None else requested_checks
        if not names <= set(self._checks):
            raise ValueError("Unknown diagnostic check")
        results = await asyncio.gather(*(self._run_one(name) for name in sorted(names)))
        return ServerDiagnosticReport(generated_at=self._clock(), checks=tuple(results))

    async def _run_one(self, name: str) -> DiagnosticCheckResult:
        started = perf_counter()
        try:
            result = await asyncio.wait_for(
                self._checks[name].check_health(), timeout=self._timeout
            )
            return DiagnosticCheckResult(
                name=name,
                state=result.state.value,
                message=result.message,
                duration_ms=(perf_counter() - started) * 1000,
            )
        except Exception:
            return DiagnosticCheckResult(
                name=name,
                state="unhealthy",
                message=None,
                duration_ms=(perf_counter() - started) * 1000,
            )
