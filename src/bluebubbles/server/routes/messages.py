"""Thin authenticated routes for encrypted messages."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from bluebubbles.server.container import ServerContainer
from bluebubbles.server.dependencies import get_server_container
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.routes.authentication import current_authenticated_user
from bluebubbles.server.services.messaging import MessagingService
from bluebubbles.shared.models.messages import (
    DeletedMessageResponse,
    DeleteMessageRequest,
    EditMessageRequest,
    EncryptedMessageResponse,
    MarkConversationReadRequest,
    MessagePageResponse,
    SendMessageRequest,
    SendMessageResponse,
)

router = APIRouter(prefix="/api/v1", tags=["messages"])


def _service(container: ServerContainer) -> MessagingService:
    service = container.services.messaging
    if service is None:
        raise RuntimeError("Messaging service is not configured")
    return service


@router.post(
    "/messages", response_model=SendMessageResponse, status_code=status.HTTP_201_CREATED
)
async def send_message(
    request: SendMessageRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> SendMessageResponse:
    return await _service(container).send_message(current, request)


@router.get(
    "/conversations/{conversation_id}/messages", response_model=MessagePageResponse
)
async def list_messages(
    conversation_id: UUID,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
    limit: int = 50,
    before: str | None = None,
) -> MessagePageResponse:
    return await _service(container).list_messages(
        current, conversation_id, before, limit
    )


@router.patch("/messages/{message_id}", response_model=EncryptedMessageResponse)
async def edit_message(
    message_id: UUID,
    request: EditMessageRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> EncryptedMessageResponse:
    return await _service(container).edit_message(current, message_id, request)


@router.delete("/messages/{message_id}", response_model=DeletedMessageResponse)
async def delete_message(
    message_id: UUID,
    request: DeleteMessageRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> DeletedMessageResponse:
    return await _service(container).delete_message(
        current, message_id, request.expected_version
    )


@router.post(
    "/conversations/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT
)
async def mark_read(
    conversation_id: UUID,
    request: MarkConversationReadRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> None:
    if request.conversation_id != conversation_id:
        from bluebubbles.shared.errors.exceptions import ValidationError

        raise ValidationError(user_message="Conversation identifiers do not match.")
    await _service(container).mark_read(current, request)
