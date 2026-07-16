"""Tests for pure shared request-validation helpers."""

import base64
from uuid import uuid4

import pytest

from bluebubbles.shared.validation import (
    normalise_display_text,
    validate_base64_length,
    validate_message_type,
    validate_protocol_version,
    validate_safe_display_filename,
    validate_uuid_list,
)


def test_uuid_list_is_non_empty_and_unique() -> None:
    identifier = uuid4()
    assert validate_uuid_list([identifier]) == (identifier,)
    with pytest.raises(ValueError, match="At least"):
        validate_uuid_list([])
    with pytest.raises(ValueError, match="Duplicate"):
        validate_uuid_list([identifier, identifier])


def test_display_text_is_normalised_and_bounded() -> None:
    assert (
        normalise_display_text("  Blue   Bubbles ", maximum_length=20) == "Blue Bubbles"
    )
    with pytest.raises(ValueError, match="empty"):
        normalise_display_text("  ", maximum_length=20)
    with pytest.raises(ValueError, match="exceed"):
        normalise_display_text("long", maximum_length=3)


def test_base64_validation_checks_encoding_and_decoded_length() -> None:
    encoded = base64.b64encode(b"abc").decode()
    assert validate_base64_length(encoded, maximum_decoded_bytes=3) == encoded
    with pytest.raises(ValueError, match="valid base64"):
        validate_base64_length("!", maximum_decoded_bytes=3)
    with pytest.raises(ValueError, match="cannot exceed"):
        validate_base64_length(encoded, maximum_decoded_bytes=2)


@pytest.mark.parametrize(
    "filename", ["../secret", "folder/file", "folder\\file", "..", "bad\x00name"]
)
def test_filename_validation_rejects_paths(filename: str) -> None:
    with pytest.raises(ValueError):
        validate_safe_display_filename(filename)
    assert validate_safe_display_filename("report.pdf") == "report.pdf"


def test_allowlist_and_protocol_validation() -> None:
    assert validate_protocol_version(1) == 1
    assert validate_message_type("text", allowed=["text"]) == "text"
    with pytest.raises(ValueError, match="Unsupported"):
        validate_message_type("html", allowed=["text"])
