"""Authenticated public-key registration and retrieval routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from bluebubbles.server.container import ServerContainer
from bluebubbles.server.dependencies import get_server_container
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.routes.authentication import current_authenticated_user
from bluebubbles.server.services.keys import PublicKeyService
from bluebubbles.shared.security.key_models import (
    PublicKeyDescriptor,
    RegisterPublicKeyRequest,
    RevokePublicKeyRequest,
)

router = APIRouter(prefix="/api/v1/keys", tags=["public-keys"])


def _service(container: ServerContainer) -> PublicKeyService:
    service = container.services.public_keys
    if service is None:
        raise RuntimeError("Public-key service is not configured")
    return service


@router.post(
    "", response_model=PublicKeyDescriptor, status_code=status.HTTP_201_CREATED
)
async def register_key(
    registration: RegisterPublicKeyRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> PublicKeyDescriptor:
    """Register one client-generated public-only identity key."""
    return await _service(container).register(current, registration)


@router.post("/{key_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(
    key_id: UUID,
    revocation: RevokePublicKeyRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> Response:
    """Revoke one public-key revision owned by the authenticated user."""
    await _service(container).revoke(current, key_id, revocation)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
