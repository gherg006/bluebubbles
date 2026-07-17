"""Authentication-specific persistence protocol."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from bluebubbles.server.domain.users import LocalCredential, Permission, User


class AuthenticationRepository(Protocol):
    """Define credential, attempt, and permission operations."""

    async def get_local_identity(
        self, username: str
    ) -> tuple[User, LocalCredential] | None: ...

    async def update_local_credential(self, credential: LocalCredential) -> None: ...

    async def add_login_attempt(
        self,
        *,
        attempt_id: UUID,
        normalised_username: str,
        source_ip: str | None,
        result: str,
        failure_category: str | None,
        attempted_at: datetime,
        correlation_id: UUID,
    ) -> None: ...

    async def count_recent_failures(
        self, *, normalised_username: str, source_ip: str | None, since: datetime
    ) -> tuple[int, int]: ...

    async def permissions_for_role(self, role_id: UUID) -> frozenset[Permission]: ...

    async def role_name(self, role_id: UUID) -> str | None: ...
