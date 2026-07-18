"""Concurrent indexes and delivery operations for authenticated sockets."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from uuid import UUID

from bluebubbles.server.websocket.connection import WebSocketConnection
from bluebubbles.shared.protocol.envelope import WebSocketEventEnvelope


@dataclass(frozen=True, slots=True)
class DeliverySummary:
    attempted: int
    delivered: int
    failed: int


class WebSocketConnectionManager:
    """Index sockets by connection, user, and session under one async lock."""

    def __init__(self) -> None:
        self._connections_by_id: dict[UUID, WebSocketConnection] = {}
        self._connection_ids_by_user: dict[UUID, set[UUID]] = {}
        self._connection_ids_by_session: dict[UUID, set[UUID]] = {}
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Initialise the in-memory registry; construction already makes it ready."""

    async def stop(self) -> None:
        """Notify and close every remaining socket during graceful shutdown."""
        await self.close_all()

    async def register(self, connection: WebSocketConnection) -> None:
        async with self._lock:
            if connection.connection_id in self._connections_by_id:
                raise ValueError("Connection identifier is already registered")
            self._connections_by_id[connection.connection_id] = connection
            self._connection_ids_by_user.setdefault(connection.user_id, set()).add(
                connection.connection_id
            )
            self._connection_ids_by_session.setdefault(
                connection.session_id, set()
            ).add(connection.connection_id)

    async def unregister(self, connection_id: UUID) -> None:
        async with self._lock:
            connection = self._connections_by_id.pop(connection_id, None)
            if connection is None:
                return
            self._discard_index(
                self._connection_ids_by_user, connection.user_id, connection_id
            )
            self._discard_index(
                self._connection_ids_by_session,
                connection.session_id,
                connection_id,
            )

    async def send_to_user(
        self, user_id: UUID, event: WebSocketEventEnvelope
    ) -> DeliverySummary:
        connections = await self._connections_for(self._connection_ids_by_user, user_id)
        return await self._send(connections, event)

    async def send_to_session(
        self, session_id: UUID, event: WebSocketEventEnvelope
    ) -> DeliverySummary:
        connections = await self._connections_for(
            self._connection_ids_by_session, session_id
        )
        return await self._send(connections, event)

    async def disconnect_session(self, session_id: UUID, reason: str) -> int:
        connections = await self._connections_for(
            self._connection_ids_by_session, session_id
        )
        if connections:
            await asyncio.gather(
                *(connection.close(1008, reason) for connection in connections),
                return_exceptions=True,
            )
            for connection in connections:
                await self.unregister(connection.connection_id)
        return len(connections)

    async def disconnect_user(self, user_id: UUID, reason: str) -> int:
        connections = await self._connections_for(self._connection_ids_by_user, user_id)
        if connections:
            await asyncio.gather(
                *(connection.close(1008, reason) for connection in connections),
                return_exceptions=True,
            )
            for connection in connections:
                await self.unregister(connection.connection_id)
        return len(connections)

    async def session_revoked(self, session_id: UUID) -> None:
        await self.disconnect_session(session_id, "Session revoked")

    async def user_sessions_revoked(self, user_id: UUID) -> None:
        await self.disconnect_user(user_id, "Sessions revoked")

    async def close_all(self, reason: str = "Server shutdown") -> None:
        async with self._lock:
            connections = tuple(self._connections_by_id.values())
        await asyncio.gather(
            *(connection.close(1001, reason) for connection in connections),
            return_exceptions=True,
        )
        for connection in connections:
            await self.unregister(connection.connection_id)

    async def connection_count(self) -> int:
        async with self._lock:
            return len(self._connections_by_id)

    async def list_connections(self) -> tuple[WebSocketConnection, ...]:
        """Return a stable transient snapshot for authorised administration."""
        async with self._lock:
            return tuple(self._connections_by_id.values())

    async def disconnect_connection(self, connection_id: UUID, reason: str) -> bool:
        """Close one connection without changing its persistent session."""
        async with self._lock:
            connection = self._connections_by_id.get(connection_id)
        if connection is None:
            return False
        await connection.close(1008, reason[:123])
        await self.unregister(connection_id)
        return True

    async def _connections_for(
        self, index: dict[UUID, set[UUID]], key: UUID
    ) -> tuple[WebSocketConnection, ...]:
        async with self._lock:
            return tuple(
                self._connections_by_id[item]
                for item in index.get(key, set())
                if item in self._connections_by_id
            )

    async def _send(
        self,
        connections: tuple[WebSocketConnection, ...],
        event: WebSocketEventEnvelope,
    ) -> DeliverySummary:
        results = await asyncio.gather(
            *(connection.send(event) for connection in connections),
            return_exceptions=True,
        )
        failed_connections = [
            connection
            for connection, result in zip(connections, results, strict=True)
            if isinstance(result, BaseException)
        ]
        for connection in failed_connections:
            await self.unregister(connection.connection_id)
        return DeliverySummary(
            len(connections),
            len(connections) - len(failed_connections),
            len(failed_connections),
        )

    @staticmethod
    def _discard_index(
        index: dict[UUID, set[UUID]], key: UUID, connection_id: UUID
    ) -> None:
        identifiers = index.get(key)
        if identifiers is None:
            return
        identifiers.discard(connection_id)
        if not identifiers:
            index.pop(key, None)
