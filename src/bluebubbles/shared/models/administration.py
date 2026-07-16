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


class AuditPageResponse(ContractModel):
    """Return a cursor page of immutable audit events."""

    events: tuple[AuditEventResponse, ...]
    page: CursorPageMetadata


class SecurityAlertResponse(ContractModel):
    """Return a sanitised security alert for authorised administrators."""

    id: UUID
    alert_type: str
    severity: str
    summary: Annotated[str, Field(min_length=1, max_length=500)]
    created_at: datetime
    acknowledged_at: datetime | None = None


class ConfigurationSummary(ContractModel):
    """Return non-secret effective configuration values."""

    revision: Annotated[int, Field(ge=1)]
    values: dict[str, str | int | float | bool | None]
    updated_at: datetime


class WorkerStatusResponse(ContractModel):
    """Return lifecycle and progress metadata for one managed worker."""

    name: str
    state: JobState
    last_started_at: datetime | None = None
    last_completed_at: datetime | None = None
    last_error_code: str | None = None


class DataExportJobResponse(ContractModel):
    """Return state for a bounded administrative data export."""

    id: UUID
    state: JobState
    requested_at: datetime
    completed_at: datetime | None = None
    progress_percent: Annotated[float, Field(ge=0, le=100)] = 0
    download_url: Annotated[str, Field(max_length=2048)] | None = None
