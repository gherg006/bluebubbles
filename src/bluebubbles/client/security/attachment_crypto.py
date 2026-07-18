"""Bounded-memory authenticated encryption for attachment files."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import UUID

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from bluebubbles.shared.errors.exceptions import CryptographyError, FileTransferError


class CancellationToken(Protocol):
    """Allow long-running file work to stop between bounded chunks."""

    def raise_if_cancelled(self) -> None: ...


@dataclass(frozen=True, slots=True)
class PrepareAttachmentCommand:
    source_path: Path
    output_path: Path
    chunk_size: int = 1_048_576


@dataclass(frozen=True, slots=True)
class PreparedUpload:
    encrypted_path: Path
    file_key: bytes
    nonce_prefix: bytes
    plaintext_size: int
    encrypted_size: int
    plaintext_sha256: str
    ciphertext_sha256: str
    chunk_count: int
    chunk_size: int


@dataclass(frozen=True, slots=True)
class DecryptAttachmentCommand:
    encrypted_path: Path
    output_path: Path
    file_key: bytes
    nonce_prefix: bytes
    chunk_size: int
    plaintext_size: int
    plaintext_sha256: str


@dataclass(frozen=True, slots=True)
class AttachmentCryptoContext:
    """Bind one chunk to its attachment, membership, and manifest context."""

    attachment_id: UUID
    conversation_id: UUID
    uploader_id: UUID
    chunk_count: int
    manifest_version: int = 1


@dataclass(frozen=True, slots=True)
class AuthenticatedAttachmentChunk:
    """Contain one independently authenticated encrypted chunk."""

    index: int
    nonce: bytes
    ciphertext: bytes
    authentication_tag: bytes
    plaintext_length: int
    encrypted_hash: bytes


class AttachmentEncryptionService:
    """Encrypt and decrypt files a chunk at a time without whole-file reads."""

    def __init__(self, *, protocol_version: int = 1) -> None:
        self._protocol_version = protocol_version

    @staticmethod
    def generate_file_key() -> bytes:
        return secrets.token_bytes(32)

    @staticmethod
    def derive_subkey(master_key: bytes, purpose: bytes) -> bytes:
        """Derive a purpose-separated attachment key with HKDF-SHA-256."""
        if len(master_key) != 32 or purpose not in {
            b"bluebubbles-attachment-chunks-v1",
            b"bluebubbles-attachment-metadata-v1",
            b"bluebubbles-attachment-thumbnail-v1",
        }:
            raise CryptographyError(
                user_message="The attachment key context is invalid."
            )
        return HKDF(
            algorithm=hashes.SHA256(), length=32, salt=None, info=purpose
        ).derive(master_key)

    def encrypt_chunk(
        self,
        master_key: bytes,
        context: AttachmentCryptoContext,
        chunk_index: int,
        plaintext: bytes,
    ) -> AuthenticatedAttachmentChunk:
        """Encrypt one chunk with a fresh random nonce and complete contextual AAD."""
        if not plaintext or not 0 <= chunk_index < context.chunk_count:
            raise ValueError("Attachment chunk inputs are invalid")
        nonce = secrets.token_bytes(12)
        key = self.derive_subkey(master_key, b"bluebubbles-attachment-chunks-v1")
        combined = AESGCM(key).encrypt(
            nonce, plaintext, self._context_aad(context, chunk_index, len(plaintext))
        )
        ciphertext, tag = combined[:-16], combined[-16:]
        digest = hashlib.sha256(ciphertext).digest()
        return AuthenticatedAttachmentChunk(
            chunk_index, nonce, ciphertext, tag, len(plaintext), digest
        )

    def decrypt_chunk(
        self,
        master_key: bytes,
        context: AttachmentCryptoContext,
        chunk: AuthenticatedAttachmentChunk,
    ) -> bytes:
        """Authenticate one chunk's hash, AAD and GCM tag before returning plaintext."""
        expected = hashlib.sha256(chunk.ciphertext).digest()
        if not secrets.compare_digest(expected, chunk.encrypted_hash):
            raise CryptographyError(
                user_message="The encrypted attachment chunk is damaged."
            )
        try:
            return AESGCM(
                self.derive_subkey(master_key, b"bluebubbles-attachment-chunks-v1")
            ).decrypt(
                chunk.nonce,
                chunk.ciphertext + chunk.authentication_tag,
                self._context_aad(context, chunk.index, chunk.plaintext_length),
            )
        except (InvalidTag, ValueError) as error:
            raise CryptographyError(
                user_message="The attachment chunk could not be verified."
            ) from error

    def encrypt_metadata(
        self,
        master_key: bytes,
        context: AttachmentCryptoContext,
        metadata: dict[str, object],
    ) -> tuple[bytes, bytes, bytes]:
        """Encrypt canonical attachment metadata with a dedicated subkey."""
        nonce = secrets.token_bytes(12)
        plaintext = json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        combined = AESGCM(
            self.derive_subkey(master_key, b"bluebubbles-attachment-metadata-v1")
        ).encrypt(nonce, plaintext, self._metadata_aad(context))
        return nonce, combined[:-16], combined[-16:]

    def decrypt_metadata(
        self,
        master_key: bytes,
        context: AttachmentCryptoContext,
        nonce: bytes,
        ciphertext: bytes,
        tag: bytes,
    ) -> dict[str, object]:
        """Authenticate and parse canonical encrypted attachment metadata."""
        try:
            plaintext = AESGCM(
                self.derive_subkey(master_key, b"bluebubbles-attachment-metadata-v1")
            ).decrypt(nonce, ciphertext + tag, self._metadata_aad(context))
            value = json.loads(plaintext)
        except (InvalidTag, ValueError, UnicodeError, json.JSONDecodeError) as error:
            raise CryptographyError(
                user_message="Attachment metadata could not be verified."
            ) from error
        if not isinstance(value, dict):
            raise CryptographyError(user_message="Attachment metadata is invalid.")
        return value

    async def encrypt_file(
        self,
        command: PrepareAttachmentCommand,
        cancellation_token: CancellationToken,
    ) -> PreparedUpload:
        """Create a temporary encrypted stream with per-chunk GCM tags."""
        if not 262_144 <= command.chunk_size <= 8_388_608:
            raise ValueError("Attachment chunk size is outside the supported range")
        if command.source_path.resolve() == command.output_path.resolve():
            raise ValueError("Encrypted output must differ from the source")
        file_key = self.generate_file_key()
        nonce_prefix = secrets.token_bytes(8)
        plaintext_hash = hashlib.sha256()
        ciphertext_hash = hashlib.sha256()
        plaintext_size = encrypted_size = chunk_count = 0
        command.output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with (
                command.source_path.open("rb") as source,
                command.output_path.open("xb") as target,
            ):
                while True:
                    cancellation_token.raise_if_cancelled()
                    chunk = source.read(command.chunk_size)
                    if not chunk:
                        break
                    nonce = self._nonce(nonce_prefix, chunk_count)
                    encrypted = AESGCM(file_key).encrypt(
                        nonce, chunk, self._aad(chunk_count, len(chunk))
                    )
                    target.write(len(encrypted).to_bytes(4, "big"))
                    target.write(encrypted)
                    plaintext_hash.update(chunk)
                    ciphertext_hash.update(encrypted)
                    plaintext_size += len(chunk)
                    encrypted_size += len(encrypted) + 4
                    chunk_count += 1
                    chunk = b""
        except BaseException:
            command.output_path.unlink(missing_ok=True)
            raise
        return PreparedUpload(
            command.output_path,
            file_key,
            nonce_prefix,
            plaintext_size,
            encrypted_size,
            plaintext_hash.hexdigest(),
            ciphertext_hash.hexdigest(),
            chunk_count,
            command.chunk_size,
        )

    async def decrypt_download(
        self,
        command: DecryptAttachmentCommand,
        cancellation_token: CancellationToken,
    ) -> Path:
        """Authenticate each chunk and publish output only after hash validation."""
        if len(command.file_key) != 32 or len(command.nonce_prefix) != 8:
            raise CryptographyError(user_message="The attachment key is invalid.")
        temporary = command.output_path.with_suffix(
            command.output_path.suffix + ".part"
        )
        temporary.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        total = index = 0
        try:
            with (
                command.encrypted_path.open("rb") as source,
                temporary.open("xb") as target,
            ):
                while True:
                    cancellation_token.raise_if_cancelled()
                    length_bytes = source.read(4)
                    if not length_bytes:
                        break
                    if len(length_bytes) != 4:
                        raise FileTransferError(
                            user_message="The attachment stream is incomplete."
                        )
                    encrypted_length = int.from_bytes(length_bytes, "big")
                    if (
                        encrypted_length < 16
                        or encrypted_length > command.chunk_size + 16
                    ):
                        raise FileTransferError(
                            user_message="The attachment chunk is invalid."
                        )
                    encrypted = source.read(encrypted_length)
                    if len(encrypted) != encrypted_length:
                        raise FileTransferError(
                            user_message="The attachment stream is incomplete."
                        )
                    expected_size = min(
                        command.chunk_size, command.plaintext_size - total
                    )
                    plaintext = AESGCM(command.file_key).decrypt(
                        self._nonce(command.nonce_prefix, index),
                        encrypted,
                        self._aad(index, expected_size),
                    )
                    target.write(plaintext)
                    digest.update(plaintext)
                    total += len(plaintext)
                    index += 1
                    plaintext = b""
            if (
                total != command.plaintext_size
                or digest.hexdigest() != command.plaintext_sha256
            ):
                raise CryptographyError(
                    user_message="The attachment checksum did not match."
                )
            os.replace(temporary, command.output_path)
            return command.output_path
        except (InvalidTag, ValueError) as error:
            temporary.unlink(missing_ok=True)
            raise CryptographyError(
                user_message="The attachment could not be verified or decrypted."
            ) from error
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise

    def _aad(self, chunk_index: int, plaintext_size: int) -> bytes:
        return b"\x00".join(
            (
                b"bluebubbles-attachment-chunk-v1",
                self._protocol_version.to_bytes(4, "big"),
                chunk_index.to_bytes(8, "big"),
                plaintext_size.to_bytes(8, "big"),
            )
        )

    def _context_aad(
        self, context: AttachmentCryptoContext, chunk_index: int, plaintext_size: int
    ) -> bytes:
        return b"\x00".join(
            (
                b"bluebubbles-attachment-chunk-v1",
                self._protocol_version.to_bytes(4, "big"),
                context.attachment_id.bytes,
                context.conversation_id.bytes,
                context.uploader_id.bytes,
                chunk_index.to_bytes(8, "big"),
                context.chunk_count.to_bytes(8, "big"),
                plaintext_size.to_bytes(8, "big"),
                b"AES-256-GCM-V1",
                context.manifest_version.to_bytes(4, "big"),
            )
        )

    def _metadata_aad(self, context: AttachmentCryptoContext) -> bytes:
        return b"\x00".join(
            (
                b"bluebubbles-attachment-metadata-v1",
                self._protocol_version.to_bytes(4, "big"),
                context.attachment_id.bytes,
                context.conversation_id.bytes,
                context.uploader_id.bytes,
                context.manifest_version.to_bytes(4, "big"),
                b"AES-256-GCM-V1",
            )
        )

    @staticmethod
    def _nonce(prefix: bytes, chunk_index: int) -> bytes:
        if len(prefix) != 8 or not 0 <= chunk_index < 2**32:
            raise ValueError("Attachment chunk nonce inputs are invalid")
        return prefix + chunk_index.to_bytes(4, "big")
