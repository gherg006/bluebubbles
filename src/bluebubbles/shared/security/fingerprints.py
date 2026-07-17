"""Consistent SHA-256 public-key fingerprint creation and display."""

import hashlib
import re

_CANONICAL = re.compile(r"^[0-9A-F]{4}(?:-[0-9A-F]{4}){15}$")


def calculate_public_key_fingerprint(
    public_key: bytes,
    *,
    algorithm: str | None = None,
    key_type: str | None = None,
    key_version: int | None = None,
) -> str:
    """Return a canonical raw or identity-bound public-key fingerprint."""
    if not public_key:
        raise ValueError("Public key cannot be empty")
    qualifiers = (algorithm, key_type, key_version)
    if all(value is None for value in qualifiers):
        payload = public_key
    elif algorithm and key_type and key_version is not None and key_version > 0:
        payload = b"\x00".join(
            (
                algorithm.encode("ascii"),
                key_type.encode("ascii"),
                key_version.to_bytes(8, "big"),
                public_key,
            )
        )
    else:
        raise ValueError("Complete identity-key fingerprint context is required")
    return format_fingerprint(hashlib.sha256(payload).hexdigest())


def format_fingerprint(value: str | bytes) -> str:
    """Format a 32-byte digest or 64 hexadecimal characters canonically."""
    hexadecimal = value.hex() if isinstance(value, bytes) else value.replace("-", "")
    if not re.fullmatch(r"[0-9A-Fa-f]{64}", hexadecimal):
        raise ValueError("Fingerprint must contain exactly 32 bytes")
    upper = hexadecimal.upper()
    return "-".join(upper[index : index + 4] for index in range(0, 64, 4))


def validate_fingerprint(value: str) -> str:
    """Validate and return a canonical fingerprint string."""
    if _CANONICAL.fullmatch(value) is None:
        raise ValueError("Fingerprint is not in canonical format")
    return value
