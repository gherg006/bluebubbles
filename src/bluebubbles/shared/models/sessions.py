"""Authentication request, token response, and session-management contracts."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field, SecretStr, field_serializer

from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.models.users import UserProfileResponse


class LoginRequest(ContractModel):
    """Submit directory credentials without exposing password representations."""

    username: Annotated[str, Field(min_length=1, max_length=128)]
    password: SecretStr
    device_name: Annotated[str, Field(min_length=1, max_length=200)]
    device_id: UUID | None = None
    client_version: Annotated[str, Field(min_length=1, max_length=50)] = "0.1.0"


class LoginResponse(ContractModel):
    """Return issued application tokens and the authenticated profile."""

    success: bool = True
    access_token: SecretStr
    refresh_token: SecretStr
    token_type: str = "bearer"  # noqa: S105 - OAuth scheme, not a credential
    expires_in: Annotated[int, Field(gt=0)]
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    session_id: UUID
    user: UserProfileResponse
    permissions: tuple[str, ...] = ()

    @field_serializer("access_token", "refresh_token", when_used="json")
    def serialise_tokens(self, value: SecretStr) -> str:
        """Reveal issued tokens only at the deliberate wire-serialisation boundary."""
        return value.get_secret_value()


class RefreshTokenRequest(ContractModel):
    """Exchange an application refresh token for a new token pair."""

    refresh_token: SecretStr
    session_id: UUID


class RefreshTokenResponse(ContractModel):
    """Return a rotated application token pair."""

    access_token: SecretStr
    refresh_token: SecretStr
    token_type: str = "bearer"  # noqa: S105 - OAuth scheme, not a credential
    expires_in: Annotated[int, Field(gt=0)]
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    session_id: UUID

    @field_serializer("access_token", "refresh_token", when_used="json")
    def serialise_tokens(self, value: SecretStr) -> str:
        """Reveal rotated tokens only at the deliberate wire boundary."""
        return value.get_secret_value()


class LogoutResponse(ContractModel):
    """Confirm that a session was invalidated."""

    revoked: bool = True


class SessionSummary(ContractModel):
    """Describe a session without returning any token."""

    id: UUID
    device_name: Annotated[str, Field(min_length=1, max_length=200)]
    platform: Annotated[str, Field(min_length=1, max_length=100)]
    source_ip: str | None = None
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    current: bool = False


class SessionListResponse(ContractModel):
    """Return all visible application sessions for the authenticated user."""

    sessions: tuple[SessionSummary, ...]


class RevokeSessionRequest(ContractModel):
    """Identify a session owned by the authenticated user for revocation."""

    session_id: UUID
