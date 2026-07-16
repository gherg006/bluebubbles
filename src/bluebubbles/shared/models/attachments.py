"""Encrypted attachment upload, status, and authorisation contracts."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

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
    COMPLETE = "complete"
    FAILED = "failed"
    DELETED = "deleted"


class AttachmentRecipientKeyRequest(ContractModel):
    """Provide an attachment content-key envelope for one recipient."""

    recipient_id: UUID
    key_version: Annotated[int, Field(ge=1)]
    encrypted_key: str

    @field_validator("encrypted_key")
    @classmethod
    def _validate_key(cls, value: str) -> str:
        return validate_base64_length(value, maximum_decoded_bytes=512)


class AttachmentRecipientKeyResponse(AttachmentRecipientKeyRequest):
    """Return the authenticated recipient's attachment key envelope."""

    attachment_id: UUID


class InitialiseUploadRequest(ContractModel):
    """Reserve an upload for already encrypted attachment bytes."""

    conversation_id: UUID
    filename: str
    media_type: Annotated[str, Field(min_length=1, max_length=255)]
    encrypted_size: Annotated[int, Field(gt=0)]
    original_size: Annotated[int, Field(ge=0)]
    chunk_size: Annotated[int, Field(gt=0)]
    content_algorithm: ContentEncryptionAlgorithm
    hash_algorithm: HashAlgorithm
    encrypted_checksum: str
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
    expires_at: datetime


class UploadChunkResponse(ContractModel):
    """Acknowledge durable receipt of one encrypted chunk."""

    upload_id: UUID
    chunk_index: Annotated[int, Field(ge=0)]
    received_bytes: Annotated[int, Field(gt=0)]


class UploadStatusResponse(ContractModel):
    """Report upload progress without returning chunk contents."""

    upload_id: UUID
    status: AttachmentStatus
    received_bytes: Annotated[int, Field(ge=0)]
    total_bytes: Annotated[int, Field(gt=0)]
    received_chunks: tuple[int, ...] = ()


class AttachmentResponse(ContractModel):
    """Return client-visible encrypted attachment metadata."""

    id: UUID
    conversation_id: UUID
    uploaded_by: UUID
    filename: str
    media_type: str
    encrypted_size: Annotated[int, Field(gt=0)]
    original_size: Annotated[int, Field(ge=0)]
    status: AttachmentStatus
    created_at: datetime


class AuthorisedAttachmentResponse(AttachmentResponse):
    """Return download authorisation metadata for an eligible recipient."""

    download_url: Annotated[str, Field(min_length=1, max_length=2048)]
    recipient_key: AttachmentRecipientKeyResponse
