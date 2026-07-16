"""Typed expected application exception hierarchy with safe public metadata."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import ClassVar

from bluebubbles.shared.errors.codes import ErrorCode
from bluebubbles.shared.errors.mappings import ErrorSeverity, get_error_metadata

_SENSITIVE_CONTEXT_MARKERS = (
    "password",
    "token",
    "secret",
    "private_key",
    "plaintext",
    "ciphertext",
    "database_url",
)


def sanitise_error_context(
    context: Mapping[str, object] | None,
) -> Mapping[str, object]:
    """Remove values whose keys indicate secret or message material."""
    safe = {
        key: value
        for key, value in (context or {}).items()
        if not any(marker in key.casefold() for marker in _SENSITIVE_CONTEXT_MARKERS)
    }
    return MappingProxyType(safe)


class BlueBubblesError(Exception):
    """Base class for expected application errors safe to map at boundaries."""

    default_code: ClassVar[ErrorCode] = ErrorCode.INTERNAL_ERROR

    def __init__(
        self,
        code: ErrorCode | None = None,
        user_message: str | None = None,
        *,
        technical_message: str | None = None,
        retryable: bool | None = None,
        severity: ErrorSeverity | None = None,
        context: Mapping[str, object] | None = None,
        retry_after_seconds: int | None = None,
    ) -> None:
        selected_code = code or self.default_code
        metadata = get_error_metadata(selected_code)
        public_message = user_message or metadata.default_message
        super().__init__(technical_message or public_message)
        self.code = selected_code
        self.user_message = public_message
        self.technical_message = technical_message
        self.retryable = (
            retryable
            if retryable is not None
            else metadata.retry
            not in {
                metadata.retry.NEVER,
                metadata.retry.USER_ACTION_REQUIRED,
            }
        )
        self.severity = severity or metadata.severity
        self.context = sanitise_error_context(context)
        if retry_after_seconds is not None and retry_after_seconds < 0:
            raise ValueError("retry_after_seconds cannot be negative")
        self.retry_after_seconds = retry_after_seconds


class ValidationError(BlueBubblesError):
    """Report an invalid application command or domain value."""

    default_code = ErrorCode.INVALID_REQUEST


class AuthenticationError(BlueBubblesError):
    """Report missing or invalid authentication."""

    default_code = ErrorCode.INVALID_TOKEN


class InvalidCredentialsError(AuthenticationError):
    """Report enumeration-safe credential rejection."""

    default_code = ErrorCode.INVALID_CREDENTIALS


class SessionExpiredError(AuthenticationError):
    """Report a session beyond its permitted lifetime."""

    default_code = ErrorCode.SESSION_EXPIRED


class InvalidTokenError(AuthenticationError):
    """Report an invalid opaque or signed token."""

    default_code = ErrorCode.INVALID_TOKEN


class AccountDisabledError(AuthenticationError):
    """Report a disabled account without authentication internals."""

    default_code = ErrorCode.ACCOUNT_DISABLED


class AuthorisationError(BlueBubblesError):
    """Report authenticated access without sufficient authority."""

    default_code = ErrorCode.PERMISSION_DENIED


class ResourceNotFoundError(BlueBubblesError):
    """Report a missing or deliberately concealed resource."""

    default_code = ErrorCode.RESOURCE_NOT_FOUND


class ConflictError(BlueBubblesError):
    """Report conflicting current state or idempotency data."""

    default_code = ErrorCode.CONFLICT


class RateLimitError(BlueBubblesError):
    """Report throttling with optional bounded retry advice."""

    default_code = ErrorCode.RATE_LIMIT_EXCEEDED


class NetworkError(BlueBubblesError):
    """Report a temporary client/server connectivity failure."""

    default_code = ErrorCode.NETWORK_UNAVAILABLE


class DependencyError(BlueBubblesError):
    """Base expected failure for an unavailable infrastructure dependency."""

    default_code = ErrorCode.SERVICE_UNAVAILABLE


class DirectoryUnavailableError(DependencyError):
    """Report temporary directory-service unavailability."""

    default_code = ErrorCode.DIRECTORY_UNAVAILABLE


class DatabaseUnavailableError(DependencyError):
    """Report temporary database unavailability."""

    default_code = ErrorCode.DATABASE_UNAVAILABLE


class RedisUnavailableError(DependencyError):
    """Report temporary Redis unavailability."""

    default_code = ErrorCode.REDIS_UNAVAILABLE


class StorageUnavailableError(DependencyError):
    """Report temporary encrypted-file storage unavailability."""

    default_code = ErrorCode.STORAGE_UNAVAILABLE


class RepositoryError(BlueBubblesError):
    """Represent a translated persistence failure."""


class StorageError(BlueBubblesError):
    """Represent a translated attachment-storage failure."""

    default_code = ErrorCode.STORAGE_UNAVAILABLE


class CryptographyError(BlueBubblesError):
    """Represent a cryptographic construction or verification failure."""

    default_code = ErrorCode.CRYPTOGRAPHIC_VERIFICATION_FAILED


class ProtocolError(BlueBubblesError):
    """Represent an unsupported or malformed wire-protocol operation."""

    default_code = ErrorCode.UNSUPPORTED_PROTOCOL


class FileTransferError(BlueBubblesError):
    """Represent a permanent or temporary transfer failure."""


class LocalStorageError(BlueBubblesError):
    """Represent a Windows client's encrypted local-storage failure."""

    default_code = ErrorCode.LOCAL_DATABASE_CORRUPT


class ConfigurationError(BlueBubblesError, ValueError):
    """Represent invalid or unsafe application configuration."""

    default_code = ErrorCode.CONFIGURATION_INVALID

    def __init__(self, user_message: str) -> None:
        """Preserve the established configuration ``ValueError(message)`` API."""
        super().__init__(user_message=user_message)


class WorkerError(BlueBubblesError):
    """Represent a monitored background-worker failure."""

    default_code = ErrorCode.WORKER_FAILED


class InternalApplicationError(BlueBubblesError):
    """Represent a safely translated internal application failure."""

    default_code = ErrorCode.INTERNAL_SERVER_ERROR
