"""Tests for shared application and protocol version compatibility."""

import pytest

from bluebubbles.shared.versioning import (
    ProtocolVersion,
    SemanticVersion,
    compare_versions,
    is_client_supported,
    parse_version,
    select_highest_common_protocol,
)


def test_semantic_version_round_trip_and_precedence() -> None:
    version = parse_version("1.2.3-alpha.1+build.7")

    assert str(version) == "1.2.3-alpha.1+build.7"
    assert compare_versions(version, "1.2.3") == -1
    assert compare_versions("1.2.3+one", "1.2.3+two") == 0
    assert compare_versions("2.0.0", "1.99.99") == 1


@pytest.mark.parametrize("value", ["1", "01.2.3", "1.2.3-01", "1.2.3+", " 1.2.3"])
def test_parse_version_rejects_malformed_values(value: str) -> None:
    with pytest.raises(ValueError):
        parse_version(value)


def test_version_value_objects_validate_numbers_and_types() -> None:
    with pytest.raises(ValueError, match="negative"):
        SemanticVersion(-1, 0, 0)
    with pytest.raises(ValueError, match="positive"):
        ProtocolVersion(0)
    with pytest.raises(ValueError, match="positive"):
        ProtocolVersion(True)
    assert SemanticVersion(1, 0, 0).__lt__(object()) is NotImplemented


def test_protocol_selection_and_client_support() -> None:
    assert select_highest_common_protocol(
        [1, 2], [2, ProtocolVersion(3)]
    ) == ProtocolVersion(2)
    assert select_highest_common_protocol([1], [2]) is None
    assert is_client_supported("1.2.0", "1.1.0", maximum_major=1)
    assert not is_client_supported("2.0.0", "1.1.0", maximum_major=1)
