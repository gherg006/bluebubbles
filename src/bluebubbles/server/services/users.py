"""Authenticated user profile and directory-search use cases."""

from datetime import UTC, datetime
from uuid import UUID

from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import User
from bluebubbles.server.repositories.types import UserSearchQuery
from bluebubbles.shared.errors.exceptions import ResourceNotFoundError
from bluebubbles.shared.models.pagination import CursorPageMetadata, OpaqueCursor
from bluebubbles.shared.models.users import (
    UpdateUserProfileRequest,
    UserProfileResponse,
    UserSearchRequest,
    UserSearchResponse,
    UserSummary,
)


def user_summary(user: User) -> UserSummary:
    """Convert an authoritative user to its safe list representation."""
    return UserSummary(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        department=user.department,
        presence=user.presence,
        avatar_url=user.profile_picture_reference,
    )


class UserService:
    """Retrieve and mutate only permitted user profile information."""

    def __init__(self, unit_of_work_factory: UnitOfWorkFactory) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    async def get_user(self, user_id: UUID) -> UserProfileResponse:
        """Return one enabled, non-deleted user profile."""
        async with self._unit_of_work_factory() as unit_of_work:
            user = await unit_of_work.users.get_by_id(user_id)
            if user is None or not user.is_enabled:
                raise ResourceNotFoundError()
            role = await unit_of_work.authentication.role_name(user.role_id)
        return self._profile(user, role or "Unknown")

    async def search_users(self, request: UserSearchRequest) -> UserSearchResponse:
        """Search enabled users using bounded opaque cursor pagination."""
        async with self._unit_of_work_factory() as unit_of_work:
            page = await unit_of_work.users.search(
                UserSearchQuery(
                    term=request.query,
                    department=request.department,
                    limit=request.limit,
                    cursor=request.after.root if request.after else None,
                )
            )
        users = tuple(user_summary(user) for user in page.items if user.is_enabled)
        return UserSearchResponse(
            users=users,
            page=CursorPageMetadata(
                next_cursor=(
                    OpaqueCursor(page.next_cursor) if page.next_cursor else None
                ),
                has_more=page.next_cursor is not None,
            ),
        )

    async def update_profile(
        self, requester: AuthenticatedUser, request: UpdateUserProfileRequest
    ) -> UserProfileResponse:
        """Update only the authenticated user's editable profile fields."""
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as unit_of_work:
            user = await unit_of_work.users.get_by_id(
                requester.user_id, for_update=True
            )
            if user is None or not user.is_enabled:
                raise ResourceNotFoundError()
            expected = user.version
            display_name = request.display_name or user.display_name
            status_message = (
                request.status_message
                if "status_message" in request.model_fields_set
                else user.status_message
            )
            user.update_profile(
                display_name=display_name, status_message=status_message, at=now
            )
            if "avatar" in request.model_fields_set:
                user.profile_picture_reference = request.avatar
            await unit_of_work.users.update_profile(user, expected_version=expected)
            role = await unit_of_work.authentication.role_name(user.role_id)
            await unit_of_work.commit()
        return self._profile(user, role or "Unknown")

    @staticmethod
    def _profile(user: User, role_name: str) -> UserProfileResponse:
        return UserProfileResponse(
            **user_summary(user).model_dump(),
            email=user.email,
            job_title=user.job_title,
            status_message=user.status_message,
            role=role_name,
            is_enabled=user.is_enabled,
            last_login=user.last_login,
        )
