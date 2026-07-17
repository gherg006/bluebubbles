"""Task 14 client WebSocket authentication, dispatch, and shutdown evidence."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from bluebubbles.client.configuration.settings import (
    ClientNetworkSettings,
    ServerConnectionSettings,
)
from bluebubbles.client.networking.event_dispatcher import ClientEventDispatcher
from bluebubbles.client.networking.websocket_client import (
    WebSocketClient,
    WebSocketClientState,
)
from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.errors.exceptions import NetworkError
from bluebubbles.shared.protocol.envelope import WebSocketEventEnvelope
from bluebubbles.shared.protocol.event_types import WebSocketEventType
from bluebubbles.shared.protocol.events import (
    AuthenticatedEventData,
    HeartbeatEventData,
)

NOW = datetime.now(UTC)


class _Sessions:
    async def get_access_token(self) -> str:
        return "real-access-token"


class _Connection:
    def __init__(self) -> None:
        self.sent: list[str] = []
        self.closed: list[tuple[int, str]] = []
        self.queue: asyncio.Queue[str | None] = asyncio.Queue()
        self.authenticated = WebSocketEventEnvelope(
            event_id=uuid4(),
            event_type=WebSocketEventType.AUTHENTICATED,
            protocol_version=1,
            timestamp=NOW,
            data=AuthenticatedEventData(user_id=uuid4(), session_id=uuid4()).model_dump(
                mode="json"
            ),
        ).model_dump_json()

    async def send(self, value: str) -> None:
        self.sent.append(value)

    async def recv(self) -> str:
        return self.authenticated

    async def close(self, code: int, reason: str) -> None:
        self.closed.append((code, reason))
        await self.queue.put(None)

    def __aiter__(self) -> _Connection:
        return self

    async def __anext__(self) -> str:
        value = await self.queue.get()
        if value is None:
            raise StopAsyncIteration
        return value


def _event(event_id: UUID | None = None) -> WebSocketEventEnvelope:
    return WebSocketEventEnvelope(
        event_id=event_id or uuid4(),
        event_type=WebSocketEventType.HEARTBEAT,
        protocol_version=1,
        timestamp=NOW,
        data=HeartbeatEventData(sent_at=NOW).model_dump(mode="json"),
    )


@pytest.mark.asyncio
async def test_client_event_dispatcher_validates_and_deduplicates() -> None:
    received: list[ContractModel] = []

    async def handler(data: ContractModel, envelope: WebSocketEventEnvelope) -> None:
        del envelope
        received.append(data)

    dispatcher = ClientEventDispatcher(
        {WebSocketEventType.HEARTBEAT: handler}, deduplication_limit=1
    )
    first = _event()
    await dispatcher.dispatch(first)
    await dispatcher.dispatch(first)
    second = _event()
    await dispatcher.dispatch(second)
    await dispatcher.dispatch(first)
    assert len(received) == 3
    with pytest.raises(ValueError, match="positive"):
        ClientEventDispatcher({}, deduplication_limit=0)


@pytest.mark.asyncio
async def test_websocket_client_authenticates_sends_receives_and_disconnects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = _Connection()

    async def fake_connect(url: str) -> _Connection:
        assert url == "ws://127.0.0.1:9000/api/v1/ws"
        return connection

    monkeypatch.setattr(
        "bluebubbles.client.networking.websocket_client.connect", fake_connect
    )
    received: list[object] = []

    async def handler(data: ContractModel, envelope: WebSocketEventEnvelope) -> None:
        del data
        received.append(envelope.event_id)

    dispatcher = ClientEventDispatcher({WebSocketEventType.HEARTBEAT: handler})
    client = WebSocketClient(
        ServerConnectionSettings.model_validate(
            {
                "base_url": "http://127.0.0.1:9000",
                "websocket_url": "ws://127.0.0.1:9000/api/v1/ws",
                "connect_timeout_seconds": 1,
            }
        ),
        ClientNetworkSettings(websocket_heartbeat_seconds=60),
        _Sessions(),  # type: ignore[arg-type]
        dispatcher,
        logging.getLogger("test-client-websocket"),
    )
    await client.connect()
    assert client.state.value == WebSocketClientState.CONNECTED.value
    authentication = json.loads(connection.sent[0])
    assert authentication["data"]["access_token"] == "real-access-token"
    incoming = _event()
    await connection.queue.put(incoming.model_dump_json())
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert received == [incoming.event_id]
    outgoing = _event()
    await client.send_event(outgoing)
    assert json.loads(connection.sent[-1])["event_id"] == str(outgoing.event_id)
    await client.wait_until_connected(0.1)
    await client.disconnect()
    assert client.state.value == WebSocketClientState.DISCONNECTED.value
    assert connection.closed == [(1000, "Client disconnect")]


@pytest.mark.asyncio
async def test_websocket_client_reports_connection_and_wait_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failed_connect(url: str) -> object:
        del url
        raise OSError("offline")

    monkeypatch.setattr(
        "bluebubbles.client.networking.websocket_client.connect", failed_connect
    )
    client = WebSocketClient(
        ServerConnectionSettings.model_validate(
            {
                "base_url": "http://127.0.0.1:9000",
                "websocket_url": "ws://127.0.0.1:9000/api/v1/ws",
                "connect_timeout_seconds": 0.1,
            }
        ),
        ClientNetworkSettings(),
        _Sessions(),  # type: ignore[arg-type]
        ClientEventDispatcher({}),
        logging.getLogger("test-client-websocket-failure"),
    )
    with pytest.raises(NetworkError):
        await client.connect()
    with pytest.raises(NetworkError):
        await client.wait_until_connected(0.01)
