"""Bounded TLS, outbox, worker, connection, and backup health checks."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509

from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.websocket.manager import WebSocketConnectionManager
from bluebubbles.server.workers.manager import WorkerManager
from bluebubbles.shared.models.health import ComponentHealth, HealthState


class TLSCertificateHealthCheck:
    """Report certificate expiry state without returning paths or subject names."""

    def __init__(
        self,
        certificate_path: Path | None,
        *,
        enabled: bool,
        warning_days: int = 30,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._path = certificate_path
        self._enabled = enabled
        self._warning = timedelta(days=warning_days)
        self._clock = clock

    async def check_health(self) -> ComponentHealth:
        """Load and parse the configured PEM certificate in a worker thread."""
        if not self._enabled:
            return ComponentHealth(
                name="tls", state=HealthState.DEGRADED, message="disabled"
            )
        if self._path is None:
            return ComponentHealth(name="tls", state=HealthState.UNHEALTHY)
        try:
            data = await asyncio.to_thread(self._path.read_bytes)
            certificate = x509.load_pem_x509_certificate(data)
        except (OSError, ValueError):
            return ComponentHealth(name="tls", state=HealthState.UNHEALTHY)
        remaining = certificate.not_valid_after_utc - self._clock()
        if remaining.total_seconds() <= 0:
            return ComponentHealth(
                name="tls", state=HealthState.UNHEALTHY, message="expired"
            )
        if remaining <= self._warning:
            return ComponentHealth(
                name="tls", state=HealthState.DEGRADED, message="expiry_warning"
            )
        return ComponentHealth(name="tls", state=HealthState.HEALTHY)


class OutboxHealthCheck:
    """Translate durable delivery backlog thresholds into component health."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        *,
        warning_count: int = 100,
        critical_count: int = 1000,
    ) -> None:
        self._uow_factory = unit_of_work_factory
        self._warning = warning_count
        self._critical = critical_count

    async def check_health(self) -> ComponentHealth:
        """Count only metadata and expose a bounded aggregate message."""
        async with self._uow_factory() as uow:
            count = await uow.outbox.count_unpublished()
        if count >= self._critical:
            state = HealthState.UNHEALTHY
        elif count >= self._warning:
            state = HealthState.DEGRADED
        else:
            state = HealthState.HEALTHY
        return ComponentHealth(name="outbox", state=state, message=f"backlog:{count}")


class WorkerHealthCheck:
    """Aggregate managed worker failures without exposing exception text."""

    def __init__(
        self, manager: WorkerManager, *, repeated_failure_threshold: int
    ) -> None:
        self._manager = manager
        self._threshold = repeated_failure_threshold

    async def check_health(self) -> ComponentHealth:
        """Return unhealthy for repeated failures and degraded for any failure."""
        statuses = self._manager.health_statuses()
        failures = [int(getattr(status, "failure_count", 0)) for status in statuses]
        if any(count >= self._threshold for count in failures):
            state = HealthState.UNHEALTHY
        elif any(count > 0 for count in failures):
            state = HealthState.DEGRADED
        else:
            state = HealthState.HEALTHY
        return ComponentHealth(name="workers", state=state)


class WebSocketHealthCheck:
    """Report the registry as operational with an aggregate connection count."""

    def __init__(self, manager: WebSocketConnectionManager) -> None:
        self._manager = manager

    async def check_health(self) -> ComponentHealth:
        count = await self._manager.connection_count()
        return ComponentHealth(
            name="websocket", state=HealthState.HEALTHY, message=f"connections:{count}"
        )


class BackupStatusHealthCheck:
    """Validate a protected backup-script status file rather than infer success."""

    def __init__(
        self,
        status_path: Path | None,
        *,
        maximum_age: timedelta = timedelta(days=1),
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._path = status_path
        self._maximum_age = maximum_age
        self._clock = clock

    async def check_health(self) -> ComponentHealth:
        """Report unknown, stale, failed, or current backup status."""
        if self._path is None:
            return ComponentHealth(
                name="backup", state=HealthState.DEGRADED, message="not_configured"
            )
        try:
            payload = json.loads(
                await asyncio.to_thread(self._path.read_text, encoding="utf-8")
            )
            completed_at = datetime.fromisoformat(str(payload["completed_at"]))
            successful = payload["successful"] is True
            checksum_valid = payload["checksum_valid"] is True
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            return ComponentHealth(
                name="backup", state=HealthState.UNHEALTHY, message="invalid_status"
            )
        if completed_at.tzinfo is None or not successful or not checksum_valid:
            return ComponentHealth(
                name="backup", state=HealthState.UNHEALTHY, message="failed"
            )
        if self._clock() - completed_at > self._maximum_age:
            return ComponentHealth(
                name="backup", state=HealthState.DEGRADED, message="stale"
            )
        return ComponentHealth(name="backup", state=HealthState.HEALTHY)
