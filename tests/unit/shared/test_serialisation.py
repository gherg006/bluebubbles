"""Tests for deterministic protocol serialisation."""

import math
from datetime import UTC, datetime, timedelta, timezone
from enum import StrEnum
from uuid import UUID

import pytest

from bluebubbles.shared.protocol.serialisation import (
    canonical_json_bytes,
    canonical_timestamp,
    canonical_uuid,
)


class ExampleEnum(StrEnum):
    """Provide an enum fixture for canonical JSON tests."""

    VALUE = "value"


def test_canonical_json_is_stable_and_supports_wire_value_types() -> None:
    identifier = UUID("12345678-1234-5678-1234-567812345678")
    value = {
        "z": [ExampleEnum.VALUE, b"binary", identifier],
        "a": datetime(2026, 1, 2, 3, 4, 5, 6, tzinfo=UTC),
    }

    assert canonical_json_bytes(value) == (
        b'{"a":"2026-01-02T03:04:05.000006Z",'
        b'"z":["value","YmluYXJ5","12345678-1234-5678-1234-567812345678"]}'
    )
    assert canonical_uuid(identifier) == str(identifier)


def test_timestamp_is_normalised_to_utc_and_requires_timezone() -> None:
    value = datetime(2026, 1, 1, 1, tzinfo=timezone(timedelta(hours=1)))
    assert canonical_timestamp(value) == "2026-01-01T00:00:00.000000Z"
    with pytest.raises(ValueError, match="timezone-aware"):
        canonical_timestamp(datetime(2026, 1, 1))


def test_canonical_json_rejects_unsupported_or_unsafe_values() -> None:
    with pytest.raises(TypeError, match="mapping keys"):
        canonical_json_bytes({1: "value"})
    with pytest.raises(TypeError, match="Unsupported"):
        canonical_json_bytes(object())
    with pytest.raises(ValueError):
        canonical_json_bytes(math.nan)
