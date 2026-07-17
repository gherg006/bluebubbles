"""FastAPI WebSocket boundary with timed first-frame authentication."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from bluebubbles.server.container import ServerContainer
from bluebubbles.server.dependencies import get_server_container
from bluebubbles.server.websocket.connection import WebSocketConnection
from bluebubbles.shared.protocol.envelope import WebSocketEventEnvelope
from bluebubbles.shared.protocol.event_types import WebSocketEventType
from bluebubbles.shared.protocol.events import (
    AuthenticatedEventData,
    AuthenticationEventData,
)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
@router.websocket("/api/v1/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> None:
    """Authenticate the first frame, then delegate every later event."""
    await websocket.accept()
    connection: WebSocketConnection | None = None
    try:
        raw = await asyncio.wait_for(
            websocket.receive_text(),
            timeout=container.settings.network.websocket_auth_timeout_seconds,
        )
        if len(raw) > container.settings.network.maximum_request_body_bytes:
            await websocket.close(code=1009, reason="Frame too large")
            return
        envelope = WebSocketEventEnvelope.model_validate_json(raw)
        if envelope.event_type is not WebSocketEventType.AUTHENTICATE:
            raise ValueError("First WebSocket event must authenticate")
        authentication = AuthenticationEventData.model_validate(envelope.data)
        service = container.services.authentication
        if service is None:
            raise RuntimeError("Authentication service is not configured")
        current = await service.validate_current_user(
            authentication.access_token.get_secret_value()
        )
        device_id = await _device_id(container, current.session_id)
        connection = WebSocketConnection(
            websocket,
            uuid4(),
            current.user_id,
            current.session_id,
            device_id,
            datetime.now(UTC),
        )
        await container.websocket_manager.register(connection)
        await connection.send(
            WebSocketEventEnvelope(
                event_id=uuid4(),
                event_type=WebSocketEventType.AUTHENTICATED,
                protocol_version=container.settings.protocol.current_version,
                timestamp=datetime.now(UTC),
                correlation_id=envelope.event_id,
                data=AuthenticatedEventData(
                    user_id=current.user_id, session_id=current.session_id
                ).model_dump(mode="json"),
            )
        )
        timeout = (
            container.settings.network.websocket_heartbeat_seconds
            * container.settings.network.websocket_missed_heartbeat_limit
        )
        while True:
            frame = await asyncio.wait_for(websocket.receive(), timeout=timeout)
            raw_message = frame.get("text") or frame.get("bytes")
            if raw_message is None:
                if frame.get("type") == "websocket.disconnect":
                    break
                continue
            if len(raw_message) > container.settings.network.maximum_request_body_bytes:
                await connection.close(1009, "Frame too large")
                break
            acknowledgement = await container.websocket_dispatcher.dispatch(
                connection, raw_message
            )
            if acknowledgement is not None:
                await connection.send_json(acknowledgement.model_dump(mode="json"))
    except (TimeoutError, ValueError, ValidationError):
        if connection is None:
            await websocket.close(code=1008, reason="Authentication required")
        else:
            await connection.close(1008, "Heartbeat timeout")
    except WebSocketDisconnect:
        pass
    finally:
        if connection is not None:
            await container.websocket_manager.unregister(connection.connection_id)


async def _device_id(container: ServerContainer, session_id: UUID) -> UUID:
    async with container.unit_of_work_factory() as uow:
        session = await uow.sessions.get_by_id(session_id)
    return (
        session.device_id if session is not None and session.device_id else session_id
    )
