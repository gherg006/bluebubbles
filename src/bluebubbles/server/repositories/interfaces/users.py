"""User repository protocol."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from bluebubbles.server.domain.users import User
from bluebubbles.server.repositories.types import CursorPage, UserSearchQuery


class UserRepository(Protocol):
    """Define persistent user operations without authorization policy."""

    async def get_by_id(
        self, user_id: UUID, *, for_update: bool = False
    ) -> User | None: ...

    async def get_by_normalised_username(self, username: str) -> User | None: ...

    async def get_by_directory_guid(self, directory_guid: UUID) -> User | None: ...

    async def search(self, query: UserSearchQuery) -> CursorPage[User]: ...

    async def create(self, user: User) -> User: ...

    async def update(
        self, user: User, *, expected_version: int | None = None
    ) -> User: ...

    async def update_profile(self, user: User, *, expected_version: int) -> User: ...

    async def set_enabled(
        self, user_id: UUID, enabled: bool, *, expected_version: int
    ) -> bool: ...

    async def set_role(
        self, user_id: UUID, role_id: UUID, *, expected_version: int
    ) -> bool: ...

    async def soft_delete(
        self, user_id: UUID, deleted_at: datetime, *, expected_version: int
    ) -> bool: ...
