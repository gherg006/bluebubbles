"""Thin authenticated group membership and role HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from bluebubbles.server.container import ServerContainer
from bluebubbles.server.dependencies import get_server_container
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.routes.authentication import current_authenticated_user
from bluebubbles.server.services.groups import GroupService
from bluebubbles.shared.models.conversations import (
    AddGroupMemberRequest,
    ChangeGroupRoleRequest,
    TransferOwnershipRequest,
    UpdateGroupRequest,
)

router = APIRouter(prefix="/api/v1/groups", tags=["groups"])


def _service(container: ServerContainer) -> GroupService:
    service = container.services.groups
    if service is None:
        raise RuntimeError("Group service is not configured")
    return service


@router.patch("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_group(
    group_id: UUID,
    update: UpdateGroupRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> Response:
    await _service(container).update_group(current, group_id, update)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{group_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def add_member(
    group_id: UUID,
    request: AddGroupMemberRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> Response:
    await _service(container).add_member(current, group_id, request.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: UUID,
    user_id: UUID,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> Response:
    await _service(container).remove_member(current, group_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{group_id}/roles", status_code=status.HTTP_204_NO_CONTENT)
async def change_role(
    group_id: UUID,
    request: ChangeGroupRoleRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> Response:
    await _service(container).change_member_role(
        current, group_id, request.user_id, request.role
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{group_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_group(
    group_id: UUID,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> Response:
    await _service(container).leave_group(current, group_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{group_id}/owner", status_code=status.HTTP_204_NO_CONTENT)
async def transfer_ownership(
    group_id: UUID,
    request: TransferOwnershipRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> Response:
    await _service(container).transfer_ownership(
        current, group_id, request.new_owner_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
