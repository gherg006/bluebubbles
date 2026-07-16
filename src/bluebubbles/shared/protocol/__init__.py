"""Version negotiation, WebSocket events, and canonical serialisation."""

from bluebubbles.shared.protocol.envelope import (
    ProtocolMetadata,
    WebSocketAcknowledgement,
    WebSocketEventEnvelope,
)
from bluebubbles.shared.protocol.event_types import WebSocketEventType

__all__ = [
    "ProtocolMetadata",
    "WebSocketAcknowledgement",
    "WebSocketEventEnvelope",
    "WebSocketEventType",
]
