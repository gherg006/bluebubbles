"""Client login coordination without plaintext-password persistence."""

from typing import Protocol
from uuid import UUID

from pydantic import SecretStr

from bluebubbles.client.services.sessions import ClientSessionService
from bluebubbles.shared.models.sessions import LoginRequest, LoginResponse


class LoginApi(Protocol):
    """Define the remote login operation used by the client service."""

    async def login(self, request: LoginRequest) -> LoginResponse: ...


class ClientAuthenticationService:
    """Submit credentials once and hand session secrets to the session owner."""

    def __init__(
        self,
        api_client: LoginApi,
        session_service: ClientSessionService,
        *,
        device_id: UUID,
        client_version: str,
    ) -> None:
        self._api = api_client
        self._sessions = session_service
        self._device_id = device_id
        self._client_version = client_version

    async def login(
        self,
        *,
        username: str,
        password: SecretStr,
        device_name: str,
    ) -> LoginResponse:
        """Login without retaining the password or writing it to local storage."""
        request = LoginRequest(
            username=username,
            password=password,
            device_name=device_name,
            device_id=self._device_id,
            client_version=self._client_version,
        )
        response = await self._api.login(request)
        await self._sessions.accept_login(response)
        return response
