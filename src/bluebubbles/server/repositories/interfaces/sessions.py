"""Session repository protocol."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from bluebubbles.server.domain.sessions import Session


class SessionRepository(Protocol):
    """Define hashed-token session persistence operations."""

    async def create(self, session: Session) -> Session: ...

    async def get_by_id(self, session_id: UUID) -> Session | None: ...

    async def get_active(
        self, session_id: UUID, *, for_update: bool = False
    ) -> Session | None: ...

    async def get_active_by_id(
        self, session_id: UUID, *, for_update: bool = False
    ) -> Session | None: ...

    async def list_active_for_user(self, user_id: UUID) -> list[Session]: ...

    async def update_last_seen(
        self, session_id: UUID, last_seen_at: datetime
    ) -> bool: ...

    async def update_refresh_token(
        self,
        session_id: UUID,
        refresh_token_hash: bytes,
        token_version: int,
        last_seen_at: datetime,
    ) -> None: ...

    async def rotate_refresh_token(
        self,
        session_id: UUID,
        refresh_token_hash: bytes,
        token_version: int,
        last_seen_at: datetime,
        access_expires_at: datetime | None = None,
    ) -> bool: ...

    async def invalidate(
        self, session_id: UUID, invalidated_at: datetime, reason: str
    ) -> bool: ...

    async def invalidate_all_for_user(
        self, user_id: UUID, invalidated_at: datetime, reason: str
    ) -> int: ...

    async def list_expired(self, at: datetime, *, limit: int) -> list[Session]: ...

    async def delete_expired(self, at: datetime, *, limit: int) -> int: ...
