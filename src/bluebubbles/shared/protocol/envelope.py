"""Versioned WebSocket event envelope and acknowledgement contracts."""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import Field, field_validator

from bluebubbles.shared._model import ContractModel, ImmutableContractModel
from bluebubbles.shared.protocol.event_types import WebSocketEventType
from bluebubbles.shared.validation import validate_protocol_version


class ProtocolMetadata(ImmutableContractModel):
    """Describe the protocol and application version used by one peer."""

    protocol_identifier: Annotated[str, Field(min_length=1, max_length=100)]
    protocol_version: int
    application_version: Annotated[str, Field(min_length=1, max_length=100)]

    @field_validator("protocol_version")
    @classmethod
    def _validate_version(cls, value: int) -> int:
        return validate_protocol_version(value)


class WebSocketEventEnvelope(ContractModel):
    """Carry one typed, correlated, versioned WebSocket event."""

    event_id: UUID
    event_type: WebSocketEventType
    protocol_version: int
    timestamp: datetime
    correlation_id: UUID | None = None
    data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("protocol_version")
    @classmethod
    def _validate_version(cls, value: int) -> int:
        return validate_protocol_version(value)


class WebSocketAcknowledgement(ContractModel):
    """Acknowledge successful or failed processing of one event."""

    event_id: UUID
    accepted: bool
    correlation_id: UUID | None = None
    error_code: str | None = None
