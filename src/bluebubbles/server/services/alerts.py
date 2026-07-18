"""Deduplicated security-alert lifecycle and audited review transitions."""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.alerts import SecurityAlert
from bluebubbles.server.domain.audit import AuditSeverity
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission
from bluebubbles.server.services.audit import AuditWriter
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.shared.errors.exceptions import ResourceNotFoundError, ValidationError
from bluebubbles.shared.models.administration import SecurityAlertResponse


class SecurityAlertService:
    """Create trusted alert occurrences and audit administrator transitions."""

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

    async def create_or_update(
        self,
        *,
        code: str,
        title: str,
        summary: str,
        severity: str,
        source_component: str,
    ) -> SecurityAlertResponse:
        """Deduplicate one trusted internal occurrence and reopen after recurrence."""
        now = self._clock()
        async with self._uow_factory() as uow:
            repository = uow.security_alerts
            if repository is None:
                raise RuntimeError("Security alert repository is not configured")
            alert = await repository.get_open_by_code(code, for_update=True)
            if alert is None:
                alert = SecurityAlert(
                    id=uuid4(),
                    created_at=now,
                    updated_at=now,
                    code=code,
                    title=title,
                    summary=summary,
                    severity=severity,
                    source_component=source_component,
                )
                await repository.add(alert)
            else:
                expected = alert.version
                alert.recur(now)
                await repository.update(alert, expected_version=expected)
            await uow.commit()
        return self._response(alert)

    async def list_alerts(
        self, requester: AuthenticatedUser, *, limit: int = 50
    ) -> tuple[SecurityAlertResponse, ...]:
        """Return recent safe alert metadata to an authorised reviewer."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.ALERT_VIEW
        )
        async with self._uow_factory() as uow:
            repository = uow.security_alerts
            if repository is None:
                raise RuntimeError("Security alert repository is not configured")
            alerts = await repository.list_recent(limit=limit)
        return tuple(self._response(alert) for alert in alerts)

    async def acknowledge(
        self, requester: AuthenticatedUser, alert_id: UUID, notes: str
    ) -> SecurityAlertResponse:
        """Acknowledge an open alert and record the state change in the same commit."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.ALERT_ACKNOWLEDGE
        )
        return await self._transition(requester, alert_id, notes, resolve=False)

    async def resolve(
        self, requester: AuthenticatedUser, alert_id: UUID, notes: str
    ) -> SecurityAlertResponse:
        """Resolve an alert only with non-empty investigation notes."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.ALERT_RESOLVE
        )
        return await self._transition(requester, alert_id, notes, resolve=True)

    async def _transition(
        self,
        requester: AuthenticatedUser,
        alert_id: UUID,
        notes: str,
        *,
        resolve: bool,
    ) -> SecurityAlertResponse:
        notes = notes.strip()
        if not notes or len(notes) > 2000:
            raise ValidationError(user_message="Alert transition notes are required.")
        now = self._clock()
        async with self._uow_factory() as uow:
            repository = uow.security_alerts
            if repository is None:
                raise RuntimeError("Security alert repository is not configured")
            alert = await repository.get_by_id(alert_id, for_update=True)
            if alert is None:
                raise ResourceNotFoundError()
            expected = alert.version
            if resolve:
                alert.resolve(now, requester.user_id, notes)
                action = "security_alert.resolved"
            else:
                alert.acknowledge(requester.user_id, now)
                action = "security_alert.acknowledged"
            await repository.update(alert, expected_version=expected)
            await self._audit.append(
                uow.audit,
                event_type=action,
                occurred_at=now,
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.WARNING,
                details={
                    "alert_id": str(alert.id),
                    "alert_code": alert.code,
                    "notes": notes,
                },
            )
            await uow.commit()
        return self._response(alert)

    @staticmethod
    def _response(alert: SecurityAlert) -> SecurityAlertResponse:
        return SecurityAlertResponse(
            id=alert.id,
            alert_type=alert.code,
            severity=alert.severity,
            summary=alert.summary,
            created_at=alert.created_at,
            acknowledged_at=alert.acknowledged_at,
            status=alert.state.value,
            occurrence_count=alert.occurrence_count,
            resolved_at=alert.resolved_at,
        )
