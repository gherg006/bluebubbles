"""Pure validation helpers shared at network contract boundaries."""

import base64
import binascii
import re
from collections.abc import Iterable
from pathlib import PurePath
from uuid import UUID

from bluebubbles.shared.constants import MAX_FILENAME_LENGTH
from bluebubbles.shared.versioning import ProtocolVersion

_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")


def validate_uuid_list(values: Iterable[UUID]) -> tuple[UUID, ...]:
    """Return a non-empty, duplicate-free UUID tuple."""
    result = tuple(values)
    if not result:
        raise ValueError("At least one identifier is required")
    if len(set(result)) != len(result):
        raise ValueError("Duplicate identifiers are not allowed")
    return result


def normalise_display_text(value: str, *, maximum_length: int) -> str:
    """Trim display text and reject control characters or excessive length."""
    if _CONTROL_CHARACTERS.search(value):
        raise ValueError("Text cannot contain control characters")
    normalised = " ".join(value.split())
    if not normalised:
        raise ValueError("Text cannot be empty")
    if len(normalised) > maximum_length:
        raise ValueError(f"Text cannot exceed {maximum_length} characters")
    return normalised


def validate_base64_length(
    value: str,
    *,
    maximum_decoded_bytes: int,
    minimum_decoded_bytes: int = 0,
) -> str:
    """Validate canonical base64 and its decoded byte length."""
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("Value must be valid base64") from error
    if len(decoded) < minimum_decoded_bytes:
        raise ValueError(
            f"Decoded value must contain at least {minimum_decoded_bytes} bytes"
        )
    if len(decoded) > maximum_decoded_bytes:
        raise ValueError(f"Decoded value cannot exceed {maximum_decoded_bytes} bytes")
    return value


def validate_protocol_version(value: int) -> int:
    """Validate and return a positive protocol version integer."""
    return ProtocolVersion(value).value


def validate_safe_display_filename(value: str) -> str:
    """Return a safe display-only filename with no path components."""
    if not value or len(value) > MAX_FILENAME_LENGTH:
        raise ValueError("Filename has an invalid length")
    if value in {".", ".."} or PurePath(value).name != value:
        raise ValueError("Filename must not contain a path")
    if "/" in value or "\\" in value or _CONTROL_CHARACTERS.search(value):
        raise ValueError("Filename contains unsafe characters")
    return value


def validate_message_type(value: str, *, allowed: Iterable[str]) -> str:
    """Return ``value`` when it is in the explicit message-type allowlist."""
    if value not in frozenset(allowed):
        raise ValueError("Unsupported message type")
    return value
