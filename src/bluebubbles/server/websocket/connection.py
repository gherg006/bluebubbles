"""One authenticated WebSocket connection and serialised frame writes."""

from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import UUID

from fastapi import WebSocket

from bluebubbles.shared.protocol.envelope import WebSocketEventEnvelope


class WebSocketConnection:
    """Own identity, heartbeat state, subscriptions, and one send lock."""

    def __init__(
        self,
        websocket: WebSocket,
        connection_id: UUID,
        user_id: UUID,
        session_id: UUID,
        device_id: UUID,
        connected_at: datetime,
    ) -> None:
        self.websocket = websocket
        self.connection_id = connection_id
        self.user_id = user_id
        self.session_id = session_id
        self.device_id = device_id
        self.connected_at = connected_at
        self.last_heartbeat = connected_at
        self.subscriptions: set[str] = set()
        self._send_lock = asyncio.Lock()
        self._closed = False

    async def send(self, event: WebSocketEventEnvelope) -> None:
        """Send one validated JSON envelope without overlapping frame writes."""
        async with self._send_lock:
            if self._closed:
                raise RuntimeError("WebSocket connection is closed")
            await self.websocket.send_text(event.model_dump_json())

    async def send_json(self, value: object) -> None:
        """Send a validated acknowledgement-like JSON value serially."""
        async with self._send_lock:
            if self._closed:
                raise RuntimeError("WebSocket connection is closed")
            await self.websocket.send_json(value)

    async def close(self, code: int, reason: str) -> None:
        """Close once using a bounded non-sensitive reason."""
        async with self._send_lock:
            if self._closed:
                return
            self._closed = True
            await self.websocket.close(code=code, reason=reason[:123])

    def mark_heartbeat(self, timestamp: datetime) -> None:
        if timestamp.tzinfo is None or timestamp < self.last_heartbeat:
            raise ValueError("Heartbeat timestamp must be aware and monotonic")
        self.last_heartbeat = timestamp
