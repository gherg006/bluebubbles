"""Client-side encrypted attachment preparation and resumable upload coordination."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import mimetypes
import os
import re
import secrets
import shutil
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic
from typing import Protocol
from uuid import UUID, uuid4

from bluebubbles.client.security.attachment_crypto import (
    AttachmentCryptoContext,
    AttachmentEncryptionService,
    AuthenticatedAttachmentChunk,
    CancellationToken,
)
from bluebubbles.shared.errors.exceptions import FileTransferError, ValidationError
from bluebubbles.shared.models.attachments import (
    AttachmentRecipientKeyRequest,
    AttachmentResponse,
    AuthorisedAttachmentResponse,
    InitialiseUploadRequest,
    InitialiseUploadResponse,
    UploadChunkResponse,
    UploadStatusResponse,
)
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    HashAlgorithm,
)

_RESERVED_WINDOWS = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.I)


class AttachmentTransferApi(Protocol):
    """Define ciphertext-only network operations used by the transfer service."""

    async def initialise_upload(
        self, request: InitialiseUploadRequest
    ) -> InitialiseUploadResponse: ...
    async def get_upload_status(self, upload_id: UUID) -> UploadStatusResponse: ...
    async def upload_chunk(
        self, upload_id: UUID, chunk: AuthenticatedAttachmentChunk
    ) -> UploadChunkResponse: ...
    async def complete_upload(self, upload_id: UUID) -> AttachmentResponse: ...
    async def cancel_upload(self, upload_id: UUID) -> None: ...
    async def get_attachment(
        self, attachment_id: UUID
    ) -> AuthorisedAttachmentResponse: ...
    async def download_chunk(
        self, attachment_id: UUID, chunk_index: int
    ) -> AuthenticatedAttachmentChunk: ...


class FileValidator:
    """Validate and sanitise a selected source before encryption begins."""

    @staticmethod
    def sanitise_display_filename(filename: str) -> str:
        value = filename.strip().replace("/", "_").replace("\\", "_")
        value = "".join(character for character in value if ord(character) >= 32)
        if not value or value in {".", ".."} or "\x00" in value:
            raise ValidationError(user_message="The file name is not valid.")
        value = value[:255].rstrip(" .")
        if _RESERVED_WINDOWS.match(value):
            value += "_file"
        return value

    def validate(self, path: Path, maximum_size: int) -> tuple[int, str, str]:
        """Return size, safe filename and advisory MIME type for a regular file."""
        try:
            resolved = path.resolve(strict=True)
            stat = resolved.stat()
        except OSError as error:
            raise FileTransferError(
                user_message="The selected file cannot be read."
            ) from error
        if not resolved.is_file() or stat.st_size <= 0:
            raise FileTransferError(user_message="Select a non-empty regular file.")
        if stat.st_size > maximum_size:
            raise FileTransferError(user_message="The selected file is too large.")
        try:
            with resolved.open("rb"):
                pass
        except OSError as error:
            raise FileTransferError(
                user_message="The selected file cannot be read."
            ) from error
        return (
            stat.st_size,
            self.sanitise_display_filename(path.name),
            mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        )


class BandwidthLimiter:
    """Apply an asynchronous average bytes-per-second transfer ceiling."""

    def __init__(self, bytes_per_second: int | None) -> None:
        if bytes_per_second is not None and bytes_per_second <= 0:
            raise ValueError("Bandwidth limit must be positive")
        self._rate = bytes_per_second
        self._started = monotonic()
        self._consumed = 0

    async def consume(self, byte_count: int) -> None:
        if byte_count < 0:
            raise ValueError("Byte count cannot be negative")
        if self._rate is None:
            return
        self._consumed += byte_count
        delay = self._consumed / self._rate - (monotonic() - self._started)
        if delay > 0:
            await asyncio.sleep(delay)


@dataclass(frozen=True, slots=True)
class PreparedEncryptedAttachment:
    """Hold resumable ciphertext paths and the client-only master key."""

    attachment_id: UUID
    conversation_id: UUID
    uploader_id: UUID
    source_path: Path
    directory: Path
    filename: str
    media_type: str
    plaintext_size: int
    encrypted_size: int
    chunk_size: int
    chunks: tuple[PreparedEncryptedChunk, ...]
    plaintext_sha256: str
    encrypted_sha256: bytes
    metadata_nonce: bytes
    metadata_ciphertext: bytes
    metadata_tag: bytes
    master_key: bytes = field(repr=False)


@dataclass(frozen=True, slots=True)
class PreparedEncryptedChunk:
    """Reference one encrypted chunk without retaining its body in memory."""

    index: int
    path: Path
    nonce: bytes = field(repr=False)
    authentication_tag: bytes = field(repr=False)
    plaintext_length: int
    encrypted_hash: bytes = field(repr=False)
    encrypted_size: int

    def load(self) -> AuthenticatedAttachmentChunk:
        """Load and revalidate one bounded chunk immediately before transfer."""
        ciphertext = self.path.read_bytes()
        if len(ciphertext) != self.encrypted_size:
            raise FileTransferError(
                user_message="The prepared attachment chunk is incomplete."
            )
        digest = hashlib.sha256(ciphertext).digest()
        if not secrets.compare_digest(digest, self.encrypted_hash):
            raise FileTransferError(
                user_message="The prepared attachment chunk is damaged."
            )
        return AuthenticatedAttachmentChunk(
            self.index,
            self.nonce,
            ciphertext,
            self.authentication_tag,
            self.plaintext_length,
            self.encrypted_hash,
        )


class FileTransferService:
    """Prepare bounded ciphertext chunks and upload only server-missing indices."""

    def __init__(
        self,
        api: AttachmentTransferApi,
        crypto: AttachmentEncryptionService,
        validator: FileValidator,
        temporary_root: Path,
        *,
        maximum_plaintext_size: int = 2_147_483_648,
        chunk_size: int = 1_048_576,
        bandwidth_limit: int | None = None,
    ) -> None:
        self._api = api
        self._crypto = crypto
        self._validator = validator
        self._temporary_root = temporary_root.resolve()
        self._maximum_size = maximum_plaintext_size
        self._chunk_size = chunk_size
        self._bandwidth_limit = bandwidth_limit

    async def prepare_upload(
        self,
        path: Path,
        conversation_id: UUID,
        uploader_id: UUID,
        cancellation_token: CancellationToken,
    ) -> PreparedEncryptedAttachment:
        size, filename, media_type = self._validator.validate(path, self._maximum_size)
        initial_stat = path.stat()
        attachment_id = uuid4()
        count = (size + self._chunk_size - 1) // self._chunk_size
        context = AttachmentCryptoContext(
            attachment_id, conversation_id, uploader_id, count
        )
        master_key = self._crypto.generate_file_key()
        directory = (self._temporary_root / str(attachment_id)).resolve()
        if not directory.is_relative_to(self._temporary_root):
            raise FileTransferError(user_message="The transfer path is invalid.")
        await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=False)
        plaintext_hash = hashlib.sha256()
        encrypted_hash = hashlib.sha256()
        chunks: list[PreparedEncryptedChunk] = []
        try:
            with path.open("rb") as source:
                for index in range(count):
                    cancellation_token.raise_if_cancelled()
                    plaintext = source.read(self._chunk_size)
                    plaintext_hash.update(plaintext)
                    chunk = self._crypto.encrypt_chunk(
                        master_key, context, index, plaintext
                    )
                    encrypted_hash.update(
                        chunk.nonce + chunk.ciphertext + chunk.authentication_tag
                    )
                    target = directory / f"{index:08d}.chunk"
                    with target.open("xb") as stream:
                        stream.write(chunk.ciphertext)
                        stream.flush()
                        os.fsync(stream.fileno())
                    chunks.append(
                        PreparedEncryptedChunk(
                            chunk.index,
                            target,
                            chunk.nonce,
                            chunk.authentication_tag,
                            chunk.plaintext_length,
                            chunk.encrypted_hash,
                            len(chunk.ciphertext),
                        )
                    )
                    plaintext = b""
            final_stat = path.stat()
            if (
                final_stat.st_size != initial_stat.st_size
                or final_stat.st_mtime_ns != initial_stat.st_mtime_ns
            ):
                raise FileTransferError(
                    user_message="The selected file changed during preparation."
                )
            metadata = {
                "format_version": 1,
                "original_filename": filename,
                "mime_type": media_type,
                "plaintext_size": size,
                "plaintext_sha256": plaintext_hash.hexdigest(),
                "chunk_count": count,
                "chunk_size": self._chunk_size,
            }
            nonce, ciphertext, tag = self._crypto.encrypt_metadata(
                master_key, context, metadata
            )
        except BaseException:
            await asyncio.to_thread(shutil.rmtree, directory, True)
            raise
        return PreparedEncryptedAttachment(
            attachment_id,
            conversation_id,
            uploader_id,
            path,
            directory,
            filename,
            media_type,
            size,
            sum(item.encrypted_size for item in chunks),
            self._chunk_size,
            tuple(chunks),
            plaintext_hash.hexdigest(),
            encrypted_hash.digest(),
            nonce,
            ciphertext,
            tag,
            master_key,
        )

    def build_initialise_request(
        self,
        prepared: PreparedEncryptedAttachment,
        recipient_keys: tuple[AttachmentRecipientKeyRequest, ...],
    ) -> InitialiseUploadRequest:
        """Create a plaintext-free upload request after callers wrap the master key."""
        return InitialiseUploadRequest(
            attachment_id=prepared.attachment_id,
            conversation_id=prepared.conversation_id,
            filename=prepared.filename,
            media_type=prepared.media_type,
            encrypted_size=prepared.encrypted_size,
            original_size=prepared.plaintext_size,
            chunk_size=prepared.chunk_size,
            chunk_count=len(prepared.chunks),
            content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
            hash_algorithm=HashAlgorithm.SHA256_V1,
            encrypted_checksum=base64.b64encode(prepared.encrypted_sha256).decode(
                "ascii"
            ),
            encrypted_metadata=base64.b64encode(prepared.metadata_ciphertext).decode(
                "ascii"
            ),
            metadata_nonce=base64.b64encode(prepared.metadata_nonce).decode("ascii"),
            metadata_authentication_tag=base64.b64encode(prepared.metadata_tag).decode(
                "ascii"
            ),
            recipient_keys=recipient_keys,
        )

    async def upload(
        self,
        prepared: PreparedEncryptedAttachment,
        recipient_keys: tuple[AttachmentRecipientKeyRequest, ...],
    ) -> AttachmentResponse:
        initialised = await self._api.initialise_upload(
            self.build_initialise_request(prepared, recipient_keys)
        )
        status = await self._api.get_upload_status(initialised.upload_id)
        limiter = BandwidthLimiter(self._bandwidth_limit)
        missing = set(status.missing_chunks)
        try:
            for prepared_chunk in prepared.chunks:
                if prepared_chunk.index not in missing:
                    continue
                chunk = await asyncio.to_thread(prepared_chunk.load)
                await limiter.consume(len(chunk.ciphertext))
                await self._api.upload_chunk(initialised.upload_id, chunk)
                del chunk
            return await self._api.complete_upload(initialised.upload_id)
        except BaseException:
            with suppress(Exception):
                await self._api.cancel_upload(initialised.upload_id)
            raise

    async def download(
        self,
        attachment_id: UUID,
        destination: Path,
        master_key: bytes,
        cancellation_token: CancellationToken,
    ) -> Path:
        """Download, authenticate and atomically publish one attachment."""
        metadata = await self._api.get_attachment(attachment_id)
        if metadata.chunk_count is None or metadata.chunk_count < 1:
            raise FileTransferError(user_message="Attachment metadata is incomplete.")
        encrypted_metadata_value = metadata.encrypted_metadata
        metadata_nonce_value = metadata.metadata_nonce
        metadata_tag_value = metadata.metadata_authentication_tag
        if (
            encrypted_metadata_value is None
            or metadata_nonce_value is None
            or metadata_tag_value is None
        ):
            raise FileTransferError(user_message="Attachment metadata is incomplete.")
        context = AttachmentCryptoContext(
            metadata.id,
            metadata.conversation_id,
            metadata.uploaded_by,
            metadata.chunk_count,
        )
        encrypted_metadata = self._crypto.decrypt_metadata(
            master_key,
            context,
            base64.b64decode(metadata_nonce_value, validate=True),
            base64.b64decode(encrypted_metadata_value, validate=True),
            base64.b64decode(metadata_tag_value, validate=True),
        )
        expected_hash = encrypted_metadata.get("plaintext_sha256")
        expected_size = encrypted_metadata.get("plaintext_size")
        if (
            not isinstance(expected_hash, str)
            or expected_size != metadata.original_size
        ):
            raise FileTransferError(user_message="Attachment metadata is invalid.")
        output = self._available_destination(destination)
        partial = output.with_name(output.name + ".bluebubbles-partial")
        digest = hashlib.sha256()
        total = 0
        try:
            partial.parent.mkdir(parents=True, exist_ok=True)
            with partial.open("xb") as stream:
                for index in range(metadata.chunk_count):
                    cancellation_token.raise_if_cancelled()
                    chunk = await self._api.download_chunk(attachment_id, index)
                    if chunk.index != index:
                        raise FileTransferError(
                            user_message="Attachment chunks arrived out of order."
                        )
                    plaintext = self._crypto.decrypt_chunk(master_key, context, chunk)
                    stream.write(plaintext)
                    digest.update(plaintext)
                    total += len(plaintext)
                    plaintext = b""
                stream.flush()
                os.fsync(stream.fileno())
            if total != metadata.original_size or not secrets.compare_digest(
                digest.hexdigest(), expected_hash
            ):
                raise FileTransferError(
                    user_message="The downloaded attachment checksum did not match."
                )
            os.replace(partial, output)
            return output
        except BaseException:
            partial.unlink(missing_ok=True)
            raise

    @staticmethod
    def _available_destination(destination: Path) -> Path:
        """Choose a collision-free filename without overwriting user data."""
        selected = destination.resolve()
        if not selected.exists():
            return selected
        for index in range(1, 10_000):
            candidate = selected.with_name(
                f"{selected.stem} ({index}){selected.suffix}"
            )
            if not candidate.exists():
                return candidate
        raise FileTransferError(user_message="A safe download filename is unavailable.")
