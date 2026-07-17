"""Public-key descriptors and recipient key-envelope contracts."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator

from bluebubbles.shared._model import ImmutableContractModel
from bluebubbles.shared.security.algorithms import (
    KeyEnvelopeAlgorithm,
)
from bluebubbles.shared.validation import validate_base64_length


class KeyVersion(ImmutableContractModel):
    """Identify a positive revision of a user's public key."""

    value: Annotated[int, Field(ge=1)]


class KeyFingerprint(ImmutableContractModel):
    """Carry a canonical SHA-256 public-key fingerprint."""

    value: Annotated[str, Field(pattern=r"^[0-9A-F]{4}(?:-[0-9A-F]{4}){15}$")]


class PublicKeyType(StrEnum):
    """Distinguish independently versioned identity key purposes."""

    ENCRYPTION = "encryption"
    SIGNING = "signing"


class PublicKeyAlgorithm(StrEnum):
    """Allow only the Version 1.0 identity-key algorithms."""

    X25519_V1 = "X25519-V1"
    ED25519_V1 = "ED25519-V1"


class PublicKeyDescriptor(ImmutableContractModel):
    """Describe one public identity-key revision; never private material."""

    owner_id: UUID
    key_type: PublicKeyType
    version: KeyVersion
    algorithm: PublicKeyAlgorithm
    public_key: str
    fingerprint: KeyFingerprint
    created_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    is_primary: bool = False

    @field_validator("public_key")
    @classmethod
    def _validate_public_key(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=32, maximum_decoded_bytes=32
        )


class RegisterPublicKeyRequest(ImmutableContractModel):
    """Register one client-generated public key and no private-key fields."""

    key_type: PublicKeyType
    version: KeyVersion
    algorithm: PublicKeyAlgorithm
    public_key: str
    fingerprint: KeyFingerprint
    expires_at: datetime | None = None

    @field_validator("public_key")
    @classmethod
    def _validate_public_key(cls, value: str) -> str:
        return validate_base64_length(
            value, minimum_decoded_bytes=32, maximum_decoded_bytes=32
        )


class RevokePublicKeyRequest(ImmutableContractModel):
    """Revoke one owned public-key revision for all future use."""

    reason: Annotated[str, Field(min_length=1, max_length=500)]


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
