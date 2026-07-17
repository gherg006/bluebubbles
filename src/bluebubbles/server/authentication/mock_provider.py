"""Predictable injectable authentication provider for automated tests."""

import asyncio
from collections.abc import Mapping

from bluebubbles.server.authentication.providers import (
    AuthenticatedDirectoryIdentity,
    DirectoryUser,
    LoginCredentials,
)
from bluebubbles.shared.errors.exceptions import (
    DirectoryUnavailableError,
    InvalidCredentialsError,
)
from bluebubbles.shared.models.health import ComponentHealth, HealthState


class MockAuthenticationProvider:
    """Authenticate configured synthetic identities without production shortcuts."""

    def __init__(
        self,
        users: Mapping[str, tuple[str, DirectoryUser]],
        *,
        unavailable: bool = False,
        response_delay_seconds: float = 0,
    ) -> None:
        self._users = {name.casefold(): value for name, value in users.items()}
        self._unavailable = unavailable
        self._delay = response_delay_seconds

    async def authenticate(
        self, credentials: LoginCredentials
    ) -> AuthenticatedDirectoryIdentity:
        """Return a known identity or the enumeration-safe credential error."""
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._unavailable:
            raise DirectoryUnavailableError()
        record = self._users.get(credentials.username.casefold())
        if record is None or record[0] != credentials.password.get_secret_value():
            raise InvalidCredentialsError()
        return record[1]

    async def get_user_by_identifier(self, identifier: str) -> DirectoryUser | None:
        """Return a configured identity without exposing its test password."""
        record = self._users.get(identifier.casefold())
        return record[1] if record else None

    async def check_health(self) -> ComponentHealth:
        """Return deterministic safe availability for lifecycle tests."""
        return ComponentHealth(
            name="authentication_directory",
            state=(HealthState.UNHEALTHY if self._unavailable else HealthState.HEALTHY),
        )
