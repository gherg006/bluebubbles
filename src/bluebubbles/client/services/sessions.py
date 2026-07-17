"""Client in-memory access-token state and protected refresh handling."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from pydantic import SecretStr

from bluebubbles.client.security.secure_store import SecureStore
from bluebubbles.shared.errors.exceptions import SessionExpiredError
from bluebubbles.shared.models.sessions import (
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)


class SessionApi(Protocol):
    """Define only remote operations required by client session management."""

    async def refresh(self, request: RefreshTokenRequest) -> RefreshTokenResponse: ...

    async def logout(self, access_token: str) -> None: ...


class ClientSessionService:
    """Keep access tokens in memory and refresh tokens in protected storage."""

    def __init__(self, api_client: SessionApi, secure_store: SecureStore) -> None:
        self._api = api_client
        self._secure_store = secure_store
        self._profile_id: UUID | None = None
        self._access_token: str | None = None
        self._access_expires_at: datetime | None = None
        self._session_id: UUID | None = None

    async def accept_login(self, response: LoginResponse) -> None:
        """Store refresh state securely and retain access state only in memory."""
        profile_id = response.user.id
        await self._secure_store.set_secret(
            self._key(profile_id, "refresh_token"),
            response.refresh_token.get_secret_value().encode("utf-8"),
        )
        await self._secure_store.set_secret(
            self._key(profile_id, "session_id"),
            str(response.session_id).encode("ascii"),
        )
        self._profile_id = profile_id
        self._access_token = response.access_token.get_secret_value()
        self._access_expires_at = response.access_token_expires_at
        self._session_id = response.session_id

    async def get_access_token(self) -> str:
        """Return a currently valid access token, refreshing before expiry."""
        if (
            self._access_token is not None
            and self._access_expires_at is not None
            and self._access_expires_at > datetime.now(UTC)
        ):
            return self._access_token
        return await self.refresh()

    async def refresh(self) -> str:
        """Rotate the protected refresh token and replace in-memory access state."""
        if self._profile_id is None or self._session_id is None:
            raise SessionExpiredError()
        raw = await self._secure_store.get_secret(
            self._key(self._profile_id, "refresh_token")
        )
        if raw is None:
            raise SessionExpiredError()
        response = await self._api.refresh(
            RefreshTokenRequest(
                refresh_token=SecretStr(raw.decode("utf-8")),
                session_id=self._session_id,
            )
        )
        await self._secure_store.set_secret(
            self._key(self._profile_id, "refresh_token"),
            response.refresh_token.get_secret_value().encode("utf-8"),
        )
        self._access_token = response.access_token.get_secret_value()
        self._access_expires_at = response.access_token_expires_at
        self._session_id = response.session_id
        return self._access_token

    async def logout(self) -> None:
        """Request server revocation, then always clear every local session secret."""
        profile_id = self._profile_id
        access_token = self._access_token
        try:
            if access_token is not None:
                await self._api.logout(access_token)
        finally:
            self._clear_memory()
            if profile_id is not None:
                await self._secure_store.delete_profile(profile_id)

    async def handle_revocation(self) -> None:
        """Clear local state immediately after a server session-revoked event."""
        profile_id = self._profile_id
        self._clear_memory()
        if profile_id is not None:
            await self._secure_store.delete_profile(profile_id)

    @staticmethod
    def _key(profile_id: UUID, name: str) -> str:
        return f"profile:{profile_id}:{name}"

    def _clear_memory(self) -> None:
        self._profile_id = None
        self._access_token = None
        self._access_expires_at = None
        self._session_id = None
