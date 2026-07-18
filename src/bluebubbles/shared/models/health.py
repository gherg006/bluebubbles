"""Separated public and administrative server health contracts."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import Field

from bluebubbles.shared._model import ContractModel, ImmutableContractModel


class HealthState(StrEnum):
    """Represent aggregate or component health."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class CapabilityState(StrEnum):
    """Represent availability of a server capability."""

    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ComponentHealth(ContractModel):
    """Describe one component without leaking credentials or topology details."""

    name: Annotated[str, Field(min_length=1, max_length=100)]
    state: HealthState
    latency_ms: Annotated[float, Field(ge=0)] | None = None
    message: Annotated[str, Field(max_length=500)] | None = None


class PublicHealthResponse(ContractModel):
    """Return minimal unauthenticated service health."""

    status: HealthState
    timestamp: datetime


class DetailedHealthResponse(PublicHealthResponse):
    """Return administrative component health and application version."""

    application_version: str
    protocol_versions: tuple[int, ...]
    components: tuple[ComponentHealth, ...]
    capabilities: dict[str, CapabilityState] = Field(default_factory=dict)


class ClientVisibleLimits(ImmutableContractModel):
    """Declare limits clients must enforce before requests."""

    maximum_message_bytes: Annotated[int, Field(gt=0)]
    maximum_attachment_bytes: Annotated[int, Field(gt=0)]
    maximum_group_members: Annotated[int, Field(gt=1)]
    maximum_page_size: Annotated[int, Field(gt=0)]


class ClientVisiblePolicies(ImmutableContractModel):
    """Declare non-sensitive behavioural policies visible to clients."""

    message_edit_window_seconds: Annotated[int, Field(ge=0)]
    message_delete_window_seconds: Annotated[int, Field(ge=0)]
    session_idle_timeout_seconds: Annotated[int, Field(gt=0)]


class ServerCapabilities(ImmutableContractModel):
    """Describe compatible protocols, algorithms, features, limits, and policies."""

    application_version: str
    protocol_versions: tuple[int, ...]
    capabilities: dict[str, CapabilityState]
    algorithms: tuple[str, ...]
    limits: ClientVisibleLimits
    policies: ClientVisiblePolicies
