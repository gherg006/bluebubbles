"""Focused client attachment encryption and preparation evidence."""

from __future__ import annotations

import base64
from pathlib import Path
from uuid import uuid4

import pytest

from bluebubbles.client.security.attachment_crypto import (
    AttachmentCryptoContext,
    AttachmentEncryptionService,
    AuthenticatedAttachmentChunk,
)
from bluebubbles.client.services.attachments import (
    FileTransferService,
    FileValidator,
)
from bluebubbles.shared.errors.exceptions import CryptographyError
from bluebubbles.shared.models.attachments import AttachmentRecipientKeyRequest


class _Token:
    def raise_if_cancelled(self) -> None:
        return


class _UnusedApi:
    pass


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def test_contextual_random_nonce_chunk_round_trip_and_tamper_rejection() -> None:
    service = AttachmentEncryptionService()
    key = service.generate_file_key()
    context = AttachmentCryptoContext(uuid4(), uuid4(), uuid4(), 2)
    first = service.encrypt_chunk(key, context, 0, b"first")
    second = service.encrypt_chunk(key, context, 1, b"second")
    assert len(first.nonce) == 12
    assert first.nonce != second.nonce
    assert service.decrypt_chunk(key, context, first) == b"first"
    damaged = AuthenticatedAttachmentChunk(
        first.index,
        first.nonce,
        bytes([first.ciphertext[0] ^ 1]) + first.ciphertext[1:],
        first.authentication_tag,
        first.plaintext_length,
        first.encrypted_hash,
    )
    with pytest.raises(CryptographyError):
        service.decrypt_chunk(key, context, damaged)
    wrong_context = AttachmentCryptoContext(
        uuid4(), context.conversation_id, context.uploader_id, 2
    )
    with pytest.raises(CryptographyError):
        service.decrypt_chunk(key, wrong_context, first)


def test_metadata_is_purpose_separated_and_authenticated() -> None:
    service = AttachmentEncryptionService()
    key = service.generate_file_key()
    context = AttachmentCryptoContext(uuid4(), uuid4(), uuid4(), 1)
    nonce, ciphertext, tag = service.encrypt_metadata(
        key, context, {"plaintext_sha256": "synthetic", "format_version": 1}
    )
    assert b"synthetic" not in ciphertext
    assert (
        service.decrypt_metadata(key, context, nonce, ciphertext, tag)[
            "plaintext_sha256"
        ]
        == "synthetic"
    )
    with pytest.raises(CryptographyError):
        service.decrypt_metadata(key, context, nonce, ciphertext, bytes(16))


@pytest.mark.asyncio
async def test_streaming_preparation_creates_ciphertext_only_resumable_chunks(
    tmp_path: Path,
) -> None:
    source = tmp_path / "report.bin"
    marker = b"known-plaintext-marker-"
    source.write_bytes(marker * 20_000)
    service = FileTransferService(
        _UnusedApi(),  # type: ignore[arg-type]
        AttachmentEncryptionService(),
        FileValidator(),
        tmp_path / "transfers",
        chunk_size=262_144,
    )
    prepared = await service.prepare_upload(source, uuid4(), uuid4(), _Token())
    assert len(prepared.chunks) == 2
    assert all(
        marker not in path.read_bytes() for path in prepared.directory.glob("*.chunk")
    )
    recipient = AttachmentRecipientKeyRequest(
        recipient_id=uuid4(),
        key_version=1,
        encrypted_key=_b64(b"wrapped"),
        ephemeral_public_key=_b64(bytes(32)),
        nonce=_b64(bytes(12)),
    )
    request = service.build_initialise_request(prepared, (recipient,))
    assert request.attachment_id == prepared.attachment_id
    assert request.chunk_count == 2
    assert request.encrypted_metadata is not None


def test_filename_rules_remove_paths_and_reserved_windows_names() -> None:
    validator = FileValidator()
    assert validator.sanitise_display_filename("../report.pdf") == ".._report.pdf"
    assert validator.sanitise_display_filename("CON") == "CON_file"
