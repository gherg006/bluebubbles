"""Idempotent validated dispatch of server WebSocket events."""

from __future__ import annotations

from collections import deque
from collections.abc import Awaitable, Callable, Mapping

from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.protocol.envelope import WebSocketEventEnvelope
from bluebubbles.shared.protocol.event_types import WebSocketEventType
from bluebubbles.shared.protocol.events import validate_event_data

ClientEventHandler = Callable[[ContractModel, WebSocketEventEnvelope], Awaitable[None]]


class ClientEventDispatcher:
    """Validate data and suppress bounded duplicate event identifiers."""

    def __init__(
        self,
        handlers: Mapping[WebSocketEventType, ClientEventHandler],
        *,
        deduplication_limit: int = 10_000,
    ) -> None:
        if deduplication_limit < 1:
            raise ValueError("Deduplication limit must be positive")
        self._handlers = dict(handlers)
        self._limit = deduplication_limit
        self._processed_order: deque[object] = deque()
        self._processed: set[object] = set()

    async def dispatch(self, envelope: WebSocketEventEnvelope) -> None:
        if envelope.event_id in self._processed:
            return
        data = validate_event_data(envelope.event_type.value, envelope.data)
        handler = self._handlers.get(envelope.event_type)
        if handler is not None:
            await handler(data, envelope)
        self._processed.add(envelope.event_id)
        self._processed_order.append(envelope.event_id)
        while len(self._processed_order) > self._limit:
            self._processed.discard(self._processed_order.popleft())
