"""Safe construction helpers for REST and WebSocket error envelopes."""

from datetime import UTC, datetime
from uuid import UUID

from bluebubbles.shared.errors.codes import ErrorCode
from bluebubbles.shared.errors.exceptions import BlueBubblesError
from bluebubbles.shared.errors.mappings import get_error_metadata
from bluebubbles.shared.errors.models import ApiErrorDetail, ApiErrorResponse


def to_api_error_response(
    error: BlueBubblesError,
    correlation_id: UUID,
    *,
    timestamp: datetime | None = None,
) -> ApiErrorResponse:
    """Translate one expected error into client-safe REST data."""
    metadata = get_error_metadata(error.code)
    return ApiErrorResponse(
        error=ApiErrorDetail(
            code=error.code,
            message=error.user_message,
            retryable=error.retryable,
            retry_after_seconds=error.retry_after_seconds,
            help_code=metadata.help_code,
        ),
        correlation_id=correlation_id,
        timestamp=timestamp or datetime.now(UTC),
    )


def unexpected_api_error_response(
    correlation_id: UUID, *, timestamp: datetime | None = None
) -> ApiErrorResponse:
    """Return a generic response that reveals no unexpected exception details."""
    code = ErrorCode.INTERNAL_SERVER_ERROR
    metadata = get_error_metadata(code)
    return ApiErrorResponse(
        error=ApiErrorDetail(
            code=code,
            message=metadata.default_message,
            retryable=True,
            help_code=metadata.help_code,
        ),
        correlation_id=correlation_id,
        timestamp=timestamp or datetime.now(UTC),
    )
