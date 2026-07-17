"""Login-time directory identity synchronisation and role mapping."""

from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from bluebubbles.server.authentication.providers import DirectoryUser
from bluebubbles.server.configuration.settings import AuthenticationSettings
from bluebubbles.server.database.seed import stable_seed_id
from bluebubbles.server.database.unit_of_work import UnitOfWork
from bluebubbles.server.domain.users import User, normalise_username

_ROLE_PRIORITY = {
    "Employee": 10,
    "Helpdesk": 20,
    "HR": 30,
    "Manager": 35,
    "Administrator": 40,
    "SuperAdministrator": 50,
}


class DirectorySynchronisationService:
    """Synchronise trusted identity fields and one effective mapped role."""

    def __init__(self, settings: AuthenticationSettings) -> None:
        self._settings = settings

    async def synchronise_user(
        self,
        unit_of_work: UnitOfWork,
        identity: DirectoryUser,
        at: datetime,
    ) -> tuple[User, str]:
        """Create or update one user inside the caller's login transaction."""
        role_name = self.map_groups_to_role(identity.groups)
        role_id = stable_seed_id("role", role_name)
        directory_guid = self._directory_uuid(identity.directory_guid)
        user = None
        if directory_guid is not None:
            user = await unit_of_work.users.get_by_directory_guid(directory_guid)
        if user is None:
            user = await unit_of_work.users.get_by_normalised_username(
                identity.username
            )
        if user is None:
            user = User(
                id=uuid4(),
                created_at=at,
                updated_at=at,
                username=identity.username,
                display_name=identity.display_name,
                role_id=role_id,
                email=identity.email,
                department=identity.department,
                job_title=identity.job_title,
                active_directory_guid=directory_guid,
                is_enabled=identity.is_enabled,
                last_login=at,
            )
            await unit_of_work.users.create(user)
            return user, role_name
        if identity.directory_guid is None and identity.distinguished_name is None:
            role_id = user.role_id
            stored_role_name = await unit_of_work.authentication.role_name(role_id)
            role_name = stored_role_name or self._settings.default_role
        expected_version = user.version
        user.username = normalise_username(identity.username)
        user.display_name = identity.display_name.strip()
        user.email = identity.email
        user.department = identity.department
        user.job_title = identity.job_title
        user.active_directory_guid = directory_guid or user.active_directory_guid
        user.role_id = role_id
        user.is_enabled = identity.is_enabled
        user.last_login = at
        user.touch(at)
        await unit_of_work.users.update(user, expected_version=expected_version)
        return user, role_name

    def map_groups_to_role(self, groups: tuple[str, ...]) -> str:
        """Choose the highest explicitly mapped role, defaulting to Employee."""
        mappings = {
            group.casefold(): role
            for group, role in self._settings.directory_group_role_mapping.items()
        }
        selected = [
            mappings[group.casefold()]
            for group in groups
            if group.casefold() in mappings
        ]
        if not selected:
            return self._settings.default_role
        return max(selected, key=lambda role: _ROLE_PRIORITY.get(role, -1))

    @staticmethod
    def _directory_uuid(value: str | None) -> UUID | None:
        if value is None:
            return None
        try:
            return UUID(value)
        except ValueError:
            return uuid5(NAMESPACE_URL, f"bluebubbles-directory:{value}")
