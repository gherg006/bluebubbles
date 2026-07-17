"""Explicitly enabled local-account authentication provider."""

from collections.abc import Callable
from datetime import UTC, datetime

from bluebubbles.server.authentication.password_hashing import PasswordHasher
from bluebubbles.server.authentication.providers import (
    AuthenticatedDirectoryIdentity,
    DirectoryUser,
    LoginCredentials,
)
from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.shared.errors.exceptions import (
    AccountDisabledError,
    AccountLockedError,
    InvalidCredentialsError,
)
from bluebubbles.shared.models.health import ComponentHealth, HealthState


class LocalAuthenticationProvider:
    """Verify Argon2id local credentials only when configuration enables them."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        password_hasher: PasswordHasher,
        *,
        enabled: bool,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._password_hasher = password_hasher
        self._enabled = enabled
        self._clock = clock or (lambda: datetime.now(UTC))

    async def authenticate(
        self, credentials: LoginCredentials
    ) -> AuthenticatedDirectoryIdentity:
        """Verify one local account and opportunistically upgrade its verifier."""
        if not self._enabled:
            raise InvalidCredentialsError()
        async with self._unit_of_work_factory() as unit_of_work:
            record = await unit_of_work.authentication.get_local_identity(
                credentials.username
            )
            if record is None:
                raise InvalidCredentialsError()
            user, credential = record
            now = self._clock()
            if credential.locked_until is not None and credential.locked_until > now:
                raise AccountLockedError(
                    retry_after_seconds=max(
                        0, int((credential.locked_until - now).total_seconds())
                    )
                )
            if not user.is_enabled:
                raise AccountDisabledError()
            if not self._password_hasher.verify_password(
                credentials.password, credential.password_hash
            ):
                raise InvalidCredentialsError()
            if self._password_hasher.requires_rehash(credential.password_hash):
                credential.password_hash = self._password_hasher.rehash_password(
                    credentials.password
                )
                credential.touch(now)
                await unit_of_work.authentication.update_local_credential(credential)
                await unit_of_work.commit()
            return DirectoryUser(
                username=user.username,
                display_name=user.display_name,
                email=user.email,
                department=user.department,
                job_title=user.job_title,
                directory_guid=(
                    str(user.active_directory_guid)
                    if user.active_directory_guid is not None
                    else None
                ),
                is_enabled=user.is_enabled,
            )

    async def get_user_by_identifier(self, identifier: str) -> DirectoryUser | None:
        """Return local identity metadata without returning its verifier."""
        if not self._enabled:
            return None
        async with self._unit_of_work_factory() as unit_of_work:
            record = await unit_of_work.authentication.get_local_identity(identifier)
            if record is None:
                return None
            user, _credential = record
            return DirectoryUser(
                username=user.username,
                display_name=user.display_name,
                email=user.email,
                department=user.department,
                job_title=user.job_title,
                is_enabled=user.is_enabled,
            )

    async def check_health(self) -> ComponentHealth:
        """Report whether local authentication is intentionally enabled."""
        return ComponentHealth(
            name="local_authentication",
            state=HealthState.HEALTHY if self._enabled else HealthState.DEGRADED,
        )
