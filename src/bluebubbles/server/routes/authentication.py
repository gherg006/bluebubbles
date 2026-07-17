"""Authentication and user-owned session HTTP routes."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import SecretStr

from bluebubbles.server.container import ServerContainer
from bluebubbles.server.dependencies import get_server_container
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import User
from bluebubbles.server.services.authentication import LoginContext
from bluebubbles.shared.errors.exceptions import InvalidTokenError
from bluebubbles.shared.models.sessions import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    SessionListResponse,
)
from bluebubbles.shared.models.users import UserProfileResponse

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
_bearer = HTTPBearer(auto_error=False)


def _profile(user: User, role_name: str) -> UserProfileResponse:
    return UserProfileResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        department=user.department,
        presence=user.presence,
        avatar_url=user.profile_picture_reference,
        email=user.email,
        job_title=user.job_title,
        status_message=user.status_message,
        role=role_name,
        is_enabled=user.is_enabled,
        last_login=user.last_login,
    )


async def current_authenticated_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> AuthenticatedUser:
    """Validate bearer signature plus session and account state for every request."""
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise InvalidTokenError()
    service = container.services.authentication
    if service is None:
        raise RuntimeError("Authentication service is not configured")
    return await service.validate_current_user(credentials.credentials)


@router.post("/login", response_model=LoginResponse)
async def login(
    login_request: LoginRequest,
    request: Request,
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> LoginResponse:
    """Authenticate credentials and return one committed server-side session."""
    service = container.services.authentication
    if service is None:
        raise RuntimeError("Authentication service is not configured")
    result = await service.login(
        login_request,
        LoginContext(
            source_ip=request.client.host if request.client is not None else None,
            correlation_id=uuid4(),
        ),
    )
    return LoginResponse(
        access_token=SecretStr(result.tokens.access_token),
        refresh_token=SecretStr(result.tokens.refresh_token),
        expires_in=container.settings.tokens.access_token_lifetime_seconds,
        access_token_expires_at=result.tokens.access_expires_at,
        refresh_token_expires_at=result.tokens.refresh_expires_at,
        session_id=result.tokens.session.id,
        user=_profile(result.user, result.role_name),
        permissions=result.permissions,
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh(
    refresh_request: RefreshTokenRequest,
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> RefreshTokenResponse:
    """Rotate a bound refresh token exactly once and return replacement tokens."""
    service = container.services.sessions
    if service is None:
        raise RuntimeError("Session service is not configured")
    result = await service.refresh(refresh_request)
    return RefreshTokenResponse(
        access_token=SecretStr(result.access_token),
        refresh_token=SecretStr(result.refresh_token),
        expires_in=container.settings.tokens.access_token_lifetime_seconds,
        access_token_expires_at=result.access_expires_at,
        refresh_token_expires_at=result.refresh_expires_at,
        session_id=result.session.id,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> Response:
    """Invalidate the current server session before the client clears secrets."""
    service = container.services.sessions
    if service is None:
        raise RuntimeError("Session service is not configured")
    await service.invalidate(current, current.session_id, "user_logout")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> Response:
    """Invalidate every active session owned by the authenticated user."""
    service = container.services.sessions
    if service is None:
        raise RuntimeError("Session service is not configured")
    await service.invalidate_all_for_user(current.user_id, "user_logout_all")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserProfileResponse)
async def current_profile(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> UserProfileResponse:
    """Return the current enabled profile after authoritative session validation."""
    service = container.services.authentication
    if service is None:
        raise RuntimeError("Authentication service is not configured")
    user, role_name = await service.get_profile(current)
    return _profile(user, role_name)


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> SessionListResponse:
    """Return only token-free session metadata owned by the current user."""
    service = container.services.sessions
    if service is None:
        raise RuntimeError("Session service is not configured")
    return SessionListResponse(sessions=await service.list_for_user(current))


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: str,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> Response:
    """Revoke one user-owned session without exposing token identifiers."""
    from uuid import UUID

    service = container.services.sessions
    if service is None:
        raise RuntimeError("Session service is not configured")
    try:
        selected = UUID(session_id)
    except ValueError as error:
        raise InvalidTokenError() from error
    await service.invalidate(current, selected, "user_device_revocation")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
