"""Task 15 upload/download coordination and failure-path evidence."""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from bluebubbles.client.security.attachment_crypto import (
    AttachmentCryptoContext,
    AttachmentEncryptionService,
    AuthenticatedAttachmentChunk,
)
from bluebubbles.client.services.attachments import (
    BandwidthLimiter,
    FileTransferService,
    FileValidator,
)
from bluebubbles.shared.errors.exceptions import FileTransferError
from bluebubbles.shared.models.attachments import (
    AttachmentRecipientKeyRequest,
    AttachmentRecipientKeyResponse,
    AttachmentResponse,
    AttachmentStatus,
    AuthorisedAttachmentResponse,
    InitialiseUploadRequest,
    InitialiseUploadResponse,
    UploadChunkResponse,
    UploadStatusResponse,
)


class Token:
    """Deterministic cancellation boundary for transfer tests."""

    def __init__(self, cancelled: bool = False) -> None:
        self.cancelled = cancelled

    def raise_if_cancelled(self) -> None:
        if self.cancelled:
            raise FileTransferError(user_message="cancelled")


class MemoryTransferApi:
    """Keep only synthetic encrypted chunks for client orchestration tests."""

    def __init__(self) -> None:
        self.upload_id = uuid4()
        self.uploaded: list[int] = []
        self.cancelled = False
        self.download_metadata: AuthorisedAttachmentResponse | None = None
        self.download_chunks: tuple[AuthenticatedAttachmentChunk, ...] = ()

    async def initialise_upload(
        self, request: InitialiseUploadRequest
    ) -> InitialiseUploadResponse:
        return InitialiseUploadResponse(
            attachment_id=request.attachment_id,
            upload_id=self.upload_id,
            chunk_size=request.chunk_size,
            expected_chunk_count=request.chunk_count or 1,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

    async def get_upload_status(self, upload_id: UUID) -> UploadStatusResponse:
        assert upload_id == self.upload_id
        return UploadStatusResponse(
            upload_id=upload_id,
            status=AttachmentStatus.UPLOADING,
            received_bytes=1,
            total_bytes=2,
            received_chunks=(0,),
            missing_chunks=(1,),
        )

    async def upload_chunk(
        self, upload_id: UUID, chunk: AuthenticatedAttachmentChunk
    ) -> UploadChunkResponse:
        self.uploaded.append(chunk.index)
        return UploadChunkResponse(
            upload_id=upload_id,
            chunk_index=chunk.index,
            received_bytes=len(chunk.ciphertext),
            total_received_bytes=len(chunk.ciphertext),
            received_chunk_count=1,
            expected_chunk_count=2,
            is_complete=True,
        )

    async def complete_upload(self, upload_id: UUID) -> AttachmentResponse:
        if self.cancelled:
            raise FileTransferError(user_message="cancelled")
        assert upload_id == self.upload_id
        assert self.download_metadata is not None
        return AttachmentResponse(
            **self.download_metadata.model_dump(
                exclude={
                    "download_url",
                    "recipient_key",
                    "encrypted_metadata",
                    "metadata_nonce",
                    "metadata_authentication_tag",
                }
            )
        )

    async def cancel_upload(self, upload_id: UUID) -> None:
        assert upload_id == self.upload_id
        self.cancelled = True

    async def get_attachment(self, attachment_id: UUID) -> AuthorisedAttachmentResponse:
        assert self.download_metadata is not None
        assert attachment_id == self.download_metadata.id
        return self.download_metadata

    async def download_chunk(
        self, attachment_id: UUID, chunk_index: int
    ) -> AuthenticatedAttachmentChunk:
        assert self.download_metadata is not None
        assert attachment_id == self.download_metadata.id
        return self.download_chunks[chunk_index]


def recipient_key(attachment_id: UUID | None = None) -> AttachmentRecipientKeyResponse:
    """Build a structurally valid synthetic recipient envelope."""
    return AttachmentRecipientKeyResponse(
        attachment_id=attachment_id or uuid4(),
        recipient_id=uuid4(),
        key_version=1,
        encrypted_key=base64.b64encode(b"wrapped").decode(),
        ephemeral_public_key=base64.b64encode(bytes(32)).decode(),
        nonce=base64.b64encode(bytes(12)).decode(),
    )


@pytest.mark.asyncio
async def test_upload_resumes_from_missing_chunk_and_revalidates_disk(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"a" * 300_000)
    api = MemoryTransferApi()
    service = FileTransferService(
        api,
        AttachmentEncryptionService(),
        FileValidator(),
        tmp_path / "temporary",
        chunk_size=262_144,
    )
    prepared = await service.prepare_upload(source, uuid4(), uuid4(), Token())
    api.download_metadata = AuthorisedAttachmentResponse(
        id=prepared.attachment_id,
        conversation_id=prepared.conversation_id,
        uploaded_by=prepared.uploader_id,
        filename=prepared.filename,
        media_type=prepared.media_type,
        encrypted_size=prepared.encrypted_size,
        original_size=prepared.plaintext_size,
        chunk_count=2,
        status=AttachmentStatus.COMPLETE,
        created_at=datetime.now(UTC),
        download_url="/chunks/{chunk_index}",
        recipient_key=recipient_key(prepared.attachment_id),
    )
    envelope = AttachmentRecipientKeyRequest(
        recipient_id=uuid4(),
        key_version=1,
        encrypted_key=base64.b64encode(b"wrapped").decode(),
        ephemeral_public_key=base64.b64encode(bytes(32)).decode(),
        nonce=base64.b64encode(bytes(12)).decode(),
    )
    response = await service.upload(prepared, (envelope,))
    assert response.id == prepared.attachment_id
    assert api.uploaded == [1]
    prepared.chunks[1].path.write_bytes(b"damaged")
    with pytest.raises(FileTransferError):
        prepared.chunks[1].load()


@pytest.mark.asyncio
async def test_download_round_trip_collision_and_failure_cleanup(
    tmp_path: Path,
) -> None:
    crypto = AttachmentEncryptionService()
    key = crypto.generate_file_key()
    attachment_id, conversation_id, uploader_id = uuid4(), uuid4(), uuid4()
    plaintext_chunks = (b"first ", b"second")
    context = AttachmentCryptoContext(
        attachment_id, conversation_id, uploader_id, len(plaintext_chunks)
    )
    chunks = tuple(
        crypto.encrypt_chunk(key, context, index, plaintext)
        for index, plaintext in enumerate(plaintext_chunks)
    )
    plaintext = b"".join(plaintext_chunks)
    import hashlib

    nonce, encrypted_metadata, tag = crypto.encrypt_metadata(
        key,
        context,
        {
            "plaintext_size": len(plaintext),
            "plaintext_sha256": hashlib.sha256(plaintext).hexdigest(),
        },
    )
    api = MemoryTransferApi()
    api.download_chunks = chunks
    api.download_metadata = AuthorisedAttachmentResponse(
        id=attachment_id,
        conversation_id=conversation_id,
        uploaded_by=uploader_id,
        filename="report.txt",
        media_type="text/plain",
        encrypted_size=len(plaintext),
        original_size=len(plaintext),
        chunk_count=2,
        status=AttachmentStatus.COMPLETE,
        created_at=datetime.now(UTC),
        download_url="/chunks/{chunk_index}",
        recipient_key=recipient_key(attachment_id),
        encrypted_metadata=base64.b64encode(encrypted_metadata).decode(),
        metadata_nonce=base64.b64encode(nonce).decode(),
        metadata_authentication_tag=base64.b64encode(tag).decode(),
    )
    service = FileTransferService(api, crypto, FileValidator(), tmp_path / "temporary")
    destination = tmp_path / "report.txt"
    destination.write_text("existing", encoding="utf-8")
    completed = await service.download(attachment_id, destination, key, Token())
    assert completed.name == "report (1).txt"
    assert completed.read_bytes() == plaintext
    api.download_chunks = (chunks[1], chunks[0])
    with pytest.raises(FileTransferError):
        await service.download(attachment_id, tmp_path / "bad.txt", key, Token())
    assert not (tmp_path / "bad.txt.bluebubbles-partial").exists()


@pytest.mark.asyncio
async def test_validator_limiter_and_cancelled_preparation(tmp_path: Path) -> None:
    validator = FileValidator()
    with pytest.raises(FileTransferError):
        validator.validate(tmp_path / "missing", 10)
    empty = tmp_path / "empty"
    empty.write_bytes(b"")
    with pytest.raises(FileTransferError):
        validator.validate(empty, 10)
    large = tmp_path / "large"
    large.write_bytes(b"large")
    with pytest.raises(FileTransferError):
        validator.validate(large, 1)
    with pytest.raises(ValueError):
        BandwidthLimiter(0)
    limiter = BandwidthLimiter(None)
    with pytest.raises(ValueError):
        await limiter.consume(-1)
    service = FileTransferService(
        MemoryTransferApi(),
        AttachmentEncryptionService(),
        validator,
        tmp_path / "temporary",
        chunk_size=262_144,
    )
    with pytest.raises(FileTransferError):
        await service.prepare_upload(large, uuid4(), uuid4(), Token(True))
    assert not list((tmp_path / "temporary").glob("*"))
