"""Recipient-filtered publication of committed durable events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from bluebubbles.server.domain.outbox import OutboxEvent
from bluebubbles.server.websocket.manager import WebSocketConnectionManager
from bluebubbles.shared.protocol.envelope import WebSocketEventEnvelope
from bluebubbles.shared.protocol.event_types import WebSocketEventType


@dataclass(frozen=True, slots=True)
class PublicationResult:
    recipients: int
    connected_deliveries: int
    failed_connections: int


class EventPublisher:
    """Publish outbox events without treating sockets as durable storage."""

    def __init__(self, websocket_manager: WebSocketConnectionManager) -> None:
        self._websocket_manager = websocket_manager

    async def publish(self, event: OutboxEvent) -> PublicationResult:
        recipients_raw = event.payload.get("recipient_ids", [])
        if not isinstance(recipients_raw, list):
            raise ValueError("Outbox recipient list is invalid")
        recipients = tuple(UUID(str(value)) for value in recipients_raw)
        delivered = failed = 0
        for recipient in recipients:
            envelope = self._envelope_for(event, recipient)
            summary = await self._websocket_manager.send_to_user(recipient, envelope)
            delivered += summary.delivered
            failed += summary.failed
        return PublicationResult(len(recipients), delivered, failed)

    def _envelope_for(
        self, event: OutboxEvent, recipient_id: UUID
    ) -> WebSocketEventEnvelope:
        raw_data = event.payload.get("data")
        if not isinstance(raw_data, dict):
            raise ValueError("Outbox event data is invalid")
        data = dict(raw_data)
        if event.event_type in {"MESSAGE_RECEIVED", "MESSAGE_UPDATED"}:
            keys = event.payload.get("recipient_keys")
            digest = event.payload.get("recipient_envelope_digest")
            if not isinstance(keys, dict) or not isinstance(digest, str):
                raise ValueError("Encrypted message outbox payload is incomplete")
            selected = keys.get(str(recipient_id))
            if not isinstance(selected, dict):
                raise ValueError("Recipient message key is missing")
            data["encrypted_key"] = selected
            data["recipient_envelope_digest"] = digest
            data = {"message": data}
        return WebSocketEventEnvelope(
            event_id=event.id,
            event_type=WebSocketEventType(event.event_type),
            protocol_version=event.protocol_version,
            timestamp=event.created_at,
            correlation_id=event.id,
            data=data,
        )

    async def publish_transient(
        self,
        recipients: set[UUID],
        event_type: WebSocketEventType,
        event_id: UUID,
        data: dict[str, object],
        protocol_version: int = 1,
    ) -> PublicationResult:
        envelope = WebSocketEventEnvelope(
            event_id=event_id,
            event_type=event_type,
            protocol_version=protocol_version,
            timestamp=datetime.now(UTC),
            correlation_id=event_id,
            data=data,
        )
        delivered = failed = 0
        for recipient in recipients:
            summary = await self._websocket_manager.send_to_user(recipient, envelope)
            delivered += summary.delivered
            failed += summary.failed
        return PublicationResult(len(recipients), delivered, failed)
