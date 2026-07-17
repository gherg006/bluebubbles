"""Thin authenticated contact relationship HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from bluebubbles.server.container import ServerContainer
from bluebubbles.server.dependencies import get_server_container
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.routes.authentication import current_authenticated_user
from bluebubbles.server.services.contacts import ContactService
from bluebubbles.shared.models.contacts import (
    AddContactRequest,
    BlockContactRequest,
    ContactListResponse,
    ContactSummary,
    UpdateContactRequest,
)

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])


def _service(container: ServerContainer) -> ContactService:
    service = container.services.contacts
    if service is None:
        raise RuntimeError("Contact service is not configured")
    return service


@router.get("", response_model=ContactListResponse)
async def list_contacts(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> ContactListResponse:
    return await _service(container).list_contacts(current)


@router.post("", response_model=ContactSummary, status_code=status.HTTP_201_CREATED)
async def add_contact(
    contact: AddContactRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> ContactSummary:
    return await _service(container).add_contact(current, contact)


@router.patch("/{contact_id}", response_model=ContactSummary)
async def update_contact(
    contact_id: UUID,
    update: UpdateContactRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> ContactSummary:
    return await _service(container).update_contact(current, contact_id, update)


@router.patch("/{contact_id}/favourite", response_model=ContactSummary)
async def favourite_contact(
    contact_id: UUID,
    update: UpdateContactRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> ContactSummary:
    return await _service(container).update_contact(current, contact_id, update)


@router.patch("/{contact_id}/block", response_model=ContactSummary)
async def block_contact(
    contact_id: UUID,
    update: BlockContactRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> ContactSummary:
    return await _service(container).set_blocked(current, contact_id, update.blocked)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_contact(
    contact_id: UUID,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> Response:
    await _service(container).remove_contact(current, contact_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
