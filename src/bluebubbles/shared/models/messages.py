"""Encrypted message request, response, status, and pagination contracts."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.models.pagination import CursorPageMetadata
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


class MessageDeliveryStatus(StrEnum):
    """Represent the server-visible delivery lifecycle."""

    PENDING = "pending"
    STORED = "stored"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


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
    encrypted_keys: Annotated[
        tuple[RecipientKeyEnvelopeRequest, ...], Field(min_length=1)
    ]
    reply_to_id: UUID | None = None
    attachment_ids: tuple[UUID, ...] = ()

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
    encrypted_key: RecipientKeyEnvelopeRequest
    sent_at: datetime
    edited_at: datetime | None = None
    reply_to_id: UUID | None = None
    attachment_ids: tuple[UUID, ...] = ()
    delivery_status: MessageDeliveryStatus = MessageDeliveryStatus.STORED


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
        return self


class DeletedMessageResponse(ContractModel):
    """Confirm soft deletion without returning prior encrypted content."""

    message_id: UUID
    deleted_at: datetime


class MessagePageResponse(ContractModel):
    """Return one cursor page of encrypted messages."""

    messages: tuple[EncryptedMessageResponse, ...]
    page: CursorPageMetadata


class MarkConversationReadRequest(ContractModel):
    """Advance the authenticated user's read position in a conversation."""

    conversation_id: UUID
    through_message_id: UUID
