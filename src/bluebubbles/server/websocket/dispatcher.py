"""Validated, rate-limited WebSocket event dispatch."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from pydantic import ValidationError as PydanticValidationError

from bluebubbles.server.websocket.connection import WebSocketConnection
from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.errors.codes import ErrorCode
from bluebubbles.shared.errors.exceptions import BlueBubblesError, RateLimitError
from bluebubbles.shared.errors.mappings import get_error_metadata
from bluebubbles.shared.errors.models import WebSocketErrorEventData
from bluebubbles.shared.protocol.envelope import (
    WebSocketAcknowledgement,
    WebSocketEventEnvelope,
)
from bluebubbles.shared.protocol.event_types import WebSocketEventType
from bluebubbles.shared.protocol.events import validate_event_data

WebSocketEventHandler = Callable[
    [WebSocketConnection, ContractModel, WebSocketEventEnvelope], Awaitable[None]
]


class WebSocketRateLimiter:
    """Bound each connection's event rate with an in-memory sliding window."""

    def __init__(
        self, maximum_events: int, window: timedelta = timedelta(minutes=1)
    ) -> None:
        if maximum_events < 1:
            raise ValueError("WebSocket rate limit must be positive")
        self._maximum_events = maximum_events
        self._window = window
        self._events: dict[UUID, deque[datetime]] = defaultdict(deque)

    def require_allowed(self, connection_id: UUID, now: datetime) -> None:
        events = self._events[connection_id]
        boundary = now - self._window
        while events and events[0] <= boundary:
            events.popleft()
        if len(events) >= self._maximum_events:
            raise RateLimitError(retry_after_seconds=1)
        events.append(now)

    def discard(self, connection_id: UUID) -> None:
        self._events.pop(connection_id, None)


class WebSocketEventDispatcher:
    """Parse, validate, rate-limit, and invoke registered event handlers."""

    def __init__(
        self,
        handlers: Mapping[WebSocketEventType, WebSocketEventHandler],
        rate_limiter: WebSocketRateLimiter,
        supported_protocol_versions: set[int],
    ) -> None:
        self._handlers = dict(handlers)
        self._rate_limiter = rate_limiter
        self._supported_protocol_versions = supported_protocol_versions

    async def dispatch(
        self, connection: WebSocketConnection, raw_message: str | bytes
    ) -> WebSocketAcknowledgement | None:
        request_id: UUID | None = None
        try:
            if isinstance(raw_message, bytes):
                raw_message = raw_message.decode("utf-8")
            envelope = WebSocketEventEnvelope.model_validate_json(raw_message)
            request_id = envelope.event_id
            if envelope.protocol_version not in self._supported_protocol_versions:
                from bluebubbles.shared.errors.exceptions import ProtocolError

                raise ProtocolError()
            self._rate_limiter.require_allowed(
                connection.connection_id, datetime.now(UTC)
            )
            data = validate_event_data(envelope.event_type.value, envelope.data)
            handler = self._handlers.get(envelope.event_type)
            if handler is None:
                raise ValueError("Event type is not accepted from clients")
            await handler(connection, data, envelope)
            return WebSocketAcknowledgement(
                event_id=envelope.event_id,
                accepted=True,
                correlation_id=envelope.correlation_id,
            )
        except (
            BlueBubblesError,
            PydanticValidationError,
            UnicodeError,
            ValueError,
        ) as error:
            if isinstance(error, BlueBubblesError):
                code = error.code
                message = error.user_message
                retryable = error.retryable
            else:
                code = ErrorCode.INVALID_REQUEST
                metadata = get_error_metadata(code)
                message = metadata.default_message
                retryable = False
            error_event = WebSocketEventEnvelope(
                event_id=uuid4(),
                event_type=WebSocketEventType.ERROR,
                protocol_version=min(self._supported_protocol_versions),
                timestamp=datetime.now(UTC),
                correlation_id=request_id,
                data=WebSocketErrorEventData(
                    code=code,
                    message=message,
                    retryable=retryable,
                    request_event_id=request_id,
                ).model_dump(mode="json"),
            )
            await connection.send(error_event)
            return WebSocketAcknowledgement(
                event_id=request_id or uuid4(),
                accepted=False,
                correlation_id=request_id,
                error_code=code.value,
            )
