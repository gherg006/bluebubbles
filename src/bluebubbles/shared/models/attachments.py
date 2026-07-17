"""Encrypted attachment upload, status, and authorisation contracts."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    HashAlgorithm,
)
from bluebubbles.shared.validation import (
    validate_base64_length,
    validate_safe_display_filename,
)


class AttachmentStatus(StrEnum):
    """Represent the server-visible encrypted attachment lifecycle."""

    INITIALISED = "initialised"
    UPLOADING = "uploading"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    DELETED = "deleted"


class AttachmentRecipientKeyRequest(ContractModel):
    """Provide an attachment content-key envelope for one recipient."""

    recipient_id: UUID
    key_version: Annotated[int, Field(ge=1)]
    encrypted_key: str
    algorithm: str | None = None
    ephemeral_public_key: str | None = None
    nonce: str | None = None

    @field_validator("encrypted_key")
    @classmethod
    def _validate_key(cls, value: str) -> str:
        return validate_base64_length(value, maximum_decoded_bytes=512)


class AttachmentRecipientKeyResponse(AttachmentRecipientKeyRequest):
    """Return the authenticated recipient's attachment key envelope."""

    attachment_id: UUID


class InitialiseUploadRequest(ContractModel):
    """Reserve an upload for already encrypted attachment bytes."""

    attachment_id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    filename: str
    media_type: Annotated[str, Field(min_length=1, max_length=255)]
    encrypted_size: Annotated[int, Field(gt=0)]
    original_size: Annotated[int, Field(ge=0)]
    chunk_size: Annotated[int, Field(gt=0)]
    chunk_count: Annotated[int, Field(gt=0)] | None = None
    content_algorithm: ContentEncryptionAlgorithm
    hash_algorithm: HashAlgorithm
    encrypted_checksum: str
    encrypted_metadata: str | None = None
    metadata_nonce: str | None = None
    metadata_authentication_tag: str | None = None
    manifest_signature: str | None = None
    uploader_signing_key_version: Annotated[int, Field(ge=1)] | None = None
    protocol_version: Annotated[int, Field(ge=1)] = 1
    recipient_keys: Annotated[
        tuple[AttachmentRecipientKeyRequest, ...], Field(min_length=1)
    ]

    @field_validator("filename")
    @classmethod
    def _validate_filename(cls, value: str) -> str:
        return validate_safe_display_filename(value)

    @field_validator("encrypted_checksum")
    @classmethod
    def _validate_checksum(cls, value: str) -> str:
        return validate_base64_length(value, maximum_decoded_bytes=128)


class InitialiseUploadResponse(ContractModel):
    """Return upload identity and bounded chunk instructions."""

    attachment_id: UUID
    upload_id: UUID
    chunk_size: Annotated[int, Field(gt=0)]
    expected_chunk_count: Annotated[int, Field(gt=0)]
    expires_at: datetime
    already_received_chunks: tuple[int, ...] = ()


class UploadChunkResponse(ContractModel):
    """Acknowledge durable receipt of one encrypted chunk."""

    upload_id: UUID
    chunk_index: Annotated[int, Field(ge=0)]
    received_bytes: Annotated[int, Field(gt=0)]
    total_received_bytes: Annotated[int, Field(ge=0)]
    received_chunk_count: Annotated[int, Field(ge=0)]
    expected_chunk_count: Annotated[int, Field(gt=0)]
    is_complete: bool


class UploadStatusResponse(ContractModel):
    """Report upload progress without returning chunk contents."""

    upload_id: UUID
    status: AttachmentStatus
    received_bytes: Annotated[int, Field(ge=0)]
    total_bytes: Annotated[int, Field(gt=0)]
    received_chunks: tuple[int, ...] = ()
    missing_chunks: tuple[int, ...] = ()
    attachment_id: UUID | None = None
    expires_at: datetime | None = None


class AttachmentResponse(ContractModel):
    """Return client-visible encrypted attachment metadata."""

    id: UUID
    conversation_id: UUID
    uploaded_by: UUID
    filename: str
    media_type: str
    encrypted_size: Annotated[int, Field(gt=0)]
    original_size: Annotated[int, Field(ge=0)]
    chunk_count: Annotated[int, Field(gt=0)] | None = None
    status: AttachmentStatus
    created_at: datetime


class AuthorisedAttachmentResponse(AttachmentResponse):
    """Return download authorisation metadata for an eligible recipient."""

    download_url: Annotated[str, Field(min_length=1, max_length=2048)]
    recipient_key: AttachmentRecipientKeyResponse
    encrypted_metadata: str | None = None
    metadata_nonce: str | None = None
    metadata_authentication_tag: str | None = None
