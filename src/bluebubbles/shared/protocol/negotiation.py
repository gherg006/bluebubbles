"""Protocol capability exchange and authoritative server selection."""

from typing import Annotated

from pydantic import Field, model_validator

from bluebubbles.shared._model import ImmutableContractModel
from bluebubbles.shared.versioning import (
    ProtocolVersion,
    select_highest_common_protocol,
)


class ProtocolNegotiationRequest(ImmutableContractModel):
    """Declare client application and supported protocol versions."""

    client_version: Annotated[str, Field(min_length=1, max_length=100)]
    supported_protocols: tuple[int, ...]

    @model_validator(mode="after")
    def _validate_protocols(self) -> "ProtocolNegotiationRequest":
        _validate_versions(self.supported_protocols)
        return self


class ProtocolNegotiationResponse(ImmutableContractModel):
    """Report the server-selected protocol and compatibility outcome."""

    accepted: bool
    selected_protocol: int | None = None
    server_version: Annotated[str, Field(min_length=1, max_length=100)]
    minimum_client_version: Annotated[str, Field(min_length=1, max_length=100)]
    reason: Annotated[str, Field(min_length=1, max_length=500)] | None = None

    @model_validator(mode="after")
    def _validate_outcome(self) -> "ProtocolNegotiationResponse":
        if self.accepted != (self.selected_protocol is not None):
            raise ValueError("Accepted negotiations require a selected protocol")
        if self.selected_protocol is not None:
            ProtocolVersion(self.selected_protocol)
        return self


def negotiate_protocol(
    request: ProtocolNegotiationRequest,
    *,
    server_protocols: tuple[int, ...],
    server_version: str,
    minimum_client_version: str,
) -> ProtocolNegotiationResponse:
    """Select the highest common protocol, with the server authoritative."""
    _validate_versions(server_protocols)
    selected = select_highest_common_protocol(
        request.supported_protocols, server_protocols
    )
    return ProtocolNegotiationResponse(
        accepted=selected is not None,
        selected_protocol=selected.value if selected else None,
        server_version=server_version,
        minimum_client_version=minimum_client_version,
        reason=None if selected else "No mutually supported protocol version",
    )


def _validate_versions(values: tuple[int, ...]) -> None:
    if not values or len(values) != len(set(values)):
        raise ValueError("Protocol versions must be non-empty and unique")
    for value in values:
        ProtocolVersion(value)
