"""One-time, transaction-safe initial administrator creation."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import SecretStr

from bluebubbles.server.authentication.directory_sync import (
    DirectorySynchronisationService,
)
from bluebubbles.server.authentication.password_hashing import PasswordHasher
from bluebubbles.server.authentication.providers import DirectoryUser
from bluebubbles.server.configuration.settings import AuthenticationSettings
from bluebubbles.server.database.seed import stable_seed_id
from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.audit import AuditSeverity
from bluebubbles.server.domain.users import LocalCredential, User
from bluebubbles.server.services.audit import AuditWriter
from bluebubbles.shared.errors.exceptions import ConflictError


class InitialAdministratorService:
    """Create exactly one initial administrator without a default credential."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        audit_writer: AuditWriter | None = None,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        self._uow_factory = unit_of_work_factory
        self._audit = audit_writer or AuditWriter()
        self._passwords = password_hasher or PasswordHasher()

    async def create_local(
        self, *, username: str, display_name: str, password: SecretStr
    ) -> UUID:
        """Create a local administrator and verifier in one audited transaction."""
        if len(password.get_secret_value()) < 12:
            raise ValueError(
                "The initial administrator password must be 12 characters."
            )
        administrator_role = stable_seed_id("role", "Administrator")
        now = datetime.now(UTC)
        user_id = uuid4()
        async with self._uow_factory() as unit_of_work:
            existing = await unit_of_work.users.get_by_normalised_username(username)
            if existing is not None:
                raise ConflictError(user_message="That username already exists.")
            if await unit_of_work.authentication.count_enabled_users_with_role(
                administrator_role
            ):
                raise ConflictError(
                    user_message="An enabled initial administrator already exists."
                )
            user = User(
                id=user_id,
                created_at=now,
                updated_at=now,
                username=username,
                display_name=display_name,
                role_id=administrator_role,
            )
            credential = LocalCredential(
                id=user_id,
                created_at=now,
                updated_at=now,
                user_id=user_id,
                password_hash=self._passwords.hash_password(password),
            )
            await unit_of_work.users.create(user)
            await unit_of_work.authentication.create_local_credential(credential)
            await self._audit.append(
                unit_of_work.audit,
                event_type="administrator.initial_created",
                occurred_at=now,
                actor_id=user_id,
                source_ip=None,
                severity=AuditSeverity.WARNING,
                details={"user_id": str(user_id), "authentication_source": "local"},
            )
            await unit_of_work.commit()
        return user_id

    async def create_directory(
        self, identity: DirectoryUser, settings: AuthenticationSettings
    ) -> UUID:
        """Provision a credential-validated directory identity as initial admin."""
        if not identity.is_enabled:
            raise ConflictError(user_message="The directory account is disabled.")
        administrator_role = stable_seed_id("role", "Administrator")
        now = datetime.now(UTC)
        async with self._uow_factory() as unit_of_work:
            if await unit_of_work.authentication.count_enabled_users_with_role(
                administrator_role
            ):
                raise ConflictError(
                    user_message="An enabled initial administrator already exists."
                )
            user, _ = await DirectorySynchronisationService(settings).synchronise_user(
                unit_of_work, identity, now
            )
            if user.role_id != administrator_role:
                expected_version = user.version
                user.role_id = administrator_role
                user.touch(now)
                await unit_of_work.users.update(user, expected_version=expected_version)
            await self._audit.append(
                unit_of_work.audit,
                event_type="administrator.initial_created",
                occurred_at=now,
                actor_id=user.id,
                source_ip=None,
                severity=AuditSeverity.WARNING,
                details={
                    "user_id": str(user.id),
                    "authentication_source": "directory",
                },
            )
            await unit_of_work.commit()
        return user.id
