"""Task 20 monitoring, maintenance, diagnostics, metrics, and worker evidence."""

# mypy: disable-error-code="arg-type,dict-item"

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission
from bluebubbles.server.monitoring.checks import (
    BackupStatusHealthCheck,
    OutboxHealthCheck,
    TLSCertificateHealthCheck,
    WebSocketHealthCheck,
    WorkerHealthCheck,
)
from bluebubbles.server.monitoring.metrics import MetricsService, MetricsSnapshot
from bluebubbles.server.services.diagnostics import ServerDiagnosticService
from bluebubbles.server.services.maintenance import MaintenanceService
from bluebubbles.server.services.monitoring import (
    AdminDashboardService,
    MonitoringService,
)
from bluebubbles.server.workers.base import BackgroundWorker, ManagedWorkerState
from bluebubbles.server.workers.manager import WorkerManager
from bluebubbles.shared.errors.exceptions import (
    AuthorisationError,
    ConflictError,
    ResourceNotFoundError,
)
from bluebubbles.shared.models.administration import MaintenanceState
from bluebubbles.shared.models.health import (
    ComponentHealth,
    DetailedHealthResponse,
    HealthState,
)

NOW = datetime(2026, 7, 18, 12, tzinfo=UTC)
USER_ID = UUID("40000000-0000-0000-0000-000000000001")


class FakeUow(SimpleNamespace):
    """Expose repositories through the asynchronous Unit-of-Work protocol."""

    async def __aenter__(self) -> FakeUow:
        return self

    async def __aexit__(self, *args: object) -> None:
        del args

    async def commit(self) -> None:
        self.committed = True


class FakeFactory:
    """Return one deterministic fake Unit of Work."""

    def __init__(self, uow: FakeUow) -> None:
        self.uow = uow

    def __call__(self) -> FakeUow:
        return self.uow


def _requester(*permissions: Permission) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=USER_ID,
        session_id=uuid4(),
        username="administrator",
        role_id=uuid4(),
        permissions=frozenset(permission.value for permission in permissions),
    )


def _permission_service() -> SimpleNamespace:
    return SimpleNamespace(require_authenticated_permission=AsyncMock())


def _audit_writer() -> SimpleNamespace:
    return SimpleNamespace(append=AsyncMock(return_value=SimpleNamespace(id=uuid4())))


def _certificate(path: Path, expires_at: datetime) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "server")])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(NOW - timedelta(days=1))
        .not_valid_after(expires_at)
        .sign(key, hashes.SHA256())
    )
    path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))


@pytest.mark.asyncio
async def test_tls_backup_outbox_websocket_and_worker_health(tmp_path: Path) -> None:
    certificate_path = tmp_path / "server.pem"
    _certificate(certificate_path, NOW + timedelta(days=90))
    healthy_tls = TLSCertificateHealthCheck(
        certificate_path, enabled=True, clock=lambda: NOW
    )
    assert (await healthy_tls.check_health()).state is HealthState.HEALTHY
    _certificate(certificate_path, NOW + timedelta(days=2))
    assert (await healthy_tls.check_health()).state is HealthState.DEGRADED
    _certificate(certificate_path, NOW - timedelta(days=1))
    assert (await healthy_tls.check_health()).state is HealthState.UNHEALTHY
    assert (
        await TLSCertificateHealthCheck(None, enabled=False).check_health()
    ).message == "disabled"
    assert (
        await TLSCertificateHealthCheck(None, enabled=True).check_health()
    ).state is HealthState.UNHEALTHY
    certificate_path.write_text("not a certificate", encoding="utf-8")
    assert (await healthy_tls.check_health()).state is HealthState.UNHEALTHY

    backup_path = tmp_path / "backup.json"
    backup_path.write_text(
        json.dumps(
            {
                "completed_at": NOW.isoformat(),
                "successful": True,
                "checksum_valid": True,
            }
        ),
        encoding="utf-8",
    )
    backup = BackupStatusHealthCheck(backup_path, clock=lambda: NOW)
    assert (await backup.check_health()).state is HealthState.HEALTHY
    stale = BackupStatusHealthCheck(
        backup_path,
        maximum_age=timedelta(hours=1),
        clock=lambda: NOW + timedelta(days=1),
    )
    assert (await stale.check_health()).state is HealthState.DEGRADED
    backup_path.write_text("{}", encoding="utf-8")
    assert (await backup.check_health()).state is HealthState.UNHEALTHY
    backup_path.write_text(
        json.dumps(
            {
                "completed_at": NOW.isoformat(),
                "successful": False,
                "checksum_valid": True,
            }
        ),
        encoding="utf-8",
    )
    assert (await backup.check_health()).message == "failed"
    assert (
        await BackupStatusHealthCheck(None).check_health()
    ).state is HealthState.DEGRADED

    outbox = SimpleNamespace(count_unpublished=AsyncMock(return_value=0))
    outbox_check = OutboxHealthCheck(
        cast(object, FakeFactory(FakeUow(outbox=outbox))),
        warning_count=2,
        critical_count=4,
    )
    assert (await outbox_check.check_health()).state is HealthState.HEALTHY
    outbox.count_unpublished.return_value = 2
    assert (await outbox_check.check_health()).state is HealthState.DEGRADED
    outbox.count_unpublished.return_value = 4
    assert (await outbox_check.check_health()).state is HealthState.UNHEALTHY

    connections = SimpleNamespace(connection_count=AsyncMock(return_value=3))
    assert (
        await WebSocketHealthCheck(cast(object, connections)).check_health()
    ).message == "connections:3"
    statuses = [SimpleNamespace(failure_count=0)]
    manager = SimpleNamespace(health_statuses=lambda: tuple(statuses))
    worker_check = WorkerHealthCheck(
        cast(object, manager), repeated_failure_threshold=3
    )
    assert (await worker_check.check_health()).state is HealthState.HEALTHY
    statuses[0].failure_count = 1
    assert (await worker_check.check_health()).state is HealthState.DEGRADED
    statuses[0].failure_count = 3
    assert (await worker_check.check_health()).state is HealthState.UNHEALTHY


@pytest.mark.asyncio
async def test_background_worker_lifecycle_pause_failure_and_recovery() -> None:
    operation = AsyncMock(return_value=2)
    worker = BackgroundWorker("cleanup", 3600, operation)
    assert worker.status().state is ManagedWorkerState.STOPPED
    await worker.start()
    assert await worker.run_now() == 2
    worker.pause()
    assert worker.status().state is ManagedWorkerState.PAUSED
    worker.resume()
    assert worker.status().state is ManagedWorkerState.IDLE
    operation.side_effect = RuntimeError("safe failure test")
    with pytest.raises(RuntimeError):
        await worker.run_now()
    assert worker.status().last_error_code == "worker_run_failed"
    await worker.stop()
    assert worker.status().state is ManagedWorkerState.STOPPED
    critical = BackgroundWorker(
        "critical", 1, AsyncMock(return_value=0), pausable=False
    )
    with pytest.raises(ValueError):
        critical.pause()


@pytest.mark.asyncio
async def test_worker_manager_manual_run_duplicate_policy_and_pause() -> None:
    operation = AsyncMock(return_value=1)
    worker = BackgroundWorker("cleanup", 3600, operation)
    administration = SimpleNamespace(
        add_worker_execution=AsyncMock(),
        complete_worker_execution=AsyncMock(return_value=True),
    )
    uow = FakeUow(administration=administration, audit=object())
    manager = WorkerManager(
        (worker,),
        cast(object, FakeFactory(uow)),
        cast(object, _permission_service()),
        cast(object, _audit_writer()),
        lambda: NOW,
    )
    await manager.start()
    listed = await manager.list_workers(_requester(Permission.WORKER_VIEW))
    assert listed.workers[0].name == "cleanup"
    status = await manager.run_worker_now(
        _requester(Permission.WORKER_RUN), "cleanup", "Operator request"
    )
    assert status.name == "cleanup"
    assert administration.add_worker_execution.await_count == 1
    paused = await manager.pause_worker(
        _requester(Permission.WORKER_CONTROL), "cleanup"
    )
    assert paused.paused
    resumed = await manager.resume_worker(
        _requester(Permission.WORKER_CONTROL), "cleanup"
    )
    assert not resumed.paused
    manager._manual_running.add("cleanup")  # noqa: SLF001 - duplicate-run test setup
    with pytest.raises(ConflictError):
        await manager.run_worker_now(_requester(), "cleanup", "Duplicate")
    manager._manual_running.clear()  # noqa: SLF001 - duplicate-run test cleanup
    await manager.stop()


@pytest.mark.asyncio
async def test_worker_manager_missing_disallowed_and_failed_execution() -> None:
    disallowed = BackgroundWorker(
        "critical",
        3600,
        AsyncMock(return_value=0),
        manually_runnable=False,
        pausable=False,
    )
    failing = BackgroundWorker(
        "failing", 3600, AsyncMock(side_effect=RuntimeError("failure"))
    )
    administration = SimpleNamespace(
        add_worker_execution=AsyncMock(),
        complete_worker_execution=AsyncMock(return_value=True),
    )
    manager = WorkerManager(
        (disallowed, failing),
        cast(
            object, FakeFactory(FakeUow(administration=administration, audit=object()))
        ),
        cast(object, _permission_service()),
        cast(object, _audit_writer()),
        lambda: NOW,
    )
    with pytest.raises(ValueError):
        WorkerManager(
            (disallowed, disallowed),
            cast(object, FakeFactory(FakeUow())),
            cast(object, _permission_service()),
        )
    with pytest.raises(AuthorisationError):
        await manager.run_worker_now(_requester(), "critical", "Attempt")
    with pytest.raises(ResourceNotFoundError):
        await manager.run_worker_now(_requester(), "missing", "Attempt")
    failed = await manager.run_worker_now(_requester(), "failing", "Test failure")
    assert failed.state.value == "failed"
    with pytest.raises(ResourceNotFoundError):
        await manager.pause_worker(_requester(), "missing")


@pytest.mark.asyncio
async def test_metrics_monitoring_dashboard_maintenance_and_diagnostics(
    tmp_path: Path,
) -> None:
    connection = SimpleNamespace(user_id=USER_ID)
    connection_manager = SimpleNamespace(
        list_connections=AsyncMock(return_value=(connection, connection))
    )
    metrics = MetricsService(cast(object, connection_manager), tmp_path)
    snapshot = await metrics.snapshot()
    assert snapshot.connected_users == 1 and snapshot.active_connections == 2

    health = DetailedHealthResponse(
        status=HealthState.HEALTHY,
        timestamp=NOW,
        application_version="1.0",
        protocol_versions=(1,),
        components=(ComponentHealth(name="database", state=HealthState.HEALTHY),),
    )
    aggregator = SimpleNamespace(detailed_health=AsyncMock(return_value=health))
    permission_service = _permission_service()
    monitoring = MonitoringService(
        cast(object, aggregator), cast(object, permission_service)
    )
    assert (
        await monitoring.get_detailed_health(_requester())
    ).status is HealthState.HEALTHY
    metrics_fake = SimpleNamespace(
        snapshot=AsyncMock(return_value=MetricsSnapshot(1, 2, 3, 4, 5, 6))
    )
    dashboard = AdminDashboardService(
        cast(object, metrics_fake),
        monitoring,
        cast(object, permission_service),
        lambda: NOW,
    )
    response = await dashboard.build_dashboard(_requester())
    assert response.connected_users == 2 and response.disk_percent == 6

    audit = _audit_writer()
    maintenance = MaintenanceService(
        cast(object, FakeFactory(FakeUow(audit=object()))),
        cast(object, permission_service),
        cast(object, aggregator.detailed_health),
        cast(object, audit),
        lambda: NOW,
    )
    assert maintenance.get_state().state is MaintenanceState.NORMAL
    assert (await maintenance.view_state(_requester())).state is MaintenanceState.NORMAL
    state = await maintenance.change_state(
        _requester(), MaintenanceState.READ_ONLY, "Database upgrade"
    )
    assert state.state is MaintenanceState.READ_ONLY
    with pytest.raises(ConflictError):
        maintenance.require_write_available()
    await maintenance.change_state(_requester(), MaintenanceState.NORMAL, "Complete")
    maintenance.require_write_available()
    aggregator.detailed_health.return_value = health.model_copy(
        update={"status": HealthState.UNHEALTHY}
    )
    await maintenance.change_state(_requester(), MaintenanceState.FULL, "Failure")
    with pytest.raises(ConflictError):
        await maintenance.change_state(_requester(), MaintenanceState.NORMAL, "Unsafe")

    healthy_check = SimpleNamespace(
        check_health=AsyncMock(
            return_value=ComponentHealth(name="database", state=HealthState.HEALTHY)
        )
    )
    diagnostics = ServerDiagnosticService(
        {"database": cast(object, healthy_check)},
        cast(object, permission_service),
        timeout_seconds=1,
        clock=lambda: NOW,
    )
    report = await diagnostics.run(_requester(), {"database"})
    assert report.checks[0].state == "healthy"
    healthy_check.check_health.side_effect = TimeoutError
    report = await diagnostics.run(_requester())
    assert report.checks[0].state == "unhealthy" and report.checks[0].message is None
