"""Encrypted server message entities and delivery-state invariants."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID

from bluebubbles.server.domain.common import BaseEntity
from bluebubbles.shared.models.messages import MessageDeliveryStatus, MessageType
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    KeyEnvelopeAlgorithm,
    SignatureAlgorithm,
)


@dataclass(kw_only=True)
class MessageRecipientKey(BaseEntity):
    """Store an encrypted message key for one authorised recipient."""

    message_id: UUID
    recipient_id: UUID
    key_version: int
    algorithm: KeyEnvelopeAlgorithm
    ephemeral_public_key: bytes
    nonce: bytes
    encrypted_key: bytes = field(repr=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.key_version < 1 or not self.encrypted_key:
            raise ValueError("Recipient key version and encrypted key are required")


@dataclass(kw_only=True)
class Message(BaseEntity):
    """Represent an encrypted envelope; plaintext is deliberately impossible."""

    client_message_id: UUID
    conversation_id: UUID
    sender_id: UUID
    message_type: MessageType
    content_algorithm: ContentEncryptionAlgorithm
    ciphertext: bytes = field(repr=False)
    nonce: bytes = field(repr=False)
    signature_algorithm: SignatureAlgorithm
    signature: bytes = field(repr=False)
    sender_key_version: int
    sent_at: datetime
    recipient_keys: tuple[MessageRecipientKey, ...]
    reply_to_id: UUID | None = None
    attachment_ids: tuple[UUID, ...] = ()
    edited_at: datetime | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.ciphertext or not self.signature or self.sender_key_version < 1:
            raise ValueError("Complete encrypted and signed message data is required")
        recipients = [key.recipient_id for key in self.recipient_keys]
        if not recipients or len(recipients) != len(set(recipients)):
            raise ValueError("Recipient keys must be non-empty and unique")
        if len(self.attachment_ids) != len(set(self.attachment_ids)):
            raise ValueError("Attachment identifiers must be unique")

    def can_edit(self, actor_id: UUID, at: datetime, window: timedelta) -> bool:
        """Return whether the sender remains inside the edit window."""
        return (
            not self.is_deleted
            and actor_id == self.sender_id
            and at <= self.sent_at + window
        )

    def can_delete(self, actor_id: UUID, at: datetime, window: timedelta) -> bool:
        """Return whether the sender remains inside the delete window."""
        return (
            not self.is_deleted
            and actor_id == self.sender_id
            and at <= self.sent_at + window
        )

    def replace_envelope(
        self,
        *,
        ciphertext: bytes,
        nonce: bytes,
        signature: bytes,
        recipient_keys: tuple[MessageRecipientKey, ...],
        at: datetime,
    ) -> None:
        """Replace encrypted content while retaining immutable message identity."""
        if not ciphertext or not nonce or not signature or not recipient_keys:
            raise ValueError("Complete replacement envelope is required")
        ids = [key.recipient_id for key in recipient_keys]
        if len(ids) != len(set(ids)):
            raise ValueError("Replacement recipient keys must be unique")
        self.ciphertext = ciphertext
        self.nonce = nonce
        self.signature = signature
        self.recipient_keys = recipient_keys
        self.edited_at = at
        self.touch(at)


@dataclass(kw_only=True)
class MessageDelivery(BaseEntity):
    """Track one recipient's server-visible delivery state."""

    message_id: UUID
    recipient_id: UUID
    status: MessageDeliveryStatus = MessageDeliveryStatus.PENDING
    status_at: datetime

    def transition(self, target: MessageDeliveryStatus, at: datetime) -> None:
        """Advance through an allowed delivery transition."""
        validate_delivery_transition(self.status, target)
        self.status = target
        self.status_at = at
        self.touch(at)


@dataclass(frozen=True, slots=True)
class MessageVersion:
    """Retain an immutable prior encrypted envelope for audit-safe edits."""

    message_id: UUID
    version: int
    ciphertext: bytes = field(repr=False)
    nonce: bytes = field(repr=False)
    signature: bytes = field(repr=False)
    created_at: datetime

    def __post_init__(self) -> None:
        validate_version(self.version)


def validate_version(version: int) -> None:
    """Require a positive optimistic or message version."""
    if version < 1:
        raise ValueError("Version must be at least one")


def validate_delivery_transition(
    current: MessageDeliveryStatus, target: MessageDeliveryStatus
) -> None:
    """Reject delivery-state regression and transitions after failure."""
    allowed = {
        MessageDeliveryStatus.PENDING: {
            MessageDeliveryStatus.STORED,
            MessageDeliveryStatus.FAILED,
        },
        MessageDeliveryStatus.STORED: {
            MessageDeliveryStatus.DELIVERED,
            MessageDeliveryStatus.FAILED,
        },
        MessageDeliveryStatus.DELIVERED: {MessageDeliveryStatus.READ},
        MessageDeliveryStatus.READ: set(),
        MessageDeliveryStatus.FAILED: set(),
    }
    if target not in allowed[current]:
        raise ValueError(f"Invalid delivery transition: {current} -> {target}")
