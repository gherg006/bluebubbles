"""Public-key descriptors and recipient key-envelope contracts."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator

from bluebubbles.shared._model import ImmutableContractModel
from bluebubbles.shared.security.algorithms import (
    KeyEnvelopeAlgorithm,
    SignatureAlgorithm,
)
from bluebubbles.shared.validation import validate_base64_length


class KeyVersion(ImmutableContractModel):
    """Identify a positive revision of a user's public key."""

    value: Annotated[int, Field(ge=1)]


class KeyFingerprint(ImmutableContractModel):
    """Carry a canonical SHA-256 public-key fingerprint."""

    value: Annotated[str, Field(pattern=r"^[0-9A-F]{4}(?:-[0-9A-F]{4}){15}$")]


class PublicKeyDescriptor(ImmutableContractModel):
    """Describe public encryption and signing keys; never private keys."""

    owner_id: UUID
    version: KeyVersion
    encryption_public_key: str
    signing_public_key: str
    signature_algorithm: SignatureAlgorithm = SignatureAlgorithm.ED25519_V1
    fingerprint: KeyFingerprint
    created_at: datetime
    expires_at: datetime | None = None

    @field_validator("encryption_public_key", "signing_public_key")
    @classmethod
    def _validate_public_key(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=32, maximum_decoded_bytes=32
        )


class RecipientKeyEnvelope(ImmutableContractModel):
    """Carry one encrypted content key for an explicit recipient key version."""

    recipient_id: UUID
    key_version: KeyVersion
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
    def _validate_nonce(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=12, maximum_decoded_bytes=12
        )

    @field_validator("encrypted_key")
    @classmethod
    def _validate_encrypted_key(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=1, maximum_decoded_bytes=512
        )
