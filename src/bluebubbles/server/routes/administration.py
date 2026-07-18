"""Thin authenticated administrative HTTP transport boundaries."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse

from bluebubbles.server.container import ServerContainer
from bluebubbles.server.dependencies import get_server_container
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.routes.authentication import current_authenticated_user
from bluebubbles.shared.models.administration import (
    AdminDashboardResponse,
    AdministrativeCapabilities,
    AdministrativeReasonRequest,
    AdminUserPageResponse,
    AlertTransitionRequest,
    AuditPageResponse,
    AuditVerificationResponse,
    ChangeUserRoleRequest,
    ConfigurationSummary,
    ConfigurationUpdateRequest,
    ConnectionListResponse,
    DataExportJobResponse,
    MaintenanceChangeRequest,
    MaintenanceStateResponse,
    SecurityAlertResponse,
    ServerDiagnosticReport,
    SessionRevocationResult,
    UserAdministrationResult,
    WorkerListResponse,
    WorkerRunRequest,
    WorkerStatusResponse,
)
from bluebubbles.shared.models.announcements import (
    AnnouncementResponse,
    CreateAnnouncementRequest,
)
from bluebubbles.shared.models.health import DetailedHealthResponse
from bluebubbles.shared.models.sessions import SessionListResponse

router = APIRouter(prefix="/api/v1/admin", tags=["administration"])


def _required[T](value: T | None, name: str) -> T:
    if value is None:
        raise RuntimeError(f"{name} service is not configured")
    return value


@router.get("/capabilities", response_model=AdministrativeCapabilities)
async def capabilities(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> AdministrativeCapabilities:
    """Return client presentation hints derived from live server authority."""
    service = _required(container.services.admin, "Administration")
    return service.capabilities(current)


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def dashboard(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> AdminDashboardResponse:
    """Return one aggregate content-free operational snapshot."""
    service = _required(container.services.dashboard, "Dashboard")
    return await service.build_dashboard(current)


@router.get("/users", response_model=AdminUserPageResponse)
async def search_users(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
    query: str = "",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    after: str | None = None,
) -> AdminUserPageResponse:
    """Search administrative account metadata without logging the raw query."""
    service = _required(container.services.user_administration, "User administration")
    return await service.search_users(current, term=query, limit=limit, cursor=after)


@router.post("/users/{user_id}/disable", response_model=UserAdministrationResult)
async def disable_user(
    user_id: UUID,
    request: AdministrativeReasonRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> UserAdministrationResult:
    """Disable one eligible account through the transaction-owning service."""
    service = _required(container.services.user_administration, "User administration")
    return await service.disable_user(
        current,
        user_id,
        expected_version=request.expected_user_version,
        reason=request.reason,
    )


@router.post("/users/{user_id}/enable", response_model=UserAdministrationResult)
async def enable_user(
    user_id: UUID,
    request: AdministrativeReasonRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> UserAdministrationResult:
    """Enable one eligible account through the transaction-owning service."""
    service = _required(container.services.user_administration, "User administration")
    return await service.enable_user(
        current,
        user_id,
        expected_version=request.expected_user_version,
        reason=request.reason,
    )


@router.post("/users/{user_id}/role", response_model=UserAdministrationResult)
async def change_role(
    user_id: UUID,
    request: ChangeUserRoleRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> UserAdministrationResult:
    """Assign one allowed role with optimistic concurrency and session invalidation."""
    service = _required(container.services.user_administration, "User administration")
    return await service.change_role(
        current,
        user_id,
        request.role_id,
        expected_version=request.expected_user_version,
        reason=request.reason,
    )


@router.get("/users/{user_id}/sessions", response_model=SessionListResponse)
async def list_user_sessions(
    user_id: UUID,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> SessionListResponse:
    """Return token-free sessions for one policy-eligible target user."""
    service = _required(
        container.services.session_administration, "Session administration"
    )
    return SessionListResponse(sessions=await service.list_sessions(current, user_id))


@router.post("/sessions/{session_id}/revoke", response_model=SessionRevocationResult)
async def revoke_session(
    session_id: UUID,
    request: WorkerRunRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> SessionRevocationResult:
    """Revoke one session durably before its socket is disconnected."""
    service = _required(
        container.services.session_administration, "Session administration"
    )
    return await service.revoke_session(current, session_id, request.reason)


@router.get("/connections", response_model=ConnectionListResponse)
async def list_connections(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> ConnectionListResponse:
    """Return current transient connection metadata."""
    service = _required(
        container.services.connection_administration, "Connection administration"
    )
    return await service.list_connections(current)


@router.post("/connections/{connection_id}/disconnect")
async def disconnect_connection(
    connection_id: UUID,
    request: WorkerRunRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> dict[str, bool]:
    """Disconnect one socket while intentionally preserving its session."""
    service = _required(
        container.services.connection_administration, "Connection administration"
    )
    return {
        "disconnected": await service.disconnect_connection(
            current, connection_id, request.reason
        )
    }


@router.get("/audit", response_model=AuditPageResponse)
async def query_audit(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    after: str | None = None,
    category: str | None = None,
    actor_id: UUID | None = None,
) -> AuditPageResponse:
    """Return a permission-filtered immutable audit page."""
    service = _required(container.services.audit, "Audit")
    return await service.query(
        current, limit=limit, cursor=after, category=category, actor_id=actor_id
    )


@router.post("/audit/verify", response_model=AuditVerificationResponse)
async def verify_audit(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
    full: bool = False,
) -> AuditVerificationResponse:
    """Run recent or full hash-chain verification."""
    service = _required(container.services.audit_integrity, "Audit integrity")
    return await service.verify(current, full=full)


@router.get("/alerts", response_model=tuple[SecurityAlertResponse, ...])
async def list_alerts(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> tuple[SecurityAlertResponse, ...]:
    """Return recent sanitised security alerts."""
    service = _required(container.services.alerts, "Security alert")
    return await service.list_alerts(current, limit=limit)


@router.post("/alerts/{alert_id}/acknowledge", response_model=SecurityAlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    request: AlertTransitionRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> SecurityAlertResponse:
    """Acknowledge an open alert with required notes."""
    service = _required(container.services.alerts, "Security alert")
    return await service.acknowledge(current, alert_id, request.notes)


@router.post("/alerts/{alert_id}/resolve", response_model=SecurityAlertResponse)
async def resolve_alert(
    alert_id: UUID,
    request: AlertTransitionRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> SecurityAlertResponse:
    """Resolve an alert with required investigation notes."""
    service = _required(container.services.alerts, "Security alert")
    return await service.resolve(current, alert_id, request.notes)


@router.get("/health", response_model=DetailedHealthResponse)
async def detailed_health(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> DetailedHealthResponse:
    """Return detailed health only to an authorised administrative session."""
    service = _required(container.services.monitoring, "Monitoring")
    return await service.get_detailed_health(current)


@router.get("/workers", response_model=WorkerListResponse)
async def list_workers(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> WorkerListResponse:
    """Return registered lifecycle-owned worker state."""
    service = _required(container.services.workers, "Worker")
    return await service.list_workers(current)


@router.post("/workers/{worker_name}/run", response_model=WorkerStatusResponse)
async def run_worker(
    worker_name: str,
    request: WorkerRunRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> WorkerStatusResponse:
    """Run one explicitly allowed worker once."""
    service = _required(container.services.workers, "Worker")
    return await service.run_worker_now(current, worker_name, request.reason)


@router.get("/configuration", response_model=ConfigurationSummary)
async def configuration(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> ConfigurationSummary:
    """Return the latest public configuration revision."""
    service = _required(container.services.configuration, "Configuration")
    return await service.latest(current)


@router.get("/configuration/history", response_model=tuple[ConfigurationSummary, ...])
async def configuration_history(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> tuple[ConfigurationSummary, ...]:
    """Return the immutable public configuration revision history."""
    service = _required(container.services.configuration, "Configuration")
    return await service.history(current)


@router.post("/configuration", response_model=ConfigurationSummary)
async def update_configuration(
    request: ConfigurationUpdateRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> ConfigurationSummary:
    """Append an approved, secret-free configuration revision."""
    service = _required(container.services.configuration, "Configuration")
    return await service.update(
        current,
        expected_revision=request.expected_revision,
        values=request.values,
        reason=request.reason,
    )


@router.post("/announcements", response_model=AnnouncementResponse)
async def publish_announcement(
    request: CreateAnnouncementRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> AnnouncementResponse:
    """Publish one organisational announcement in an audited transaction."""
    service = _required(container.services.announcements, "Announcement")
    return await service.publish(current, request)


@router.post(
    "/announcements/{announcement_id}/withdraw", response_model=AnnouncementResponse
)
async def withdraw_announcement(
    announcement_id: UUID,
    request: WorkerRunRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> AnnouncementResponse:
    """Withdraw one announcement with a required reason."""
    service = _required(container.services.announcements, "Announcement")
    return await service.withdraw(current, announcement_id, request.reason)


@router.get("/maintenance", response_model=MaintenanceStateResponse)
async def maintenance_state(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> MaintenanceStateResponse:
    """Return maintenance state to an authenticated administrative caller."""
    service = _required(container.services.maintenance, "Maintenance")
    return await service.view_state(current)


@router.post("/maintenance", response_model=MaintenanceStateResponse)
async def change_maintenance(
    request: MaintenanceChangeRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> MaintenanceStateResponse:
    """Enter or exit controlled maintenance through the owning service."""
    service = _required(container.services.maintenance, "Maintenance")
    return await service.change_state(current, request.state, request.reason)


@router.get("/diagnostics", response_model=ServerDiagnosticReport)
async def diagnostics(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
    checks: str | None = None,
) -> ServerDiagnosticReport:
    """Run selected privacy-safe diagnostic checks under timeouts."""
    service = _required(container.services.diagnostics, "Diagnostic")
    selected = (
        {item.strip() for item in checks.split(",") if item.strip()} if checks else None
    )
    return await service.run(current, selected)


@router.post(
    "/exports",
    response_model=DataExportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_audit_export(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
    export_format: Annotated[str, Query(pattern="^(csv|json)$")] = "csv",
) -> DataExportJobResponse:
    """Queue a protected audit export owned by the requesting administrator."""
    service = _required(container.services.exports, "Audit export")
    return await service.create(current, export_format)


@router.get("/exports/{job_id}", response_model=DataExportJobResponse)
async def audit_export_status(
    job_id: UUID,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> DataExportJobResponse:
    """Return one unexpired export job to its requesting administrator."""
    service = _required(container.services.exports, "Audit export")
    return await service.get(current, job_id)


@router.get("/exports/{job_id}/download", response_class=FileResponse)
async def download_audit_export(
    job_id: UUID,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> FileResponse:
    """Download a completed export after ownership and expiry validation."""
    service = _required(container.services.exports, "Audit export")
    path = await service.download_path(current, job_id)
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")
