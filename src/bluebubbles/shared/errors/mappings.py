"""Stable public metadata associated with each shared error code."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from bluebubbles.shared.errors.codes import ErrorCode


class RetryClassification(StrEnum):
    """Describe whether retrying an operation can be useful."""

    NEVER = "never"
    AFTER_CORRECTION = "after_correction"
    AFTER_DELAY = "after_delay"


class ErrorSeverity(StrEnum):
    """Classify the operational importance of a public error."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ErrorMetadata:
    """Define presentation-neutral metadata for a public error."""

    default_message: str
    http_status: int
    retry: RetryClassification = RetryClassification.NEVER
    severity: ErrorSeverity = ErrorSeverity.WARNING
    help_code: str | None = None


def _metadata(code: ErrorCode) -> ErrorMetadata:
    status = 400
    retry = RetryClassification.NEVER
    severity = ErrorSeverity.WARNING
    if code in {
        ErrorCode.INVALID_LOGIN,
        ErrorCode.INVALID_TOKEN,
        ErrorCode.SESSION_EXPIRED,
    }:
        status = 401
    elif code in {ErrorCode.USER_DISABLED, ErrorCode.INSUFFICIENT_PERMISSIONS}:
        status = 403
    elif code.name.endswith("NOT_FOUND"):
        status = 404
    elif code in {ErrorCode.CONFLICT, ErrorCode.MESSAGE_CONFLICT}:
        status = 409
    elif code is ErrorCode.RATE_LIMIT_EXCEEDED:
        status, retry = 429, RetryClassification.AFTER_DELAY
    elif code in {ErrorCode.SERVICE_UNAVAILABLE, ErrorCode.INTERNAL_ERROR}:
        status = 503 if code is ErrorCode.SERVICE_UNAVAILABLE else 500
        retry = RetryClassification.AFTER_DELAY
        severity = ErrorSeverity.ERROR
    message = code.value.replace("_", " ").capitalize()
    return ErrorMetadata(message, status, retry, severity, f"BB-{code.value}")


ERROR_METADATA: Final[Mapping[ErrorCode, ErrorMetadata]] = MappingProxyType(
    {code: _metadata(code) for code in ErrorCode}
)


def get_error_metadata(code: ErrorCode) -> ErrorMetadata:
    """Return stable metadata for ``code``."""
    return ERROR_METADATA[code]
