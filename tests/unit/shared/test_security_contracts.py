"""Tests for shared cryptographic identifiers and encrypted envelope structures."""

import base64
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    HashAlgorithm,
    KeyEnvelopeAlgorithm,
    SignatureAlgorithm,
)
from bluebubbles.shared.security.attachment_envelope import (
    AttachmentChunkMetadata,
    AttachmentManifestData,
    AttachmentRecipientEnvelope,
    EncryptedAttachmentMetadata,
)
from bluebubbles.shared.security.fingerprints import (
    calculate_public_key_fingerprint,
    format_fingerprint,
    validate_fingerprint,
)
from bluebubbles.shared.security.key_models import KeyVersion
from bluebubbles.shared.security.message_envelope import (
    EncryptedMessageEnvelope,
    MessageRecipientEnvelope,
    SignedMessageFields,
)


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode()


def _message_recipient() -> MessageRecipientEnvelope:
    return MessageRecipientEnvelope(
        recipient_id=uuid4(),
        key_version=KeyVersion(value=1),
        algorithm=KeyEnvelopeAlgorithm.X25519_HKDF_SHA256_AES_256_GCM_V1,
        ephemeral_public_key=_b64(b"p" * 32),
        nonce=_b64(b"n" * 12),
        encrypted_key=_b64(b"key"),
    )


def _attachment_recipient() -> AttachmentRecipientEnvelope:
    return AttachmentRecipientEnvelope(
        recipient_id=uuid4(),
        key_version=KeyVersion(value=1),
        algorithm=KeyEnvelopeAlgorithm.X25519_HKDF_SHA256_AES_256_GCM_V1,
        ephemeral_public_key=_b64(b"p" * 32),
        nonce=_b64(b"n" * 12),
        encrypted_key=_b64(b"key"),
    )


def test_fingerprint_has_one_canonical_representation() -> None:
    fingerprint = calculate_public_key_fingerprint(b"public key")
    assert validate_fingerprint(fingerprint) == fingerprint
    assert format_fingerprint(fingerprint.replace("-", "").lower()) == fingerprint
    with pytest.raises(ValueError):
        calculate_public_key_fingerprint(b"")
    with pytest.raises(ValueError):
        format_fingerprint("abcd")
    with pytest.raises(ValueError):
        validate_fingerprint(fingerprint.lower())


def test_message_envelope_produces_stable_signing_bytes() -> None:
    fields = SignedMessageFields(
        message_id=uuid4(),
        conversation_id=uuid4(),
        sender_id=uuid4(),
        sender_key_version=1,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
        nonce=_b64(b"n" * 12),
        ciphertext=_b64(b"ciphertext"),
        recipients=(_message_recipient(),),
    )
    envelope = EncryptedMessageEnvelope(
        signed_fields=fields,
        signature_algorithm=SignatureAlgorithm.ED25519_V1,
        signature=_b64(b"s" * 64),
    )
    assert b'"ciphertext"' in envelope.signed_fields.canonical_bytes()
    with pytest.raises(ValidationError, match="unique recipient"):
        EncryptedMessageEnvelope(
            signed_fields=fields.model_copy(update={"recipients": ()}),
            signature_algorithm=SignatureAlgorithm.ED25519_V1,
            signature=_b64(b"s" * 64),
        )


def test_attachment_manifest_enforces_contiguous_complete_chunks() -> None:
    metadata = EncryptedAttachmentMetadata(
        attachment_id=uuid4(),
        filename="report.pdf",
        media_type="application/pdf",
        original_size=10,
        encrypted_size=20,
        content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
        hash_algorithm=HashAlgorithm.SHA256_V1,
        encrypted_checksum=_b64(b"checksum"),
    )
    chunk = AttachmentChunkMetadata(
        index=0, encrypted_size=20, nonce=_b64(b"n" * 12), checksum=_b64(b"sum")
    )
    manifest = AttachmentManifestData(
        metadata=metadata,
        chunks=(chunk,),
        recipients=(_attachment_recipient(),),
    )
    assert manifest.metadata.filename == "report.pdf"
    with pytest.raises(ValidationError, match="Chunk sizes"):
        AttachmentManifestData(
            metadata=metadata,
            chunks=(chunk.model_copy(update={"encrypted_size": 19}),),
            recipients=manifest.recipients,
        )
