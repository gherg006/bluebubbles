"""Encrypted message request, response, status, and pagination contracts."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.models.pagination import CursorPageMetadata
from bluebubbles.shared.protocol.serialisation import canonical_json_bytes
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    KeyEnvelopeAlgorithm,
    SignatureAlgorithm,
)
from bluebubbles.shared.validation import validate_base64_length


class MessageType(StrEnum):
    """Identify the semantic kind of encrypted message content."""

    TEXT = "text"
    SYSTEM = "system"
    ATTACHMENT = "attachment"
    TEXT_WITH_ATTACHMENT = "text_with_attachment"


class MessageDeliveryStatus(StrEnum):
    """Represent the server-visible delivery lifecycle."""

    DRAFT = "draft"
    PENDING = "pending"
    ENCRYPTING = "encrypting"
    SENDING = "sending"
    STORED = "stored"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    DELETED = "deleted"


class RecipientKeyEnvelopeRequest(ContractModel):
    """Transmit an encrypted content key for one recipient key revision."""

    recipient_id: UUID
    key_version: Annotated[int, Field(ge=1)]
    algorithm: KeyEnvelopeAlgorithm
    ephemeral_public_key: str
    nonce: str
    encrypted_key: str

    @field_validator("ephemeral_public_key")
    @classmethod
    def _validate_ephemeral_key(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=32, maximum_decoded_bytes=32
        )

    @field_validator("nonce")
    @classmethod
    def _validate_key_nonce(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=12, maximum_decoded_bytes=12
        )

    @field_validator("encrypted_key")
    @classmethod
    def _validate_key(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=1, maximum_decoded_bytes=512
        )


class SendMessageRequest(ContractModel):
    """Submit a client-encrypted, client-signed message envelope."""

    client_message_id: UUID
    conversation_id: UUID
    message_type: MessageType = MessageType.TEXT
    content_algorithm: ContentEncryptionAlgorithm
    ciphertext: Annotated[str, Field(min_length=1, max_length=16_000_000)]
    nonce: str
    signature_algorithm: SignatureAlgorithm
    signature: str
    sender_key_version: Annotated[int, Field(ge=1)]
    protocol_version: Annotated[int, Field(ge=1)] = 1
    client_created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    encrypted_keys: Annotated[
        tuple[RecipientKeyEnvelopeRequest, ...], Field(min_length=1)
    ]
    reply_to_id: UUID | None = None
    attachment_ids: tuple[UUID, ...] = ()
    recipient_envelope_digest: str | None = None

    @field_validator("ciphertext")
    @classmethod
    def _validate_ciphertext(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=1, maximum_decoded_bytes=12_000_000
        )

    @field_validator("nonce")
    @classmethod
    def _validate_nonce(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=12, maximum_decoded_bytes=12
        )

    @field_validator("signature")
    @classmethod
    def _validate_signature(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=64, maximum_decoded_bytes=64
        )

    @model_validator(mode="after")
    def _unique_recipients(self) -> "SendMessageRequest":
        ids = [item.recipient_id for item in self.encrypted_keys]
        if len(ids) != len(set(ids)):
            raise ValueError("Recipient key envelopes must be unique")
        if len(self.attachment_ids) != len(set(self.attachment_ids)):
            raise ValueError("Attachment identifiers must be unique")
        expected = recipient_envelope_digest(self.encrypted_keys)
        if self.recipient_envelope_digest is None:
            self.recipient_envelope_digest = expected
        elif self.recipient_envelope_digest != expected:
            raise ValueError("Recipient envelope digest does not match")
        return self


class EncryptedMessageResponse(ContractModel):
    """Return encrypted message fields without exposing plaintext."""

    id: UUID
    client_message_id: UUID
    conversation_id: UUID
    sender_id: UUID
    message_type: MessageType
    content_algorithm: ContentEncryptionAlgorithm
    ciphertext: str
    nonce: str
    signature_algorithm: SignatureAlgorithm
    signature: str
    sender_key_version: Annotated[int, Field(ge=1)]
    protocol_version: Annotated[int, Field(ge=1)] = 1
    encrypted_key: RecipientKeyEnvelopeRequest
    recipient_envelope_digest: str
    sent_at: datetime
    edited_at: datetime | None = None
    reply_to_id: UUID | None = None
    attachment_ids: tuple[UUID, ...] = ()
    delivery_status: MessageDeliveryStatus = MessageDeliveryStatus.STORED
    version: Annotated[int, Field(ge=1)] = 1


class SendMessageResponse(ContractModel):
    """Confirm idempotent storage of an encrypted message."""

    message: EncryptedMessageResponse
    duplicate: bool = False


class EditMessageRequest(ContractModel):
    """Replace encrypted content and signature for a sender-owned message."""

    ciphertext: str
    nonce: str
    signature: str
    encrypted_keys: Annotated[
        tuple[RecipientKeyEnvelopeRequest, ...], Field(min_length=1)
    ]
    expected_version: Annotated[int, Field(ge=1)] = 1
    sender_key_version: Annotated[int, Field(ge=1)] = 1
    edited_at_client: datetime = Field(default_factory=lambda: datetime.now(UTC))
    recipient_envelope_digest: str | None = None

    @field_validator("ciphertext")
    @classmethod
    def _validate_ciphertext(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=1, maximum_decoded_bytes=12_000_000
        )

    @field_validator("nonce")
    @classmethod
    def _validate_nonce(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=12, maximum_decoded_bytes=12
        )

    @field_validator("signature")
    @classmethod
    def _validate_signature(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=64, maximum_decoded_bytes=64
        )

    @model_validator(mode="after")
    def _unique_recipients(self) -> "EditMessageRequest":
        ids = [item.recipient_id for item in self.encrypted_keys]
        if len(ids) != len(set(ids)):
            raise ValueError("Recipient key envelopes must be unique")
        expected = recipient_envelope_digest(self.encrypted_keys)
        if self.recipient_envelope_digest is None:
            self.recipient_envelope_digest = expected
        elif self.recipient_envelope_digest != expected:
            raise ValueError("Recipient envelope digest does not match")
        return self


def recipient_envelope_digest(
    envelopes: tuple[RecipientKeyEnvelopeRequest, ...],
) -> str:
    """Return a canonical SHA-256 digest binding every recipient envelope."""
    import base64
    import hashlib

    ordered = sorted(envelopes, key=lambda item: item.recipient_id.bytes)
    canonical = canonical_json_bytes([item.model_dump(mode="json") for item in ordered])
    return base64.b64encode(hashlib.sha256(canonical).digest()).decode("ascii")


class DeletedMessageResponse(ContractModel):
    """Confirm soft deletion without returning prior encrypted content."""

    message_id: UUID
    conversation_id: UUID
    sender_id: UUID
    created_at: datetime
    deleted_at: datetime
    version: Annotated[int, Field(ge=1)]
    is_deleted: bool = True


class DeleteMessageRequest(ContractModel):
    """Provide optimistic concurrency data for a soft deletion."""

    expected_version: Annotated[int, Field(ge=1)]


class MessagePageResponse(ContractModel):
    """Return one cursor page of encrypted messages."""

    messages: tuple[EncryptedMessageResponse, ...]
    page: CursorPageMetadata


class MarkConversationReadRequest(ContractModel):
    """Advance the authenticated user's read position in a conversation."""

    conversation_id: UUID
    through_message_id: UUID
