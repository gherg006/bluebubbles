"""Administrative dashboard, audit, alert, configuration, and job contracts."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import Field

from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.models.health import ComponentHealth
from bluebubbles.shared.models.pagination import CursorPageMetadata


class JobState(StrEnum):
    """Represent an administrative background job lifecycle."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MaintenanceState(StrEnum):
    """Represent server write availability during controlled maintenance."""

    NORMAL = "normal"
    READ_ONLY = "read_only"
    FULL = "full"


class AdministrativeCapabilities(ContractModel):
    """Describe presentation hints derived from current server permissions."""

    can_open_admin: bool
    can_view_dashboard: bool
    can_manage_users: bool
    can_manage_sessions: bool
    can_view_connections: bool
    can_view_audit: bool
    can_export_audit: bool
    can_manage_alerts: bool
    can_manage_announcements: bool
    can_view_health: bool
    can_run_workers: bool
    can_modify_configuration: bool
    can_control_maintenance: bool


class AdminDashboardResponse(ContractModel):
    """Return aggregated operational statistics safe for administrators."""

    connected_users: Annotated[int, Field(ge=0)]
    messages_today: Annotated[int, Field(ge=0)]
    active_uploads: Annotated[int, Field(ge=0)]
    cpu_percent: Annotated[float, Field(ge=0, le=100)]
    memory_percent: Annotated[float, Field(ge=0, le=100)]
    disk_percent: Annotated[float, Field(ge=0, le=100)]
    components: tuple[ComponentHealth, ...]
    generated_at: datetime


class AdminUserSummary(ContractModel):
    """Return client-safe directory and account state for administration."""

    id: UUID
    username: str
    display_name: str
    role: str
    department: str | None = None
    is_enabled: bool
    active_sessions: Annotated[int, Field(ge=0)]
    last_login: datetime | None = None
    version: Annotated[int, Field(ge=1)] = 1


class AdminUserPageResponse(ContractModel):
    """Return a bounded page of permission-filtered account summaries."""

    users: tuple[AdminUserSummary, ...]
    page: CursorPageMetadata


class AdministrativeReasonRequest(ContractModel):
    """Carry a bounded, auditable reason and optimistic user version."""

    reason: Annotated[str, Field(min_length=1, max_length=1000)]
    expected_user_version: Annotated[int, Field(ge=1)]


class ChangeUserRoleRequest(AdministrativeReasonRequest):
    """Request an authorised fixed-role assignment."""

    role_id: UUID


class UserAdministrationResult(ContractModel):
    """Return committed account state and its session-revocation effect."""

    user: AdminUserSummary
    invalidated_sessions: Annotated[int, Field(ge=0)] = 0
    audit_event_id: UUID


class AuditEventResponse(ContractModel):
    """Return immutable audit metadata with no plaintext message content."""

    id: UUID
    event_type: Annotated[str, Field(min_length=1, max_length=100)]
    actor_id: UUID | None = None
    occurred_at: datetime
    severity: Annotated[str, Field(min_length=1, max_length=20)]
    correlation_id: UUID | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    chain_hash: Annotated[str, Field(min_length=1, max_length=256)]
    sequence_number: Annotated[int, Field(ge=1)]


class AuditPageResponse(ContractModel):
    """Return a cursor page of immutable audit events."""

    events: tuple[AuditEventResponse, ...]
    page: CursorPageMetadata


class AuditVerificationResponse(ContractModel):
    """Return a safe recent or full audit-integrity result."""

    valid: bool
    mode: str
    checked_events: Annotated[int, Field(ge=0)]
    first_invalid_sequence: Annotated[int, Field(ge=1)] | None = None
    reason_code: str | None = None
    verified_at: datetime


class SecurityAlertResponse(ContractModel):
    """Return a sanitised security alert for authorised administrators."""

    id: UUID
    alert_type: str
    severity: str
    summary: Annotated[str, Field(min_length=1, max_length=500)]
    created_at: datetime
    acknowledged_at: datetime | None = None
    status: str = "open"
    occurrence_count: Annotated[int, Field(ge=1)] = 1
    resolved_at: datetime | None = None


class AlertTransitionRequest(ContractModel):
    """Carry notes required for auditable alert transitions."""

    notes: Annotated[str, Field(min_length=1, max_length=2000)]


class ConfigurationSummary(ContractModel):
    """Return non-secret effective configuration values."""

    revision: Annotated[int, Field(ge=1)]
    values: dict[str, str | int | float | bool | None]
    updated_at: datetime


class ConfigurationUpdateRequest(ContractModel):
    """Request a versioned update to the approved public setting allowlist."""

    expected_revision: Annotated[int, Field(ge=0)]
    values: dict[str, str | int | float | bool | None]
    reason: Annotated[str, Field(min_length=1, max_length=1000)]


class WorkerStatusResponse(ContractModel):
    """Return lifecycle and progress metadata for one managed worker."""

    name: str
    state: JobState
    last_started_at: datetime | None = None
    last_completed_at: datetime | None = None
    last_error_code: str | None = None
    manually_runnable: bool = False
    pausable: bool = False
    paused: bool = False


class WorkerListResponse(ContractModel):
    """Return one timestamped snapshot of every lifecycle-owned worker."""

    workers: tuple[WorkerStatusResponse, ...]
    generated_at: datetime


class WorkerRunRequest(ContractModel):
    """Carry the mandatory reason for a manual worker execution."""

    reason: Annotated[str, Field(min_length=1, max_length=1000)]


class DataExportJobResponse(ContractModel):
    """Return state for a bounded administrative data export."""

    id: UUID
    state: JobState
    requested_at: datetime
    completed_at: datetime | None = None
    progress_percent: Annotated[float, Field(ge=0, le=100)] = 0
    download_url: Annotated[str, Field(max_length=2048)] | None = None


class AdminConnectionResponse(ContractModel):
    """Return transient, token-free connection metadata."""

    connection_id: UUID
    user_id: UUID
    session_id: UUID
    connected_at: datetime
    last_heartbeat_at: datetime


class ConnectionListResponse(ContractModel):
    """Return currently registered administrative connection summaries."""

    connections: tuple[AdminConnectionResponse, ...]
    generated_at: datetime


class SessionRevocationResult(ContractModel):
    """Return committed revocation state separately from socket delivery."""

    session_id: UUID
    user_id: UUID
    invalidated_at: datetime
    disconnected_connection_count: Annotated[int, Field(ge=0)]
    audit_event_id: UUID


class MaintenanceStateResponse(ContractModel):
    """Return current controlled maintenance state."""

    state: MaintenanceState
    changed_at: datetime
    changed_by: UUID | None = None


class MaintenanceChangeRequest(ContractModel):
    """Request a reasoned transition into or out of maintenance."""

    state: MaintenanceState
    reason: Annotated[str, Field(min_length=1, max_length=1000)]


class DiagnosticCheckResult(ContractModel):
    """Return one bounded privacy-safe diagnostic result."""

    name: str
    state: str
    message: str | None = None
    duration_ms: Annotated[float, Field(ge=0)]


class ServerDiagnosticReport(ContractModel):
    """Return selected privacy-safe diagnostics with no credential material."""

    generated_at: datetime
    checks: tuple[DiagnosticCheckResult, ...]
