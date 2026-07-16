"""Validated encrypted-message and canonical-signing structures."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from bluebubbles.shared._model import ImmutableContractModel
from bluebubbles.shared.protocol.serialisation import canonical_json_bytes
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    SignatureAlgorithm,
)
from bluebubbles.shared.security.key_models import RecipientKeyEnvelope
from bluebubbles.shared.validation import validate_base64_length


class MessageRecipientEnvelope(RecipientKeyEnvelope):
    """Specialise a recipient key envelope for a message."""


class SignedMessageFields(ImmutableContractModel):
    """Contain precisely the fields covered by a message signature."""

    message_id: UUID
    conversation_id: UUID
    sender_id: UUID
    sender_key_version: Annotated[int, Field(ge=1)]
    timestamp: datetime
    content_algorithm: ContentEncryptionAlgorithm
    nonce: str
    ciphertext: str
    recipients: tuple[MessageRecipientEnvelope, ...]

    @field_validator("nonce")
    @classmethod
    def _validate_nonce(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=12, maximum_decoded_bytes=12
        )

    @field_validator("ciphertext")
    @classmethod
    def _validate_ciphertext(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=1, maximum_decoded_bytes=12_000_000
        )

    def canonical_bytes(self) -> bytes:
        """Return deterministic JSON bytes used for signature verification."""
        return canonical_json_bytes(self)


class EncryptedMessageEnvelope(ImmutableContractModel):
    """Represent a complete encrypted and signed message payload."""

    signed_fields: SignedMessageFields
    signature_algorithm: SignatureAlgorithm
    signature: str

    @field_validator("signature")
    @classmethod
    def _validate_signature(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=64, maximum_decoded_bytes=64
        )

    @model_validator(mode="after")
    def _validate_recipients(self) -> "EncryptedMessageEnvelope":
        recipients = [item.recipient_id for item in self.signed_fields.recipients]
        if not recipients or len(set(recipients)) != len(recipients):
            raise ValueError("Message must have unique recipient envelopes")
        return self
