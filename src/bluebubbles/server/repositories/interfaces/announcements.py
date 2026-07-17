"""Announcement repository protocol."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from bluebubbles.server.domain.announcements import Announcement


class AnnouncementRepository(Protocol):
    """Define administrator-authored announcement persistence."""

    async def add(self, announcement: Announcement) -> Announcement: ...

    async def get_by_id(self, announcement_id: UUID) -> Announcement | None: ...

    async def list_current(self, at: datetime, *, limit: int) -> list[Announcement]: ...

    async def acknowledge(
        self,
        announcement_id: UUID,
        user_id: UUID,
        acknowledged_at: datetime,
        session_id: UUID | None = None,
    ) -> None: ...
