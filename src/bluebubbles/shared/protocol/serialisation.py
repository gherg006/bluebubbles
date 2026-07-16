"""Deterministic JSON, timestamp, and UUID serialisation helpers."""

import base64
import json
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


def canonical_timestamp(value: datetime) -> str:
    """Return a UTC RFC3339 timestamp with exactly six fractional digits."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Canonical timestamps must be timezone-aware")
    return (
        value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    )


def canonical_uuid(value: UUID) -> str:
    """Return the lowercase hyphenated representation of a UUID."""
    return str(value)


def canonical_json_bytes(value: object) -> bytes:
    """Serialise supported values as stable UTF-8 JSON bytes.

    Mappings are key-sorted, whitespace is omitted, and non-finite floats are rejected.

    Raises:
        TypeError: If a value cannot be represented by the canonical contract.
        ValueError: If a float is not finite or a timestamp is naive.
    """
    normalised = _normalise(value)
    return json.dumps(
        normalised,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _normalise(value: object) -> Any:
    if isinstance(value, BaseModel):
        return _normalise(value.model_dump(mode="python"))
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("Canonical JSON mapping keys must be strings")
        return {key: _normalise(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_normalise(item) for item in value]
    if isinstance(value, datetime):
        return canonical_timestamp(value)
    if isinstance(value, UUID):
        return canonical_uuid(value)
    if isinstance(value, Enum):
        return _normalise(value.value)
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    if value is None or isinstance(value, str | int | float | bool):
        return value
    raise TypeError(f"Unsupported canonical JSON type: {type(value).__name__}")
