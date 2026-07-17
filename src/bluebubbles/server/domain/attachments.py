"""Encrypted attachment metadata and upload-session domain rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from bluebubbles.server.domain.common import BaseEntity
from bluebubbles.shared.models.attachments import AttachmentStatus
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    HashAlgorithm,
    KeyEnvelopeAlgorithm,
)


@dataclass(kw_only=True)
class AttachmentRecipientKey(BaseEntity):
    """Store an encrypted attachment key for one recipient."""

    attachment_id: UUID
    recipient_id: UUID
    key_version: int
    encrypted_key: bytes = field(repr=False)
    algorithm: KeyEnvelopeAlgorithm = (
        KeyEnvelopeAlgorithm.X25519_HKDF_SHA256_AES_256_GCM_V1
    )
    ephemeral_public_key: bytes = field(default=b"", repr=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.key_version < 1 or not self.encrypted_key:
            raise ValueError("Attachment recipient key data is incomplete")


@dataclass(frozen=True, slots=True)
class AttachmentChunk:
    """Describe one durably stored encrypted chunk without file I/O."""

    attachment_id: UUID
    index: int
    size: int
    checksum: bytes = field(repr=False)
    received_at: datetime

    def __post_init__(self) -> None:
        if self.index < 0 or self.size <= 0 or not self.checksum:
            raise ValueError("Chunk index, size, and checksum are required")


@dataclass(kw_only=True)
class Attachment(BaseEntity):
    """Represent server-visible metadata for encrypted attachment bytes."""

    conversation_id: UUID
    uploaded_by: UUID
    filename: str
    media_type: str
    encrypted_size: int
    original_size: int
    content_algorithm: ContentEncryptionAlgorithm
    hash_algorithm: HashAlgorithm
    encrypted_checksum: bytes = field(repr=False)
    storage_reference: str
    chunk_size: int | None = None
    status: AttachmentStatus = AttachmentStatus.INITIALISED
    recipient_keys: tuple[AttachmentRecipientKey, ...] = ()
    linked_message_id: UUID | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.filename.strip() or not self.media_type.strip():
            raise ValueError("Attachment filename and media type are required")
        if self.encrypted_size <= 0 or self.original_size < 0:
            raise ValueError("Attachment sizes are invalid")
        if not self.encrypted_checksum or not self.storage_reference:
            raise ValueError("Checksum and opaque storage reference are required")
        if self.chunk_size is not None and self.chunk_size <= 0:
            raise ValueError("Attachment chunk size must be positive")

    @property
    def chunk_count(self) -> int:
        """Return the persisted chunk count when upload chunking is defined."""
        if self.chunk_size is None:
            raise ValueError("Attachment chunk size is required for persistence")
        return (self.encrypted_size + self.chunk_size - 1) // self.chunk_size

    def can_be_linked(self) -> bool:
        """Return whether complete bytes can be linked to a message once."""
        return (
            self.status is AttachmentStatus.COMPLETE and self.linked_message_id is None
        )

    def link(self, message_id: UUID, at: datetime) -> None:
        """Link a completed attachment to one message."""
        if not self.can_be_linked():
            raise ValueError("Attachment cannot be linked in its current state")
        self.linked_message_id = message_id
        self.touch(at)


@dataclass(kw_only=True)
class UploadSession(BaseEntity):
    """Track bounded receipt of encrypted chunks without accessing storage."""

    attachment_id: UUID
    uploader_id: UUID
    chunk_size: int
    total_size: int
    expires_at: datetime
    received_chunks: dict[int, int] = field(default_factory=dict)
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.chunk_size <= 0 or self.total_size <= 0:
            raise ValueError("Upload sizes must be positive")
        if self.expires_at.tzinfo is None:
            raise ValueError("Upload expiry must be timezone-aware")

    @property
    def expected_chunk_count(self) -> int:
        """Return the number of chunks required by the upload."""
        return (self.total_size + self.chunk_size - 1) // self.chunk_size

    def is_expired(self, at: datetime) -> bool:
        """Return whether the upload is no longer writable."""
        return at >= self.expires_at

    def can_accept_chunk(self, index: int, size: int, at: datetime) -> bool:
        """Validate chunk bounds and idempotent repeated receipt."""
        if self.completed_at is not None or self.is_expired(at):
            return False
        if index < 0 or index >= self.expected_chunk_count or size <= 0:
            return False
        expected = self.chunk_size
        if index == self.expected_chunk_count - 1:
            expected = self.total_size - (index * self.chunk_size)
        existing = self.received_chunks.get(index)
        return size == expected and (existing is None or existing == size)

    def accept_chunk(self, index: int, size: int, at: datetime) -> None:
        """Record durable chunk receipt after storage confirms it."""
        if not self.can_accept_chunk(index, size, at):
            raise ValueError("Upload cannot accept this chunk")
        self.received_chunks[index] = size
        self.touch(at)

    def is_complete(self) -> bool:
        """Return whether every encrypted byte has been acknowledged."""
        return (
            len(self.received_chunks) == self.expected_chunk_count
            and sum(self.received_chunks.values()) == self.total_size
        )

    def complete(self, at: datetime) -> None:
        """Seal a fully received upload session."""
        if not self.is_complete():
            raise ValueError("Upload is incomplete")
        if self.completed_at is None:
            self.completed_at = at
            self.touch(at)
