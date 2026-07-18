"""Audited organisational announcement publication and withdrawal."""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.announcements import Announcement
from bluebubbles.server.domain.audit import AuditSeverity
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission
from bluebubbles.server.services.audit import AuditWriter
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.shared.errors.exceptions import ResourceNotFoundError, ValidationError
from bluebubbles.shared.models.announcements import (
    AnnouncementResponse,
    CreateAnnouncementRequest,
)


class AnnouncementService:
    """Publish deliberate plaintext announcements separately from messages."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        audit_writer: AuditWriter | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._uow_factory = unit_of_work_factory
        self._permissions = permission_service
        self._audit = audit_writer or AuditWriter()
        self._clock = clock

    async def publish(
        self, requester: AuthenticatedUser, request: CreateAnnouncementRequest
    ) -> AnnouncementResponse:
        """Persist and audit one validated published announcement atomically."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.ANNOUNCEMENT_MANAGE
        )
        now = self._clock()
        announcement = Announcement(
            id=uuid4(),
            created_at=now,
            updated_at=now,
            author_id=requester.user_id,
            title=request.title,
            body=request.body,
            priority=request.priority,
            target_type=request.target_type,
            target_ids=request.target_ids,
            expires_at=request.expires_at,
        )
        announcement.publish(now)
        async with self._uow_factory() as uow:
            await uow.announcements.add(announcement)
            await self._audit.append(
                uow.audit,
                event_type="announcement.published",
                occurred_at=now,
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.INFORMATIONAL,
                details={
                    "announcement_id": str(announcement.id),
                    "priority": announcement.priority.value,
                },
            )
            await uow.commit()
        return self._response(announcement)

    async def withdraw(
        self, requester: AuthenticatedUser, announcement_id: UUID, reason: str
    ) -> AnnouncementResponse:
        """Withdraw a current announcement with a mandatory audited reason."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.ANNOUNCEMENT_MANAGE
        )
        reason = reason.strip()
        if not reason or len(reason) > 1000:
            raise ValidationError(user_message="A withdrawal reason is required.")
        now = self._clock()
        async with self._uow_factory() as uow:
            announcement = await uow.announcements.get_by_id(announcement_id)
            if announcement is None:
                raise ResourceNotFoundError()
            expected = announcement.version
            announcement.withdraw(now)
            await uow.announcements.update(announcement, expected_version=expected)
            await self._audit.append(
                uow.audit,
                event_type="announcement.withdrawn",
                occurred_at=now,
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.WARNING,
                details={"announcement_id": str(announcement.id), "reason": reason},
            )
            await uow.commit()
        return self._response(announcement)

    @staticmethod
    def _response(announcement: Announcement) -> AnnouncementResponse:
        assert announcement.published_at is not None
        return AnnouncementResponse(
            id=announcement.id,
            author_id=announcement.author_id,
            title=announcement.title,
            body=announcement.body,
            priority=announcement.priority,
            target_type=announcement.target_type,
            published_at=announcement.published_at,
            expires_at=announcement.expires_at,
        )
