"""End-to-end message encryption, signing, verification, and decryption."""

from __future__ import annotations

import base64
import json
import secrets
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, cast
from uuid import UUID

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from bluebubbles.client.security.key_manager import ClientKeyManager
from bluebubbles.client.security.key_store import PrivateKeyType
from bluebubbles.shared.errors.exceptions import CryptographyError
from bluebubbles.shared.models.messages import (
    EncryptedMessageResponse,
    MessageType,
    RecipientKeyEnvelopeRequest,
    SendMessageRequest,
    recipient_envelope_digest,
)
from bluebubbles.shared.protocol.serialisation import canonical_json_bytes
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    KeyEnvelopeAlgorithm,
    SignatureAlgorithm,
)


@dataclass(frozen=True, slots=True)
class RecipientPublicEncryptionKey:
    """Carry one recipient's validated active X25519 public-key revision."""

    recipient_id: UUID
    key_version: int
    public_key: bytes


@dataclass(frozen=True, slots=True)
class EncryptMessageCommand:
    """Contain transient plaintext plus all immutable security metadata."""

    message_id: UUID
    conversation_id: UUID
    sender_id: UUID
    message_type: MessageType
    plaintext: str
    recipient_public_keys: Sequence[RecipientPublicEncryptionKey]
    sender_signing_key_version: int
    client_created_at: datetime
    reply_to_id: UUID | None = None
    attachment_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class DecryptedMessage:
    """Return authenticated plaintext only after every verification succeeds."""

    message_id: UUID
    text: str
    format_version: int


class SenderSigningKeyResolver(Protocol):
    """Resolve a historical sender signing key by exact version."""

    async def get_signing_key(self, user_id: UUID, version: int) -> bytes: ...


class MessageEncryptionService:
    """Implement the fixed Version 1 hybrid message construction."""

    def __init__(
        self,
        key_manager: ClientKeyManager,
        signing_key_resolver: SenderSigningKeyResolver,
        *,
        protocol_version: int = 1,
        random_bytes: Callable[[int], bytes] = secrets.token_bytes,
    ) -> None:
        self._key_manager = key_manager
        self._signing_key_resolver = signing_key_resolver
        self._protocol_version = protocol_version
        self._random_bytes = random_bytes

    async def encrypt_message(
        self, command: EncryptMessageCommand
    ) -> SendMessageRequest:
        """Encrypt once, wrap the content key per recipient, then sign metadata."""
        self._validate_command(command)
        plaintext = canonical_json_bytes(
            {
                "client_metadata": {},
                "format_version": 1,
                "mentions": [],
                "text": command.plaintext,
            }
        )
        content_key = self._random_bytes(32)
        nonce = self._random_bytes(12)
        aad = self._message_aad(command)
        ciphertext = AESGCM(content_key).encrypt(nonce, plaintext, aad)
        envelopes = tuple(
            self._wrap_content_key(command, recipient, content_key)
            for recipient in sorted(
                command.recipient_public_keys, key=lambda item: item.recipient_id.bytes
            )
        )
        digest = recipient_envelope_digest(envelopes)
        signed = self._signed_bytes(
            aad=aad,
            ciphertext=ciphertext,
            nonce=nonce,
            recipient_digest=digest,
            signing_key_version=command.sender_signing_key_version,
        )
        handle = await self._key_manager.get_private_signing_key(
            command.sender_signing_key_version
        )
        if handle.key_type is not PrivateKeyType.SIGNING:
            raise CryptographyError(user_message="The signing key is unavailable.")
        with handle.use_key() as private_key:
            signature = cast(Ed25519PrivateKey, private_key).sign(signed)
        return SendMessageRequest(
            client_message_id=command.message_id,
            conversation_id=command.conversation_id,
            message_type=command.message_type,
            content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
            ciphertext=self._encode(ciphertext),
            nonce=self._encode(nonce),
            signature_algorithm=SignatureAlgorithm.ED25519_V1,
            signature=self._encode(signature),
            sender_key_version=command.sender_signing_key_version,
            protocol_version=self._protocol_version,
            client_created_at=command.client_created_at,
            encrypted_keys=envelopes,
            reply_to_id=command.reply_to_id,
            attachment_ids=command.attachment_ids,
            recipient_envelope_digest=digest,
        )

    async def decrypt_message(
        self, response: EncryptedMessageResponse
    ) -> DecryptedMessage:
        """Verify signature before key unwrapping and authenticated decryption."""
        try:
            ciphertext = self._decode(response.ciphertext)
            nonce = self._decode(response.nonce)
            signature = self._decode(response.signature)
            aad = self._response_aad(response)
            signing_key = await self._signing_key_resolver.get_signing_key(
                response.sender_id, response.sender_key_version
            )
            Ed25519PublicKey.from_public_bytes(signing_key).verify(
                signature,
                self._signed_bytes(
                    aad=aad,
                    ciphertext=ciphertext,
                    nonce=nonce,
                    recipient_digest=response.recipient_envelope_digest,
                    signing_key_version=response.sender_key_version,
                ),
            )
            content_key = await self._unwrap_content_key(response)
            plaintext = AESGCM(content_key).decrypt(nonce, ciphertext, aad)
            value = json.loads(plaintext)
            if (
                not isinstance(value, dict)
                or value.get("format_version") != 1
                or not isinstance(value.get("text"), str)
            ):
                raise ValueError
            return DecryptedMessage(response.id, str(value["text"]), 1)
        except (
            InvalidSignature,
            InvalidTag,
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            raise CryptographyError(
                user_message="This message could not be verified or decrypted."
            ) from error

    def _wrap_content_key(
        self,
        command: EncryptMessageCommand,
        recipient: RecipientPublicEncryptionKey,
        content_key: bytes,
    ) -> RecipientKeyEnvelopeRequest:
        if len(recipient.public_key) != 32 or recipient.key_version < 1:
            raise CryptographyError(
                user_message="A recipient encryption key is invalid."
            )
        ephemeral = X25519PrivateKey.generate()
        ephemeral_public = ephemeral.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        shared = ephemeral.exchange(
            X25519PublicKey.from_public_bytes(recipient.public_key)
        )
        wrapping_key = self._derive_wrapping_key(
            shared, command.message_id, recipient.recipient_id, recipient.key_version
        )
        wrapping_nonce = self._random_bytes(12)
        aad = self._key_aad(
            command.message_id,
            command.conversation_id,
            recipient.recipient_id,
            recipient.key_version,
            ephemeral_public,
        )
        return RecipientKeyEnvelopeRequest(
            recipient_id=recipient.recipient_id,
            key_version=recipient.key_version,
            algorithm=KeyEnvelopeAlgorithm.X25519_HKDF_SHA256_AES_256_GCM_V1,
            ephemeral_public_key=self._encode(ephemeral_public),
            nonce=self._encode(wrapping_nonce),
            encrypted_key=self._encode(
                AESGCM(wrapping_key).encrypt(wrapping_nonce, content_key, aad)
            ),
        )

    async def _unwrap_content_key(self, response: EncryptedMessageResponse) -> bytes:
        envelope = response.encrypted_key
        handle = await self._key_manager.get_private_encryption_key(
            envelope.key_version
        )
        with handle.use_key() as private_key:
            shared = cast(X25519PrivateKey, private_key).exchange(
                X25519PublicKey.from_public_bytes(
                    self._decode(envelope.ephemeral_public_key)
                )
            )
        wrapping_key = self._derive_wrapping_key(
            shared, response.id, envelope.recipient_id, envelope.key_version
        )
        return AESGCM(wrapping_key).decrypt(
            self._decode(envelope.nonce),
            self._decode(envelope.encrypted_key),
            self._key_aad(
                response.id,
                response.conversation_id,
                envelope.recipient_id,
                envelope.key_version,
                self._decode(envelope.ephemeral_public_key),
            ),
        )

    def _message_aad(self, command: EncryptMessageCommand) -> bytes:
        return canonical_json_bytes(
            {
                "attachment_ids": [str(item) for item in command.attachment_ids],
                "client_created_at": command.client_created_at,
                "content_algorithm": ContentEncryptionAlgorithm.AES_256_GCM_V1.value,
                "conversation_id": command.conversation_id,
                "message_id": command.message_id,
                "message_type": command.message_type.value,
                "message_version": 1,
                "protocol_version": self._protocol_version,
                "reply_to_id": command.reply_to_id,
                "sender_id": command.sender_id,
            }
        )

    @staticmethod
    def _response_aad(response: EncryptedMessageResponse) -> bytes:
        return canonical_json_bytes(
            {
                "attachment_ids": [str(item) for item in response.attachment_ids],
                "client_created_at": response.sent_at,
                "content_algorithm": response.content_algorithm.value,
                "conversation_id": response.conversation_id,
                "message_id": response.id,
                "message_type": response.message_type.value,
                "message_version": response.version,
                "protocol_version": response.protocol_version,
                "reply_to_id": response.reply_to_id,
                "sender_id": response.sender_id,
            }
        )

    def _derive_wrapping_key(
        self, shared: bytes, message_id: UUID, recipient_id: UUID, key_version: int
    ) -> bytes:
        return HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"bluebubbles-message-wrap-v1",
            info=canonical_json_bytes(
                {
                    "algorithm": (
                        KeyEnvelopeAlgorithm.X25519_HKDF_SHA256_AES_256_GCM_V1.value
                    ),
                    "message_id": message_id,
                    "protocol_version": self._protocol_version,
                    "recipient_id": recipient_id,
                    "recipient_key_version": key_version,
                }
            ),
        ).derive(shared)

    def _key_aad(
        self,
        message_id: UUID,
        conversation_id: UUID,
        recipient_id: UUID,
        key_version: int,
        ephemeral_public_key: bytes,
    ) -> bytes:
        return canonical_json_bytes(
            {
                "content_algorithm": ContentEncryptionAlgorithm.AES_256_GCM_V1.value,
                "conversation_id": conversation_id,
                "envelope_algorithm": (
                    KeyEnvelopeAlgorithm.X25519_HKDF_SHA256_AES_256_GCM_V1.value
                ),
                "ephemeral_public_key": self._encode(ephemeral_public_key),
                "message_id": message_id,
                "protocol_version": self._protocol_version,
                "recipient_id": recipient_id,
                "recipient_key_version": key_version,
            }
        )

    @staticmethod
    def _signed_bytes(
        *,
        aad: bytes,
        ciphertext: bytes,
        nonce: bytes,
        recipient_digest: str,
        signing_key_version: int,
    ) -> bytes:
        return canonical_json_bytes(
            {
                "aad": base64.b64encode(aad).decode("ascii"),
                "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
                "nonce": base64.b64encode(nonce).decode("ascii"),
                "recipient_envelope_digest": recipient_digest,
                "signature_algorithm": SignatureAlgorithm.ED25519_V1.value,
                "signing_key_version": signing_key_version,
            }
        )

    def _validate_command(self, command: EncryptMessageCommand) -> None:
        if command.client_created_at.tzinfo is None:
            raise ValueError("Client message timestamp must be timezone-aware")
        if len(command.plaintext) > 8000:
            raise ValueError("Message text exceeds the Version 1 limit")
        recipients = [item.recipient_id for item in command.recipient_public_keys]
        if command.sender_id not in recipients or len(recipients) != len(
            set(recipients)
        ):
            raise ValueError("Recipients must be unique and include the sender")
        if len(command.attachment_ids) != len(set(command.attachment_ids)):
            raise ValueError("Attachment identifiers must be unique")

    @staticmethod
    def _encode(value: bytes) -> str:
        return base64.b64encode(value).decode("ascii")

    @staticmethod
    def _decode(value: str) -> bytes:
        return base64.b64decode(value, validate=True)
