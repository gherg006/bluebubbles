"""Thin authenticated conversation HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from bluebubbles.server.container import ServerContainer
from bluebubbles.server.dependencies import get_server_container
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.repositories.types import ConversationListQuery
from bluebubbles.server.routes.authentication import current_authenticated_user
from bluebubbles.server.services.conversations import ConversationService
from bluebubbles.shared.models.conversations import (
    ArchiveConversationRequest,
    ConversationResponse,
    ConversationSummaryResponse,
    CreateDirectConversationRequest,
    CreateGroupConversationRequest,
)
from bluebubbles.shared.models.pagination import CursorPage

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


def _service(container: ServerContainer) -> ConversationService:
    service = container.services.conversations
    if service is None:
        raise RuntimeError("Conversation service is not configured")
    return service


@router.get("", response_model=CursorPage[ConversationSummaryResponse])
async def list_conversations(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
    limit: int = 50,
    after: str | None = None,
    include_archived: bool = False,
) -> CursorPage[ConversationSummaryResponse]:
    return await _service(container).list_for_user(
        current,
        ConversationListQuery(
            user_id=current.user_id,
            limit=limit,
            cursor=after,
            include_archived=include_archived,
        ),
    )


@router.post(
    "/direct", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED
)
async def create_direct(
    request: CreateDirectConversationRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> ConversationResponse:
    return await _service(container).create_direct(current, request)


@router.post(
    "/group", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED
)
async def create_group(
    request: CreateGroupConversationRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> ConversationResponse:
    return await _service(container).create_group(current, request)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> ConversationResponse:
    return await _service(container).get_conversation(current, conversation_id)


@router.post("/{conversation_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def archive_conversation(
    conversation_id: UUID,
    request: ArchiveConversationRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> Response:
    await _service(container).archive_for_user(
        current, conversation_id, request.archived
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
