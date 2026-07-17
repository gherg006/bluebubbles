"""Central server-side application and resource permission checks."""

from uuid import UUID

from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.conversations import ConversationMember
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission, User
from bluebubbles.shared.errors.exceptions import (
    AuthorisationError,
    ResourceNotFoundError,
)
from bluebubbles.shared.models.conversations import GroupRole

_GROUP_ROLE_RANK = {
    GroupRole.MEMBER: 10,
    GroupRole.ADMIN: 30,
    GroupRole.OWNER: 40,
}


class PermissionService:
    """Resolve every authority decision from repositories, never route role strings."""

    def __init__(self, unit_of_work_factory: UnitOfWorkFactory) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    async def require_permission(self, user: User, permission: Permission) -> None:
        """Raise when the user's current database role lacks a permission."""
        async with self._unit_of_work_factory() as unit_of_work:
            granted = await unit_of_work.authentication.permissions_for_role(
                user.role_id
            )
        if permission not in granted:
            raise AuthorisationError()

    async def require_authenticated_permission(
        self, user: AuthenticatedUser, permission: Permission
    ) -> None:
        """Re-read the current user and role before a protected operation."""
        async with self._unit_of_work_factory() as unit_of_work:
            current = await unit_of_work.users.get_by_id(user.user_id)
            if current is None or not current.is_enabled:
                raise AuthorisationError()
            granted = await unit_of_work.authentication.permissions_for_role(
                current.role_id
            )
        if permission not in granted:
            raise AuthorisationError()

    async def require_conversation_access(
        self, user_id: UUID, conversation_id: UUID
    ) -> ConversationMember:
        """Require a current active membership for one specific conversation."""
        async with self._unit_of_work_factory() as unit_of_work:
            member = await unit_of_work.conversations.get_active_membership(
                conversation_id, user_id
            )
        if member is None:
            raise ResourceNotFoundError()
        return member

    async def require_group_role(
        self, user_id: UUID, conversation_id: UUID, minimum_role: GroupRole
    ) -> ConversationMember:
        """Require both membership and the configured minimum group authority."""
        member = await self.require_conversation_access(user_id, conversation_id)
        if _GROUP_ROLE_RANK[member.role] < _GROUP_ROLE_RANK[minimum_role]:
            raise AuthorisationError()
        return member
