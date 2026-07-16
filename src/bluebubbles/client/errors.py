"""Windows-client error presentation models and safe message catalogue."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from bluebubbles.shared.errors import ErrorCode, ErrorSeverity, get_error_metadata


@dataclass(frozen=True, slots=True)
class ErrorDisplayContext:
    """Provide non-sensitive context used to choose client wording."""

    correlation_id: UUID | None = None
    retryable_override: bool | None = None


@dataclass(frozen=True, slots=True)
class ClientError:
    """Represent an error ready for client ViewModel handling and display."""

    code: str
    title: str
    message: str
    severity: ErrorSeverity
    retryable: bool
    suggested_action: str | None
    correlation_id: UUID | None
    technical_details_available: bool


class ErrorMessageCatalog:
    """Map stable public error codes to plain-English client content."""

    def get_message(self, code: str, context: ErrorDisplayContext) -> ClientError:
        """Return known wording or a safe fallback while preserving unknown codes."""
        try:
            known_code = ErrorCode(code)
        except ValueError:
            return ClientError(
                code=code,
                title="Unable to complete action",
                message="BlueBubbles could not complete this action.",
                severity=ErrorSeverity.ERROR,
                retryable=context.retryable_override or False,
                suggested_action=(
                    "Try again. If the problem continues, contact the helpdesk."
                ),
                correlation_id=context.correlation_id,
                technical_details_available=context.correlation_id is not None,
            )
        metadata = get_error_metadata(known_code)
        retryable = metadata.retry not in {
            metadata.retry.NEVER,
            metadata.retry.USER_ACTION_REQUIRED,
        }
        if context.retryable_override is not None:
            retryable = context.retryable_override
        return ClientError(
            code=known_code.value,
            title=metadata.title,
            message=metadata.default_message,
            severity=metadata.severity,
            retryable=retryable,
            suggested_action=metadata.suggested_action,
            correlation_id=context.correlation_id,
            technical_details_available=context.correlation_id is not None,
        )
