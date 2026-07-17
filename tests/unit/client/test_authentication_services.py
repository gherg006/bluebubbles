"""Client session-secret ownership and login coordination tests."""

# mypy: disable-error-code="no-untyped-def,attr-defined"

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from pydantic import SecretStr

from bluebubbles.client.services.authentication import ClientAuthenticationService
from bluebubbles.client.services.sessions import ClientSessionService
from bluebubbles.shared.errors.exceptions import SessionExpiredError
from bluebubbles.shared.models.sessions import (
    LoginResponse,
    RefreshTokenResponse,
)
from bluebubbles.shared.models.users import PresenceState, UserProfileResponse

NOW = datetime.now(UTC)
PROFILE_ID = UUID("10000000-0000-0000-0000-000000000001")
SESSION_ID = UUID("20000000-0000-0000-0000-000000000002")
DEVICE_ID = UUID("30000000-0000-0000-0000-000000000003")


def _profile() -> UserProfileResponse:
    return UserProfileResponse(
        id=PROFILE_ID,
        username="employee1",
        display_name="Employee One",
        department=None,
        presence=PresenceState.OFFLINE,
        role="Employee",
        is_enabled=True,
    )


def _login(*, expired: bool = False) -> LoginResponse:
    expiry = NOW - timedelta(seconds=1) if expired else NOW + timedelta(minutes=10)
    return LoginResponse(
        access_token=SecretStr("access-one"),
        refresh_token=SecretStr("refresh-one"),
        expires_in=900,
        access_token_expires_at=expiry,
        refresh_token_expires_at=NOW + timedelta(days=7),
        session_id=SESSION_ID,
        user=_profile(),
    )


class _Store:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}
        self.deleted: list[UUID] = []

    async def set_secret(self, key: str, value: bytes) -> None:
        self.values[key] = value

    async def get_secret(self, key: str) -> bytes | None:
        return self.values.get(key)

    async def delete_secret(self, key: str) -> None:
        self.values.pop(key, None)

    async def delete_profile(self, profile_id: UUID) -> None:
        self.deleted.append(profile_id)
        self.values.clear()


class _Api:
    def __init__(self) -> None:
        self.login_request = None
        self.logged_out: str | None = None

    async def login(self, request):
        self.login_request = request
        return _login(expired=True)

    async def refresh(self, request):
        assert request.session_id == SESSION_ID
        assert request.refresh_token.get_secret_value() == "refresh-one"
        return RefreshTokenResponse(
            access_token=SecretStr("access-two"),
            refresh_token=SecretStr("refresh-two"),
            expires_in=900,
            access_token_expires_at=NOW + timedelta(minutes=15),
            refresh_token_expires_at=NOW + timedelta(days=7),
            session_id=SESSION_ID,
        )

    async def logout(self, access_token: str) -> None:
        self.logged_out = access_token


@pytest.mark.asyncio
async def test_client_login_refresh_logout_and_revocation_cleanup() -> None:
    store = _Store()
    api = _Api()
    sessions = ClientSessionService(api, store)
    authentication = ClientAuthenticationService(
        api, sessions, device_id=DEVICE_ID, client_version="0.1.0"
    )
    response = await authentication.login(
        username="employee1",
        password=SecretStr("never-persist-this"),
        device_name="Office PC",
    )
    assert response.user.id == PROFILE_ID
    assert api.login_request.password.get_secret_value() == "never-persist-this"
    assert b"never-persist-this" not in store.values.values()
    assert await sessions.get_access_token() == "access-two"
    assert b"refresh-two" in store.values.values()
    await sessions.logout()
    assert api.logged_out == "access-two" and store.deleted == [PROFILE_ID]
    with pytest.raises(SessionExpiredError):
        await sessions.refresh()
    await sessions.accept_login(_login())
    assert await sessions.get_access_token() == "access-one"
    await sessions.handle_revocation()
    assert store.deleted[-1] == PROFILE_ID
