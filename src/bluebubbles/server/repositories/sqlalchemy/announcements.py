"""Async SQLAlchemy announcement repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.announcements import (
    AnnouncementAcknowledgementORM,
    AnnouncementORM,
)
from bluebubbles.server.domain.announcements import Announcement
from bluebubbles.server.repositories.sqlalchemy._common import (
    flush_changes,
    require_aware,
)
from bluebubbles.shared.models.announcements import (
    AnnouncementPriority,
    AnnouncementTargetType,
)


class SqlAlchemyAnnouncementRepository:
    """Persist deliberate organizational plaintext separately from messages."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, announcement: Announcement) -> Announcement:
        """Stage one validated announcement without committing."""
        self._session.add(
            AnnouncementORM(
                id=announcement.id,
                created_at=announcement.created_at,
                updated_at=announcement.updated_at,
                version=announcement.version,
                title=announcement.title,
                body=announcement.body,
                author_id=announcement.author_id,
                priority=announcement.priority.value,
                target_type=announcement.target_type.value,
                target_reference=",".join(map(str, announcement.target_ids)) or None,
                published_at=announcement.published_at,
                expires_at=announcement.expires_at,
                withdrawn_at=announcement.withdrawn_at,
                requires_acknowledgement=False,
            )
        )
        await flush_changes(self._session)
        return announcement

    async def get_by_id(self, announcement_id: UUID) -> Announcement | None:
        """Return one announcement by identifier."""
        record = await self._session.get(AnnouncementORM, announcement_id)
        return self._to_domain(record) if record is not None else None

    async def update(
        self, announcement: Announcement, *, expected_version: int
    ) -> Announcement:
        """Persist one optimistic publication or withdrawal transition."""
        result = await self._session.execute(
            update(AnnouncementORM)
            .where(
                AnnouncementORM.id == announcement.id,
                AnnouncementORM.version == expected_version,
            )
            .values(
                published_at=announcement.published_at,
                withdrawn_at=announcement.withdrawn_at,
                updated_at=announcement.updated_at,
                version=announcement.version,
            )
        )
        if result.rowcount != 1:
            raise ValueError("Announcement changed concurrently")
        return announcement

    async def list_current(self, at: datetime, *, limit: int) -> list[Announcement]:
        """Return a bounded newest-first list of currently visible announcements."""
        require_aware(at, "at")
        if limit < 1:
            raise ValueError("Announcement limit must be positive")
        statement = (
            select(AnnouncementORM)
            .where(
                AnnouncementORM.published_at.is_not(None),
                AnnouncementORM.published_at <= at,
                AnnouncementORM.withdrawn_at.is_(None),
                or_(
                    AnnouncementORM.expires_at.is_(None),
                    AnnouncementORM.expires_at > at,
                ),
            )
            .order_by(AnnouncementORM.published_at.desc(), AnnouncementORM.id)
            .limit(limit)
        )
        return [
            self._to_domain(record)
            for record in (await self._session.scalars(statement)).all()
        ]

    async def acknowledge(
        self,
        announcement_id: UUID,
        user_id: UUID,
        acknowledged_at: datetime,
        session_id: UUID | None = None,
    ) -> None:
        """Stage an idempotency-constrained user acknowledgement."""
        require_aware(acknowledged_at, "acknowledged_at")
        self._session.add(
            AnnouncementAcknowledgementORM(
                announcement_id=announcement_id,
                user_id=user_id,
                session_id=session_id,
                acknowledged_at=acknowledged_at,
            )
        )
        await flush_changes(self._session)

    @staticmethod
    def _to_domain(record: AnnouncementORM) -> Announcement:
        targets = (
            tuple(UUID(value) for value in record.target_reference.split(","))
            if record.target_reference
            else ()
        )
        return Announcement(
            id=record.id,
            created_at=record.created_at,
            updated_at=record.updated_at,
            version=record.version,
            author_id=record.author_id,
            title=record.title,
            body=record.body,
            priority=AnnouncementPriority(record.priority),
            target_type=AnnouncementTargetType(record.target_type),
            target_ids=targets,
            published_at=record.published_at,
            expires_at=record.expires_at,
            withdrawn_at=record.withdrawn_at,
        )
