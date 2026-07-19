"""Task 22 generated-input tests for parsing, paths, and canonical contracts."""

import base64
import json
import string
from pathlib import Path
from uuid import UUID

import pytest
from hypothesis import given
from hypothesis import strategies as st

from bluebubbles.deployment import ArtifactRecord
from bluebubbles.server.repositories.types import decode_cursor, encode_cursor
from bluebubbles.server.storage.files import AttachmentPathBuilder
from bluebubbles.shared.constants import MAX_FILENAME_LENGTH
from bluebubbles.shared.protocol.serialisation import canonical_json_bytes
from bluebubbles.shared.security.fingerprints import (
    format_fingerprint,
    validate_fingerprint,
)
from bluebubbles.shared.validation import (
    normalise_display_text,
    validate_base64_length,
    validate_safe_display_filename,
)


@given(st.binary(min_size=0, max_size=2048))
def test_base64_round_trip_accepts_every_payload_inside_exact_limits(
    data: bytes,
) -> None:
    encoded = base64.b64encode(data).decode("ascii")
    assert (
        validate_base64_length(
            encoded,
            minimum_decoded_bytes=len(data),
            maximum_decoded_bytes=len(data),
        )
        == encoded
    )


@given(st.binary(min_size=1, max_size=256))
def test_base64_rejects_every_payload_one_byte_outside_limits(data: bytes) -> None:
    encoded = base64.b64encode(data).decode("ascii")
    with pytest.raises(ValueError, match="cannot exceed"):
        validate_base64_length(encoded, maximum_decoded_bytes=len(data) - 1)
    with pytest.raises(ValueError, match="at least"):
        validate_base64_length(
            encoded,
            minimum_decoded_bytes=len(data) + 1,
            maximum_decoded_bytes=len(data) + 1,
        )


@given(st.text(min_size=1, max_size=MAX_FILENAME_LENGTH))
def test_accepted_filename_is_single_component_bounded_and_control_free(
    value: str,
) -> None:
    try:
        result = validate_safe_display_filename(value)
    except ValueError:
        return
    assert result == value
    assert 1 <= len(result) <= MAX_FILENAME_LENGTH
    assert "/" not in result and "\\" not in result
    assert result not in {".", ".."}
    assert all(ord(character) >= 32 and ord(character) != 127 for character in result)


@given(st.text(alphabet="\x00\x01\t\n\r\x1f\x7f", min_size=1, max_size=20))
def test_display_text_rejects_every_ascii_control_character(value: str) -> None:
    with pytest.raises(ValueError, match="control"):
        normalise_display_text(f"safe{value}text", maximum_length=100)


@given(
    st.dictionaries(
        st.text(alphabet=string.ascii_letters, min_size=1, max_size=12),
        st.one_of(st.none(), st.booleans(), st.integers(), st.text(max_size=20)),
        max_size=20,
    )
)
def test_canonical_json_is_independent_of_dictionary_insertion_order(
    value: dict[str, object],
) -> None:
    reversed_value = dict(reversed(tuple(value.items())))
    serialised = canonical_json_bytes(value)
    assert serialised == canonical_json_bytes(reversed_value)
    assert json.loads(serialised) == value


@given(
    st.lists(
        st.one_of(st.none(), st.booleans(), st.integers(), st.text(max_size=50)),
        min_size=1,
        max_size=10,
    )
)
def test_repository_cursor_round_trip_preserves_every_supported_scalar(
    values: list[object],
) -> None:
    cursor = encode_cursor(*values)
    assert decode_cursor(cursor, len(values)) == tuple(values)


@given(st.binary(min_size=32, max_size=32))
def test_fingerprint_format_is_canonical_and_validated(digest: bytes) -> None:
    result = format_fingerprint(digest)
    assert validate_fingerprint(result) == result
    assert len(result) == 79


@given(st.integers(min_value=0, max_value=2**31 - 1))
def test_generated_attachment_chunk_path_remains_inside_root(
    chunk_index: int,
) -> None:
    root = Path.cwd() / "build" / "property-test" / "attachments"
    temporary = Path.cwd() / "build" / "property-test" / "temporary"
    builder = AttachmentPathBuilder(root, temporary)
    path = builder.attachment_chunk_path(UUID(int=0), chunk_index)
    assert path.is_relative_to(root.resolve())
    assert path.name == f"{chunk_index:08d}.chunk"


@given(
    st.text(
        alphabet=string.ascii_letters + string.digits + "._-/\\",
        min_size=1,
        max_size=100,
    )
)
def test_accepted_release_artifact_path_cannot_escape_or_use_host_separator(
    value: str,
) -> None:
    try:
        artifact = ArtifactRecord(path=value, size_bytes=0, sha256="0" * 64)
    except ValueError:
        return
    assert not artifact.path.startswith("/")
    assert "\\" not in artifact.path
    assert ".." not in artifact.path.split("/")
