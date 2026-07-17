"""Thin authenticated user-profile HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from bluebubbles.server.container import ServerContainer
from bluebubbles.server.dependencies import get_server_container
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.routes.authentication import current_authenticated_user
from bluebubbles.server.services.keys import PublicKeyService
from bluebubbles.server.services.users import UserService
from bluebubbles.shared.models.pagination import OpaqueCursor
from bluebubbles.shared.models.users import (
    PublicUserKeyResponse,
    UpdateUserProfileRequest,
    UserProfileResponse,
    UserSearchRequest,
    UserSearchResponse,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _service(container: ServerContainer) -> UserService:
    service = container.services.users
    if service is None:
        raise RuntimeError("User service is not configured")
    return service


def _key_service(container: ServerContainer) -> PublicKeyService:
    service = container.services.public_keys
    if service is None:
        raise RuntimeError("Public-key service is not configured")
    return service


@router.get("/search", response_model=UserSearchResponse)
async def search_users(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
    query: str,
    department: str | None = None,
    limit: int = 50,
    after: str | None = None,
) -> UserSearchResponse:
    """Search visible enabled users through a bounded server query."""
    del current
    return await _service(container).search_users(
        UserSearchRequest(
            query=query,
            department=department,
            limit=limit,
            after=OpaqueCursor(after) if after else None,
        )
    )


@router.patch("/profile", response_model=UserProfileResponse)
async def update_profile(
    profile: UpdateUserProfileRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> UserProfileResponse:
    """Update only the authenticated user's editable profile."""
    return await _service(container).update_profile(current, profile)


@router.get("/{user_id}/keys", response_model=PublicUserKeyResponse)
async def get_user_keys(
    user_id: UUID,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> PublicUserKeyResponse:
    """Return retained public keys for a visible user."""
    del current
    return await _key_service(container).list_for_user(user_id)


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user(
    user_id: UUID,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> UserProfileResponse:
    """Return a client-safe profile after authentication."""
    del current
    return await _service(container).get_user(user_id)
