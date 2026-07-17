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
    IMMEDIATE_ONCE = "immediate_once"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    RETRY_AFTER = "retry_after"
    USER_ACTION_REQUIRED = "user_action_required"
    AFTER_CORRECTION = "user_action_required"
    AFTER_DELAY = "exponential_backoff"


class ErrorSeverity(StrEnum):
    """Classify the operational importance of a public error."""

    INFORMATIONAL = "informational"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    INFO = "informational"


@dataclass(frozen=True, slots=True)
class ErrorMetadata:
    """Define presentation-neutral metadata for a public error."""

    default_message: str
    http_status: int
    retry: RetryClassification = RetryClassification.NEVER
    severity: ErrorSeverity = ErrorSeverity.WARNING
    help_code: str | None = None
    title: str = "Unable to complete action"
    suggested_action: str | None = None


def _metadata(code: ErrorCode) -> ErrorMetadata:
    status = 400
    retry = RetryClassification.NEVER
    severity = ErrorSeverity.WARNING
    title = "Unable to complete action"
    action: str | None = None
    if code in {
        ErrorCode.INVALID_CREDENTIALS,
        ErrorCode.INVALID_LOGIN,
        ErrorCode.INVALID_TOKEN,
        ErrorCode.SESSION_EXPIRED,
        ErrorCode.SESSION_COMPROMISED,
        ErrorCode.SESSION_REVOKED,
    }:
        status = 401
        title = (
            "Session expired" if code is ErrorCode.SESSION_EXPIRED else "Sign-in failed"
        )
        action = (
            "Sign in again."
            if code is ErrorCode.SESSION_EXPIRED
            else "Check your sign-in details."
        )
    elif code in {
        ErrorCode.USER_DISABLED,
        ErrorCode.ACCOUNT_DISABLED,
        ErrorCode.INSUFFICIENT_PERMISSIONS,
        ErrorCode.PERMISSION_DENIED,
    }:
        status = 403
        title = "Access denied"
        action = "Contact the helpdesk if you believe you should have access."
    elif code is ErrorCode.ACCOUNT_LOCKED:
        status = 423
    elif code.name.endswith("NOT_FOUND") or code is ErrorCode.RESOURCE_NOT_FOUND:
        status = 404
    elif code in {ErrorCode.CONFLICT, ErrorCode.MESSAGE_CONFLICT}:
        status = 409
    elif code is ErrorCode.RATE_LIMIT_EXCEEDED:
        status, retry = 429, RetryClassification.RETRY_AFTER
        title = "Please wait"
    elif code in {
        ErrorCode.SERVICE_UNAVAILABLE,
        ErrorCode.NETWORK_UNAVAILABLE,
        ErrorCode.NETWORK_TIMEOUT,
        ErrorCode.DATABASE_UNAVAILABLE,
        ErrorCode.REDIS_UNAVAILABLE,
        ErrorCode.STORAGE_UNAVAILABLE,
        ErrorCode.DIRECTORY_UNAVAILABLE,
    }:
        status = 503
        retry = RetryClassification.EXPONENTIAL_BACKOFF
        severity = ErrorSeverity.ERROR
        title = "Server unavailable"
        action = "Try again shortly."
    elif code in {ErrorCode.INTERNAL_ERROR, ErrorCode.INTERNAL_SERVER_ERROR}:
        status = 500
        retry = RetryClassification.EXPONENTIAL_BACKOFF
        severity = ErrorSeverity.ERROR
        title = "Unexpected error"
        action = "Try again and provide the error reference if the problem continues."
    elif code is ErrorCode.ATTACHMENT_TOO_LARGE:
        status = 413
    elif code in {ErrorCode.VALIDATION_ERROR, ErrorCode.INVALID_REQUEST}:
        retry = RetryClassification.USER_ACTION_REQUIRED
    messages = {
        ErrorCode.INVALID_CREDENTIALS: "The username or password was not accepted.",
        ErrorCode.PERMISSION_DENIED: "You cannot perform this action.",
        ErrorCode.NETWORK_UNAVAILABLE: "BlueBubbles cannot reach the server.",
        ErrorCode.INTERNAL_SERVER_ERROR: (
            "BlueBubbles could not complete the request because of an unexpected "
            "server error."
        ),
    }
    message = messages.get(code, code.value.replace("_", " ").capitalize())
    return ErrorMetadata(
        message, status, retry, severity, f"BB-{code.value}", title, action
    )


ERROR_METADATA: Final[Mapping[ErrorCode, ErrorMetadata]] = MappingProxyType(
    {code: _metadata(code) for code in ErrorCode}
)


def get_error_metadata(code: ErrorCode) -> ErrorMetadata:
    """Return stable metadata for ``code``."""
    return ERROR_METADATA[code]
