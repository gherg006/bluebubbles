"""Authenticated client WebSocket event handlers."""

from __future__ import annotations

from datetime import UTC, datetime

from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.services.messaging import MessagingService
from bluebubbles.server.websocket.connection import WebSocketConnection
from bluebubbles.server.websocket.dispatcher import WebSocketEventHandler
from bluebubbles.server.websocket.publisher import EventPublisher
from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.errors.exceptions import AuthorisationError
from bluebubbles.shared.models.messages import MarkConversationReadRequest
from bluebubbles.shared.protocol.envelope import WebSocketEventEnvelope
from bluebubbles.shared.protocol.event_types import WebSocketEventType
from bluebubbles.shared.protocol.events import (
    HeartbeatEventData,
    MessageStatusEventData,
    PresenceEventData,
    TypingEventData,
)


class WebSocketHandlers:
    """Coordinate transient and acknowledgement events with server services."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        messaging_service: MessagingService,
        event_publisher: EventPublisher,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._messaging_service = messaging_service
        self._event_publisher = event_publisher

    async def heartbeat(
        self,
        connection: WebSocketConnection,
        data: ContractModel,
        envelope: WebSocketEventEnvelope,
    ) -> None:
        del envelope
        heartbeat = HeartbeatEventData.model_validate(data)
        del heartbeat
        connection.mark_heartbeat(datetime.now(UTC))

    async def delivered(
        self,
        connection: WebSocketConnection,
        data: ContractModel,
        envelope: WebSocketEventEnvelope,
    ) -> None:
        del envelope
        status = MessageStatusEventData.model_validate(data)
        await self._messaging_service.acknowledge_delivery(
            connection.user_id,
            status.message_id,
            status.conversation_id,
            status.occurred_at,
        )

    async def read(
        self,
        connection: WebSocketConnection,
        data: ContractModel,
        envelope: WebSocketEventEnvelope,
    ) -> None:
        del envelope
        status = MessageStatusEventData.model_validate(data)
        await self._messaging_service.mark_read_by_user_id(
            connection.user_id,
            MarkConversationReadRequest(
                conversation_id=status.conversation_id,
                through_message_id=status.message_id,
            ),
        )

    async def typing(
        self,
        connection: WebSocketConnection,
        data: ContractModel,
        envelope: WebSocketEventEnvelope,
    ) -> None:
        typing = TypingEventData.model_validate(data)
        async with self._unit_of_work_factory() as uow:
            members = await uow.conversations.get_active_members(typing.conversation_id)
        member_ids = {member.user_id for member in members}
        if connection.user_id not in member_ids:
            raise AuthorisationError()
        await self._event_publisher.publish_transient(
            member_ids - {connection.user_id},
            WebSocketEventType.TYPING_CHANGED,
            envelope.event_id,
            TypingEventData(
                conversation_id=typing.conversation_id,
                user_id=connection.user_id,
                is_typing=typing.is_typing,
            ).model_dump(mode="json"),
        )

    async def presence(
        self,
        connection: WebSocketConnection,
        data: ContractModel,
        envelope: WebSocketEventEnvelope,
    ) -> None:
        presence = PresenceEventData.model_validate(data)
        await self._event_publisher.publish_transient(
            {connection.user_id},
            WebSocketEventType.PRESENCE_CHANGED,
            envelope.event_id,
            PresenceEventData(
                user_id=connection.user_id,
                state=presence.state,
                changed_at=datetime.now(UTC),
                status_message=presence.status_message,
            ).model_dump(mode="json"),
        )

    def mapping(self) -> dict[WebSocketEventType, WebSocketEventHandler]:
        return {
            WebSocketEventType.HEARTBEAT: self.heartbeat,
            WebSocketEventType.MESSAGE_DELIVERED: self.delivered,
            WebSocketEventType.MESSAGE_READ: self.read,
            WebSocketEventType.TYPING_CHANGED: self.typing,
            WebSocketEventType.PRESENCE_CHANGED: self.presence,
        }
