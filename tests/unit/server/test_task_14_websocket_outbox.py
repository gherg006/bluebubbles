"""Task 14 WebSocket concurrency, publication, dispatch, and worker evidence."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from bluebubbles.server.application import create_application
from bluebubbles.server.configuration.settings import ServerSettings, WorkerSettings
from bluebubbles.server.domain.messages import Message, MessageRecipientKey
from bluebubbles.server.domain.outbox import OutboxEvent
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.services.events import EventFactory
from bluebubbles.server.websocket.connection import WebSocketConnection
from bluebubbles.server.websocket.dispatcher import (
    WebSocketEventDispatcher,
    WebSocketRateLimiter,
)
from bluebubbles.server.websocket.handlers import WebSocketHandlers
from bluebubbles.server.websocket.manager import WebSocketConnectionManager
from bluebubbles.server.websocket.publisher import EventPublisher
from bluebubbles.server.workers.outbox import OutboxPublisherWorker, WorkerState
from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.models.messages import MessageType
from bluebubbles.shared.models.users import PresenceState
from bluebubbles.shared.protocol.envelope import WebSocketEventEnvelope
from bluebubbles.shared.protocol.event_types import WebSocketEventType
from bluebubbles.shared.protocol.events import (
    HeartbeatEventData,
    MessageStatusEventData,
    PresenceEventData,
    TypingEventData,
)
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    KeyEnvelopeAlgorithm,
    SignatureAlgorithm,
)

NOW = datetime.now(UTC)


class _Socket:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.text: list[str] = []
        self.json_values: list[object] = []
        self.closed: list[tuple[int, str]] = []

    async def send_text(self, value: str) -> None:
        if self.fail:
            raise RuntimeError("network")
        self.text.append(value)

    async def send_json(self, value: object) -> None:
        self.json_values.append(value)

    async def close(self, code: int, reason: str) -> None:
        self.closed.append((code, reason))


def _connection(
    socket: _Socket, user_id: UUID, session_id: UUID | None = None
) -> WebSocketConnection:
    return WebSocketConnection(
        socket,  # type: ignore[arg-type]
        uuid4(),
        user_id,
        session_id or uuid4(),
        uuid4(),
        NOW,
    )


def _event(event_id: UUID | None = None) -> WebSocketEventEnvelope:
    return WebSocketEventEnvelope(
        event_id=event_id or uuid4(),
        event_type=WebSocketEventType.HEARTBEAT,
        protocol_version=1,
        timestamp=NOW,
        data=HeartbeatEventData(sent_at=NOW).model_dump(mode="json"),
    )


def _message(users: tuple[UUID, ...]) -> Message:
    message_id = uuid4()
    keys = tuple(
        MessageRecipientKey(
            id=uuid4(),
            created_at=NOW,
            updated_at=NOW,
            message_id=message_id,
            recipient_id=user,
            key_version=1,
            algorithm=KeyEnvelopeAlgorithm.X25519_HKDF_SHA256_AES_256_GCM_V1,
            ephemeral_public_key=b"p" * 32,
            nonce=b"n" * 12,
            encrypted_key=b"wrapped",
        )
        for user in users
    )
    return Message(
        id=message_id,
        created_at=NOW,
        updated_at=NOW,
        client_message_id=message_id,
        conversation_id=uuid4(),
        sender_id=users[0],
        message_type=MessageType.TEXT,
        content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
        ciphertext=b"ciphertext",
        nonce=b"m" * 12,
        signature_algorithm=SignatureAlgorithm.ED25519_V1,
        signature=b"s" * 64,
        sender_key_version=1,
        sent_at=NOW,
        recipient_keys=keys,
    )


@pytest.mark.asyncio
async def test_connection_manager_indexes_sends_and_cleans_failed_sockets() -> None:
    manager = WebSocketConnectionManager()
    user, session = uuid4(), uuid4()
    working_socket, failed_socket = _Socket(), _Socket(fail=True)
    working = _connection(working_socket, user, session)
    failed = _connection(failed_socket, user, session)
    await manager.register(working)
    await manager.register(failed)
    summary = await manager.send_to_user(user, _event())
    assert summary.attempted == 2 and summary.delivered == 1 and summary.failed == 1
    assert await manager.connection_count() == 1
    assert await manager.disconnect_session(session, "revoked") == 1
    assert working_socket.closed == [(1008, "revoked")]
    assert await manager.connection_count() == 0
    await manager.unregister(uuid4())
    await manager.start()
    await manager.stop()


@pytest.mark.asyncio
async def test_event_publisher_filters_keys_and_handles_offline_users() -> None:
    first, second, offline = uuid4(), uuid4(), uuid4()
    manager = WebSocketConnectionManager()
    first_socket, second_socket = _Socket(), _Socket()
    await manager.register(_connection(first_socket, first))
    await manager.register(_connection(second_socket, second))
    message = _message((first, second, offline))
    event = EventFactory().message_stored(message)
    result = await EventPublisher(manager).publish(event)
    assert result.recipients == 3 and result.connected_deliveries == 2
    first_payload = json.loads(first_socket.text[0])["data"]["message"]
    second_payload = json.loads(second_socket.text[0])["data"]["message"]
    assert UUID(first_payload["encrypted_key"]["recipient_id"]) == first
    assert UUID(second_payload["encrypted_key"]["recipient_id"]) == second
    assert "recipient_keys" not in first_payload


@pytest.mark.asyncio
async def test_dispatcher_validates_rate_limits_and_returns_structured_errors() -> None:
    socket = _Socket()
    connection = _connection(socket, uuid4())
    calls: list[ContractModel] = []

    async def heartbeat(
        selected: WebSocketConnection,
        data: ContractModel,
        envelope: WebSocketEventEnvelope,
    ) -> None:
        del selected, envelope
        calls.append(data)

    dispatcher = WebSocketEventDispatcher(
        {WebSocketEventType.HEARTBEAT: heartbeat}, WebSocketRateLimiter(1), {1}
    )
    event = _event()
    acknowledgement = await dispatcher.dispatch(connection, event.model_dump_json())
    assert acknowledgement is not None and acknowledgement.accepted
    rejected = await dispatcher.dispatch(connection, _event().model_dump_json())
    assert rejected is not None and not rejected.accepted
    assert json.loads(socket.text[-1])["event_type"] == "ERROR"
    assert len(calls) == 1
    dispatcher._rate_limiter.discard(connection.connection_id)  # noqa: SLF001
    malformed = await dispatcher.dispatch(connection, "not-json")
    assert malformed is not None and not malformed.accepted


class _OutboxRepository:
    def __init__(self, events: list[OutboxEvent]) -> None:
        self.events = events
        self.claimed = False
        self.published: list[UUID] = []
        self.failed: list[UUID] = []
        self.released = 0

    async def release_expired_locks(self, before: datetime) -> int:
        assert before.tzinfo is not None
        self.released += 1
        return 0

    async def claim_batch(
        self, worker_id: str, limit: int, now: datetime
    ) -> list[OutboxEvent]:
        assert worker_id and limit > 0 and now.tzinfo is not None
        if self.claimed:
            return []
        self.claimed = True
        return self.events

    async def mark_published(self, event_id: UUID, published_at: datetime) -> None:
        assert published_at.tzinfo is not None
        self.published.append(event_id)

    async def mark_failed(
        self, event_id: UUID, error_code: str, next_attempt_at: datetime
    ) -> None:
        assert error_code == "publication_failed" and next_attempt_at.tzinfo is not None
        self.failed.append(event_id)


class _WorkerUow:
    def __init__(self, repository: _OutboxRepository) -> None:
        self.outbox = repository
        self.commits = 0

    async def __aenter__(self) -> _WorkerUow:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1


class _WorkerFactory:
    def __init__(self, uow: _WorkerUow) -> None:
        self.uow = uow

    def __call__(self) -> _WorkerUow:
        return self.uow


class _SelectivePublisher:
    def __init__(self, failed_id: UUID | None = None) -> None:
        self.failed_id = failed_id

    async def publish(self, event: OutboxEvent) -> object:
        if event.id == self.failed_id:
            raise RuntimeError("offline")
        return object()


def _outbox_event() -> OutboxEvent:
    return OutboxEvent(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        event_type="MESSAGE_DELETED",
        aggregate_id=uuid4(),
        protocol_version=1,
        payload={"recipient_ids": [], "data": {}},
        available_at=NOW,
    )


@pytest.mark.asyncio
async def test_outbox_worker_isolates_poison_event_and_tracks_lifecycle() -> None:
    good, bad = _outbox_event(), _outbox_event()
    repository = _OutboxRepository([good, bad])
    uow = _WorkerUow(repository)
    settings = WorkerSettings(
        outbox_interval_seconds=0.01,
        outbox_batch_size=2,
        outbox_retry_base_seconds=1,
        outbox_retry_maximum_seconds=2,
    )
    worker = OutboxPublisherWorker(
        _WorkerFactory(uow),  # type: ignore[arg-type]
        _SelectivePublisher(bad.id),  # type: ignore[arg-type]
        settings,
        logging.getLogger("test-outbox"),
    )
    result = await worker.run_once()
    assert result.published == 1 and result.failed == 1
    assert repository.published == [good.id] and repository.failed == [bad.id]
    assert worker.status().state is WorkerState.FAILED
    await worker.start()
    await worker.stop()
    assert worker.status().state is WorkerState.STOPPED


def test_outbox_recursively_rejects_sensitive_nested_fields() -> None:
    with pytest.raises(ValueError, match="forbidden"):
        OutboxEvent(
            id=uuid4(),
            created_at=NOW,
            updated_at=NOW,
            event_type="unsafe",
            aggregate_id=uuid4(),
            protocol_version=1,
            payload={"data": {"plaintext_message": "never"}},
            available_at=NOW,
        )


class _HandlerMessages:
    def __init__(self) -> None:
        self.delivered = 0
        self.read = 0

    async def acknowledge_delivery(self, *args: object) -> None:
        self.delivered += 1

    async def mark_read_by_user_id(self, *args: object) -> None:
        self.read += 1


class _HandlerConversations:
    def __init__(self, users: set[UUID]) -> None:
        self.users = users

    async def get_active_members(self, conversation_id: UUID) -> list[object]:
        del conversation_id
        return [SimpleNamespace(user_id=user) for user in self.users]


class _HandlerUow:
    def __init__(self, users: set[UUID]) -> None:
        self.conversations = _HandlerConversations(users)

    async def __aenter__(self) -> _HandlerUow:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class _HandlerFactory:
    def __init__(self, users: set[UUID]) -> None:
        self.users = users

    def __call__(self) -> _HandlerUow:
        return _HandlerUow(self.users)


@pytest.mark.asyncio
async def test_websocket_handlers_derive_identity_and_publish_transient_events() -> (
    None
):
    sender, recipient, conversation_id = uuid4(), uuid4(), uuid4()
    manager = WebSocketConnectionManager()
    recipient_socket = _Socket()
    await manager.register(_connection(recipient_socket, recipient))
    messages = _HandlerMessages()
    handlers = WebSocketHandlers(
        _HandlerFactory({sender, recipient}),  # type: ignore[arg-type]
        messages,  # type: ignore[arg-type]
        EventPublisher(manager),
    )
    sender_connection = _connection(_Socket(), sender)
    envelope = _event()
    await handlers.heartbeat(
        sender_connection, HeartbeatEventData(sent_at=NOW), envelope
    )
    await handlers.typing(
        sender_connection,
        TypingEventData(conversation_id=conversation_id, is_typing=True),
        envelope,
    )
    typing_payload = json.loads(recipient_socket.text[-1])["data"]
    assert UUID(typing_payload["user_id"]) == sender
    await handlers.presence(
        sender_connection,
        PresenceEventData(
            state=PresenceState.ONLINE,
            changed_at=NOW,
            status_message="Available",
        ),
        envelope,
    )
    status = MessageStatusEventData(
        message_id=uuid4(),
        conversation_id=conversation_id,
        occurred_at=NOW,
    )
    await handlers.delivered(sender_connection, status, envelope)
    await handlers.read(sender_connection, status, envelope)
    assert messages.delivered == messages.read == 1


class _EndpointAuthentication:
    async def validate_current_user(self, token: str) -> AuthenticatedUser:
        if token != "access-token":
            raise ValueError("invalid")
        return AuthenticatedUser(uuid4(), uuid4(), "user", uuid4(), frozenset())


class _EndpointSessions:
    async def get_by_id(self, session_id: UUID) -> None:
        del session_id
        return None


class _EndpointUow:
    sessions = _EndpointSessions()

    async def __aenter__(self) -> _EndpointUow:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class _EndpointContainer:
    def __init__(self) -> None:
        self.settings = ServerSettings()
        self.services = SimpleNamespace(authentication=_EndpointAuthentication())
        self.websocket_manager = WebSocketConnectionManager()

        async def heartbeat(
            connection: WebSocketConnection,
            data: ContractModel,
            envelope: WebSocketEventEnvelope,
        ) -> None:
            del data, envelope
            connection.mark_heartbeat(datetime.now(UTC))

        self.websocket_dispatcher = WebSocketEventDispatcher(
            {WebSocketEventType.HEARTBEAT: heartbeat},
            WebSocketRateLimiter(10),
            {1},
        )
        self._logger = logging.getLogger("endpoint-test")

    def unit_of_work_factory(self) -> _EndpointUow:
        return _EndpointUow()

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        await self.websocket_manager.stop()


def test_websocket_endpoint_authenticates_and_dispatches() -> None:
    container = _EndpointContainer()
    app = create_application(container.settings, container=container)  # type: ignore[arg-type]
    with TestClient(app) as client:
        with client.websocket_connect("/api/v1/ws") as socket:
            authentication = WebSocketEventEnvelope(
                event_id=uuid4(),
                event_type=WebSocketEventType.AUTHENTICATE,
                protocol_version=1,
                timestamp=NOW,
                data={"access_token": "access-token"},
            )
            socket.send_text(authentication.model_dump_json())
            assert socket.receive_json()["event_type"] == "AUTHENTICATED"
            socket.send_text(_event().model_dump_json())
            assert socket.receive_json()["accepted"] is True
        with client.websocket_connect("/api/v1/ws") as rejected:
            rejected.send_text(_event().model_dump_json())
            with pytest.raises(WebSocketDisconnect) as error:
                rejected.receive_json()
            assert error.value.code == 1008
