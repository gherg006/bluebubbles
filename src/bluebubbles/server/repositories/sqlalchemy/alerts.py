"""Async SQLAlchemy security-alert repository."""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.audit import SecurityAlertORM
from bluebubbles.server.domain.alerts import SecurityAlert, SecurityAlertState
from bluebubbles.server.repositories.sqlalchemy._common import flush_changes


class SqlAlchemySecurityAlertRepository:
    """Persist alert occurrences and administrator transitions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, alert_id: UUID, *, for_update: bool = False
    ) -> SecurityAlert | None:
        statement = select(SecurityAlertORM).where(SecurityAlertORM.id == alert_id)
        if for_update:
            statement = statement.with_for_update()
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return self._to_domain(record) if record is not None else None

    async def get_open_by_code(
        self, code: str, *, for_update: bool = False
    ) -> SecurityAlert | None:
        statement = (
            select(SecurityAlertORM)
            .where(
                SecurityAlertORM.alert_type == code,
            )
            .order_by(SecurityAlertORM.created_at.desc())
            .limit(1)
        )
        if for_update:
            statement = statement.with_for_update()
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return self._to_domain(record) if record is not None else None

    async def add(self, alert: SecurityAlert) -> SecurityAlert:
        self._session.add(
            SecurityAlertORM(
                id=alert.id,
                created_at=alert.created_at,
                updated_at=alert.updated_at,
                alert_type=alert.code,
                severity=alert.severity,
                title=alert.title,
                summary=alert.summary,
                source_component=alert.source_component,
                status=alert.state.value,
                occurrence_count=alert.occurrence_count,
                acknowledged_at=alert.acknowledged_at,
                acknowledged_by=alert.acknowledged_by,
                resolved_at=alert.resolved_at,
                resolved_by=alert.resolved_by,
                resolution_notes=alert.resolution_notes,
            )
        )
        await flush_changes(self._session)
        return alert

    async def update(
        self, alert: SecurityAlert, *, expected_version: int
    ) -> SecurityAlert:
        result = await self._session.execute(
            update(SecurityAlertORM)
            .where(
                SecurityAlertORM.id == alert.id,
                SecurityAlertORM.updated_at < alert.updated_at,
            )
            .values(
                updated_at=alert.updated_at,
                status=alert.state.value,
                occurrence_count=alert.occurrence_count,
                acknowledged_at=alert.acknowledged_at,
                acknowledged_by=alert.acknowledged_by,
                resolved_at=alert.resolved_at,
                resolved_by=alert.resolved_by,
                resolution_notes=alert.resolution_notes,
            )
        )
        del expected_version
        if result.rowcount != 1:
            raise ValueError("Security alert changed concurrently")
        return alert

    async def list_recent(self, *, limit: int) -> tuple[SecurityAlert, ...]:
        if not 1 <= limit <= 200:
            raise ValueError("Alert limit must be between 1 and 200")
        records = (
            await self._session.scalars(
                select(SecurityAlertORM)
                .order_by(SecurityAlertORM.created_at.desc(), SecurityAlertORM.id)
                .limit(limit)
            )
        ).all()
        return tuple(self._to_domain(record) for record in records)

    @staticmethod
    def _to_domain(record: SecurityAlertORM) -> SecurityAlert:
        return SecurityAlert(
            id=record.id,
            created_at=record.created_at,
            updated_at=record.updated_at,
            version=1,
            code=record.alert_type,
            summary=record.summary,
            state=SecurityAlertState(record.status),
            severity=record.severity,
            title=record.title,
            source_component=record.source_component,
            occurrence_count=record.occurrence_count,
            acknowledged_by=record.acknowledged_by,
            acknowledged_at=record.acknowledged_at,
            resolved_at=record.resolved_at,
            resolved_by=record.resolved_by,
            resolution_notes=record.resolution_notes,
        )
