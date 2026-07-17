"""Plaintext-free durable application-event construction."""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from uuid import uuid4

from bluebubbles.server.domain.messages import Message
from bluebubbles.server.domain.outbox import OutboxEvent
from bluebubbles.shared.models.messages import (
    RecipientKeyEnvelopeRequest,
    recipient_envelope_digest,
)


class EventFactory:
    """Build durable outbox facts after validating server domain objects."""

    def __init__(self, protocol_version: int = 1) -> None:
        self._protocol_version = protocol_version

    def message_stored(self, message: Message) -> OutboxEvent:
        return self._message_event("MESSAGE_RECEIVED", message)

    def message_updated(self, message: Message) -> OutboxEvent:
        return self._message_event("MESSAGE_UPDATED", message)

    def message_deleted(self, message: Message, deleted_at: datetime) -> OutboxEvent:
        now = datetime.now(UTC)
        return OutboxEvent(
            id=uuid4(),
            created_at=now,
            updated_at=now,
            event_type="MESSAGE_DELETED",
            aggregate_type="message",
            aggregate_id=message.id,
            protocol_version=self._protocol_version,
            available_at=now,
            payload={
                "recipient_ids": [
                    str(key.recipient_id) for key in message.recipient_keys
                ],
                "data": {
                    "message_id": str(message.id),
                    "conversation_id": str(message.conversation_id),
                    "deleted_at": deleted_at.isoformat(),
                },
            },
        )

    def _message_event(self, event_type: str, message: Message) -> OutboxEvent:
        now = datetime.now(UTC)
        keys = tuple(self._key_request(key) for key in message.recipient_keys)
        return OutboxEvent(
            id=uuid4(),
            created_at=now,
            updated_at=now,
            event_type=event_type,
            aggregate_type="message",
            aggregate_id=message.id,
            protocol_version=self._protocol_version,
            available_at=now,
            payload={
                "recipient_ids": [
                    str(key.recipient_id) for key in message.recipient_keys
                ],
                "recipient_keys": {
                    str(key.recipient_id): self._key_request(key).model_dump(
                        mode="json"
                    )
                    for key in message.recipient_keys
                },
                "recipient_envelope_digest": recipient_envelope_digest(keys),
                "data": {
                    "id": str(message.id),
                    "client_message_id": str(message.client_message_id),
                    "conversation_id": str(message.conversation_id),
                    "sender_id": str(message.sender_id),
                    "message_type": message.message_type.value,
                    "content_algorithm": message.content_algorithm.value,
                    "ciphertext": self._encode(message.ciphertext),
                    "nonce": self._encode(message.nonce),
                    "signature_algorithm": message.signature_algorithm.value,
                    "signature": self._encode(message.signature),
                    "sender_key_version": message.sender_key_version,
                    "protocol_version": self._protocol_version,
                    "sent_at": message.sent_at.isoformat(),
                    "edited_at": (
                        message.edited_at.isoformat() if message.edited_at else None
                    ),
                    "reply_to_id": (
                        str(message.reply_to_id) if message.reply_to_id else None
                    ),
                    "attachment_ids": [str(item) for item in message.attachment_ids],
                    "delivery_status": "stored",
                    "version": message.version,
                },
            },
        )

    @staticmethod
    def _key_request(key: object) -> RecipientKeyEnvelopeRequest:
        from bluebubbles.server.domain.messages import MessageRecipientKey

        selected = key
        if not isinstance(selected, MessageRecipientKey):
            raise TypeError("Expected a message recipient key")
        return RecipientKeyEnvelopeRequest(
            recipient_id=selected.recipient_id,
            key_version=selected.key_version,
            algorithm=selected.algorithm,
            ephemeral_public_key=EventFactory._encode(selected.ephemeral_public_key),
            nonce=EventFactory._encode(selected.nonce),
            encrypted_key=EventFactory._encode(selected.encrypted_key),
        )

    @staticmethod
    def _encode(value: bytes) -> str:
        return base64.b64encode(value).decode("ascii")
