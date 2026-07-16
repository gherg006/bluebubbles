"""Client-safe REST and WebSocket error response contracts."""

from typing import Annotated, Any
from uuid import UUID

from pydantic import Field

from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.errors.codes import ErrorCode


class FieldError(ContractModel):
    """Describe a validation failure for one public request field."""

    field: Annotated[str, Field(min_length=1, max_length=200)]
    message: Annotated[str, Field(min_length=1, max_length=500)]
    code: Annotated[str, Field(min_length=1, max_length=100)] | None = None


class ApiErrorDetail(ContractModel):
    """Contain safe structured details for an API failure."""

    message: Annotated[str, Field(min_length=1, max_length=1000)]
    fields: tuple[FieldError, ...] = ()
    retry_after_seconds: Annotated[int, Field(ge=0)] | None = None
    help_code: Annotated[str, Field(min_length=1, max_length=100)] | None = None


class ApiErrorResponse(ContractModel):
    """Standard error envelope returned by REST endpoints."""

    success: bool = False
    code: ErrorCode
    error: ApiErrorDetail
    correlation_id: UUID | None = None


class WebSocketErrorEventData(ContractModel):
    """Error event data safe to transmit over an authenticated socket."""

    code: ErrorCode
    message: Annotated[str, Field(min_length=1, max_length=1000)]
    retryable: bool = False
    context: dict[str, Any] = Field(default_factory=dict)
