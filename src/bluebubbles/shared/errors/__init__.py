"""Public error codes, envelopes, and presentation-neutral metadata."""

from bluebubbles.shared.errors.codes import ErrorCode
from bluebubbles.shared.errors.mappings import (
    ERROR_METADATA,
    ErrorMetadata,
    ErrorSeverity,
    RetryClassification,
    get_error_metadata,
)
from bluebubbles.shared.errors.models import (
    ApiErrorDetail,
    ApiErrorResponse,
    FieldError,
    WebSocketErrorEventData,
)

__all__ = [
    "ERROR_METADATA",
    "ApiErrorDetail",
    "ApiErrorResponse",
    "ErrorCode",
    "ErrorMetadata",
    "ErrorSeverity",
    "FieldError",
    "RetryClassification",
    "WebSocketErrorEventData",
    "get_error_metadata",
]
