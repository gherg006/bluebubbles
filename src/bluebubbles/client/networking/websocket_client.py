"""Authenticated WebSocket client with heartbeat and bounded reconnection."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed

from bluebubbles.client.configuration.settings import (
    ClientNetworkSettings,
    ServerConnectionSettings,
)
from bluebubbles.client.networking.event_dispatcher import ClientEventDispatcher
from bluebubbles.client.services.sessions import ClientSessionService
from bluebubbles.shared.errors.exceptions import NetworkError, ProtocolError
from bluebubbles.shared.protocol.envelope import WebSocketEventEnvelope
from bluebubbles.shared.protocol.event_types import WebSocketEventType
from bluebubbles.shared.protocol.events import HeartbeatEventData


class WebSocketClientState(StrEnum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


class WebSocketClient:
    """Maintain one authenticated connection and suppress reconnect on logout."""

    def __init__(
        self,
        settings: ServerConnectionSettings,
        network_settings: ClientNetworkSettings,
        session_service: ClientSessionService,
        event_dispatcher: ClientEventDispatcher,
        logger: logging.Logger,
        *,
        protocol_version: int = 1,
        on_authenticated: Callable[[UUID | None], Awaitable[None]] | None = None,
        on_event_processed: Callable[[UUID], Awaitable[None]] | None = None,
    ) -> None:
        self._settings = settings
        self._network_settings = network_settings
        self._session_service = session_service
        self._event_dispatcher = event_dispatcher
        self._logger = logger
        self._protocol_version = protocol_version
        self._on_authenticated = on_authenticated
        self._on_event_processed = on_event_processed
        self._connection: ClientConnection | None = None
        self._receive_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._reconnect_task: asyncio.Task[None] | None = None
        self._last_event_id: UUID | None = None
        self._state = WebSocketClientState.DISCONNECTED
        self._stop_requested = False
        self._connect_lock = asyncio.Lock()
        self._send_lock = asyncio.Lock()
        self._connected = asyncio.Event()

    @property
    def state(self) -> WebSocketClientState:
        return self._state

    async def connect(self) -> None:
        """Open and authenticate exactly one active connection attempt."""
        async with self._connect_lock:
            if (
                self._connection is not None
                and self._state is WebSocketClientState.CONNECTED
            ):
                return
            self._stop_requested = False
            self._state = WebSocketClientState.CONNECTING
            token = await self._session_service.get_access_token()
            try:
                connection = await asyncio.wait_for(
                    connect(str(self._settings.websocket_url)),
                    timeout=self._settings.connect_timeout_seconds,
                )
                authentication = WebSocketEventEnvelope(
                    event_id=uuid4(),
                    event_type=WebSocketEventType.AUTHENTICATE,
                    protocol_version=self._protocol_version,
                    timestamp=datetime.now(UTC),
                    data={
                        "access_token": token,
                        "last_event_id": (
                            str(self._last_event_id) if self._last_event_id else None
                        ),
                    },
                )
                await connection.send(authentication.model_dump_json())
                raw = await asyncio.wait_for(
                    connection.recv(), timeout=self._settings.connect_timeout_seconds
                )
                accepted = WebSocketEventEnvelope.model_validate_json(raw)
                if accepted.event_type is not WebSocketEventType.AUTHENTICATED:
                    raise ProtocolError()
            except BaseException as error:
                self._state = WebSocketClientState.DISCONNECTED
                raise NetworkError() from error
            self._connection = connection
            self._state = WebSocketClientState.CONNECTED
            self._connected.set()
            self._receive_task = asyncio.create_task(
                self._receive_loop(), name="bluebubbles-websocket-receive"
            )
            self._heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(), name="bluebubbles-websocket-heartbeat"
            )
            if self._on_authenticated is not None:
                await self._on_authenticated(self._last_event_id)

    async def disconnect(self) -> None:
        """Close manually and suppress all automatic reconnection."""
        self._stop_requested = True
        self._connected.clear()
        tasks = tuple(
            task
            for task in (
                self._receive_task,
                self._heartbeat_task,
                self._reconnect_task,
            )
            if task is not None and task is not asyncio.current_task()
        )
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._receive_task = self._heartbeat_task = self._reconnect_task = None
        connection = self._connection
        self._connection = None
        if connection is not None:
            await connection.close(code=1000, reason="Client disconnect")
        self._state = WebSocketClientState.DISCONNECTED

    async def send_event(self, event: WebSocketEventEnvelope) -> None:
        await self.wait_until_connected(self._settings.connect_timeout_seconds)
        async with self._send_lock:
            if self._connection is None:
                raise NetworkError()
            try:
                await self._connection.send(event.model_dump_json())
            except ConnectionClosed as error:
                self._schedule_reconnect()
                raise NetworkError() from error

    async def wait_until_connected(self, timeout: float) -> None:
        try:
            await asyncio.wait_for(self._connected.wait(), timeout=timeout)
        except TimeoutError as error:
            raise NetworkError() from error

    async def _receive_loop(self) -> None:
        assert self._connection is not None
        try:
            async for raw in self._connection:
                value = json.loads(raw)
                if isinstance(value, dict) and "accepted" in value:
                    continue
                envelope = WebSocketEventEnvelope.model_validate(value)
                await self._event_dispatcher.dispatch(envelope)
                self._last_event_id = envelope.event_id
                if self._on_event_processed is not None:
                    await self._on_event_processed(envelope.event_id)
        except (ConnectionClosed, ValueError, json.JSONDecodeError) as error:
            self._logger.warning(
                "WebSocket receive ended",
                extra={"failure_category": type(error).__name__},
            )
        finally:
            self._connected.clear()
            if not self._stop_requested:
                self._schedule_reconnect()

    async def _heartbeat_loop(self) -> None:
        try:
            while not self._stop_requested:
                await asyncio.sleep(self._network_settings.websocket_heartbeat_seconds)
                await self.send_event(
                    WebSocketEventEnvelope(
                        event_id=uuid4(),
                        event_type=WebSocketEventType.HEARTBEAT,
                        protocol_version=self._protocol_version,
                        timestamp=datetime.now(UTC),
                        data=HeartbeatEventData(sent_at=datetime.now(UTC)).model_dump(
                            mode="json"
                        ),
                    )
                )
        except (asyncio.CancelledError, NetworkError):
            return

    def _schedule_reconnect(self) -> None:
        if (
            self._stop_requested
            or not self._settings.automatic_reconnect
            or (self._reconnect_task is not None and not self._reconnect_task.done())
        ):
            return
        self._reconnect_task = asyncio.create_task(
            self._reconnect_loop(), name="bluebubbles-websocket-reconnect"
        )

    async def _reconnect_loop(self) -> None:
        self._state = WebSocketClientState.RECONNECTING
        delay = self._network_settings.retry_base_delay_seconds
        while not self._stop_requested:
            await asyncio.sleep(delay)
            self._connection = None
            try:
                await self.connect()
                return
            except NetworkError:
                delay = min(
                    delay * 2, self._network_settings.retry_maximum_delay_seconds
                )
