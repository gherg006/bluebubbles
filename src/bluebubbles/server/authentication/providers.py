"""Identity-provider contracts and provider-neutral directory values."""

from dataclasses import dataclass
from typing import Protocol

from pydantic import SecretStr

from bluebubbles.shared.models.health import ComponentHealth


@dataclass(frozen=True, slots=True)
class LoginCredentials:
    """Carry one canonical username and a representation-safe password."""

    username: str
    password: SecretStr


@dataclass(frozen=True, slots=True)
class DirectoryUser:
    """Represent normalised trusted identity data from any provider."""

    username: str
    display_name: str
    email: str | None = None
    department: str | None = None
    job_title: str | None = None
    directory_guid: str | None = None
    distinguished_name: str | None = None
    groups: tuple[str, ...] = ()
    is_enabled: bool = True


AuthenticatedDirectoryIdentity = DirectoryUser


class AuthenticationProvider(Protocol):
    """Authenticate credentials against exactly one configured identity source."""

    async def authenticate(
        self, credentials: LoginCredentials
    ) -> AuthenticatedDirectoryIdentity:
        """Verify credentials and return trusted password-free identity data."""
        ...

    async def get_user_by_identifier(self, identifier: str) -> DirectoryUser | None:
        """Retrieve trusted identity data without authenticating a password."""
        ...

    async def check_health(self) -> ComponentHealth:
        """Return a safe, bounded provider availability result."""
        ...
