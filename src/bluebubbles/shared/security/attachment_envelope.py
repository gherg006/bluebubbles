"""Encrypted attachment metadata and chunk-manifest contracts."""

from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from bluebubbles.shared._model import ImmutableContractModel
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    HashAlgorithm,
)
from bluebubbles.shared.security.key_models import RecipientKeyEnvelope
from bluebubbles.shared.validation import (
    validate_base64_length,
    validate_safe_display_filename,
)


class AttachmentRecipientEnvelope(RecipientKeyEnvelope):
    """Specialise a recipient key envelope for an attachment."""


class AttachmentChunkMetadata(ImmutableContractModel):
    """Describe one encrypted attachment chunk without embedding its bytes."""

    index: Annotated[int, Field(ge=0)]
    encrypted_size: Annotated[int, Field(gt=0)]
    nonce: str
    checksum: str

    @field_validator("nonce")
    @classmethod
    def _validate_nonce(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=12, maximum_decoded_bytes=12
        )

    @field_validator("checksum")
    @classmethod
    def _validate_checksum(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=1, maximum_decoded_bytes=128
        )


class EncryptedAttachmentMetadata(ImmutableContractModel):
    """Describe structural metadata for a client-encrypted attachment."""

    attachment_id: UUID
    filename: str
    media_type: Annotated[str, Field(min_length=1, max_length=255)]
    original_size: Annotated[int, Field(ge=0)]
    encrypted_size: Annotated[int, Field(gt=0)]
    content_algorithm: ContentEncryptionAlgorithm
    hash_algorithm: HashAlgorithm
    encrypted_checksum: str

    @field_validator("filename")
    @classmethod
    def _validate_filename(cls, value: str) -> str:
        return validate_safe_display_filename(value)

    @field_validator("encrypted_checksum")
    @classmethod
    def _validate_checksum(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=1, maximum_decoded_bytes=128
        )


class AttachmentManifestData(ImmutableContractModel):
    """Describe all chunks and recipient keys for an encrypted attachment."""

    metadata: EncryptedAttachmentMetadata
    chunks: tuple[AttachmentChunkMetadata, ...]
    recipients: tuple[AttachmentRecipientEnvelope, ...]

    @model_validator(mode="after")
    def _validate_completeness(self) -> "AttachmentManifestData":
        if not self.chunks or [chunk.index for chunk in self.chunks] != list(
            range(len(self.chunks))
        ):
            raise ValueError("Attachment chunk indexes must be contiguous from zero")
        recipient_ids = [item.recipient_id for item in self.recipients]
        if not recipient_ids or len(set(recipient_ids)) != len(recipient_ids):
            raise ValueError("Attachment must have unique recipient envelopes")
        if (
            sum(chunk.encrypted_size for chunk in self.chunks)
            != self.metadata.encrypted_size
        ):
            raise ValueError("Chunk sizes must equal the encrypted attachment size")
        return self
