"""Windows-client-only message models with explicit plaintext boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from bluebubbles.shared.models.messages import MessageDeliveryStatus, MessageType
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    SignatureAlgorithm,
)


@dataclass(frozen=True, slots=True)
class DecryptedMessageContent:
    """Hold authorised plaintext only in client memory."""

    text: str
    reply_preview: str | None = None

    def __post_init__(self) -> None:
        if "\x00" in self.text:
            raise ValueError("Message content cannot contain null characters")


@dataclass(frozen=True, slots=True)
class EncryptedTransportData:
    """Hold bytes received from or submitted to the server."""

    algorithm: ContentEncryptionAlgorithm
    ciphertext: bytes = field(repr=False)
    nonce: bytes = field(repr=False)
    signature_algorithm: SignatureAlgorithm
    signature: bytes = field(repr=False)
    sender_key_version: int

    def __post_init__(self) -> None:
        if not self.ciphertext or not self.nonce or not self.signature:
            raise ValueError("Encrypted transport data is incomplete")
        if self.sender_key_version < 1:
            raise ValueError("Sender key version must be positive")


@dataclass(frozen=True, slots=True)
class EncryptedLocalContent:
    """Hold independently encrypted local-cache content."""

    ciphertext: bytes = field(repr=False)
    nonce: bytes = field(repr=False)
    key_reference: str

    def __post_init__(self) -> None:
        if not self.ciphertext or not self.nonce or not self.key_reference:
            raise ValueError("Encrypted local-cache content is incomplete")


class MessageDisplayState(StrEnum):
    """Represent client presentation state without changing server truth."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    DECRYPTION_FAILED = "decryption_failed"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True)
class MessageDraft:
    """Represent unsent client plaintext that must be encrypted before persistence."""

    conversation_id: UUID
    text: str
    reply_to_id: UUID | None = None
    attachment_ids: tuple[UUID, ...] = ()
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if len(self.attachment_ids) != len(set(self.attachment_ids)):
            raise ValueError("Draft attachment identifiers must be unique")
        if not self.text.strip() and not self.attachment_ids:
            raise ValueError("A draft requires text or an attachment")


@dataclass(frozen=True, slots=True)
class ClientMessage:
    """Combine transport, local cache, and transient display representations."""

    id: UUID
    client_message_id: UUID
    conversation_id: UUID
    sender_id: UUID
    message_type: MessageType
    sent_at: datetime
    transport: EncryptedTransportData | None
    local_content: EncryptedLocalContent | None
    decrypted_content: DecryptedMessageContent | None = field(default=None, repr=False)
    delivery_status: MessageDeliveryStatus = MessageDeliveryStatus.PENDING
    display_state: MessageDisplayState = MessageDisplayState.PENDING
    reply_to_id: UUID | None = None
    attachment_ids: tuple[UUID, ...] = ()

    def with_decrypted_content(self, content: DecryptedMessageContent) -> ClientMessage:
        """Return a new in-memory message carrying authorised plaintext."""
        return replace(self, decrypted_content=content)

    def without_plaintext(self) -> ClientMessage:
        """Return a copy suitable for leaving an authorised display context."""
        return replace(self, decrypted_content=None)

    def with_display_state(self, state: MessageDisplayState) -> ClientMessage:
        """Return a new presentation-state snapshot."""
        return replace(self, display_state=state)
