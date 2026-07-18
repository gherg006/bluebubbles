"""Async SQLAlchemy transactional outbox repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.outbox import OutboxEventORM
from bluebubbles.server.domain.outbox import OutboxEvent
from bluebubbles.server.repositories.sqlalchemy._common import (
    flush_changes,
    require_aware,
)


class SqlAlchemyOutboxRepository:
    """Persist and safely claim post-commit publication events."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: OutboxEvent) -> OutboxEvent:
        """Stage a plaintext-free outbox event in the business transaction."""
        self._session.add(
            OutboxEventORM(
                id=event.id,
                event_type=event.event_type,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                protocol_version=event.protocol_version,
                payload=dict(event.payload),
                created_at=event.created_at,
                published_at=event.published_at,
                attempt_count=event.attempts,
                next_attempt_at=event.available_at,
                last_error_code=None,
                locked_at=None,
                locked_by=None,
            )
        )
        await flush_changes(self._session)
        return event

    async def claim_batch(
        self, worker_id: str, limit: int, now: datetime
    ) -> list[OutboxEvent]:
        """Claim a bounded due batch using PostgreSQL skip-locked semantics."""
        require_aware(now, "now")
        if not worker_id.strip() or limit < 1:
            raise ValueError("Worker identifier and positive limit are required")
        statement = (
            select(OutboxEventORM)
            .where(
                OutboxEventORM.published_at.is_(None),
                or_(
                    OutboxEventORM.next_attempt_at.is_(None),
                    OutboxEventORM.next_attempt_at <= now,
                ),
                OutboxEventORM.locked_at.is_(None),
            )
            .order_by(OutboxEventORM.created_at, OutboxEventORM.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        records = list((await self._session.scalars(statement)).all())
        for record in records:
            record.locked_at = now
            record.locked_by = worker_id
        await flush_changes(self._session)
        return [self._to_domain(record) for record in records]

    async def mark_published(self, event_id: UUID, published_at: datetime) -> None:
        """Mark a claimed event published and clear its worker lock."""
        require_aware(published_at, "published_at")
        result = await self._session.execute(
            update(OutboxEventORM)
            .where(
                OutboxEventORM.id == event_id,
                OutboxEventORM.published_at.is_(None),
            )
            .values(
                published_at=published_at,
                locked_at=None,
                locked_by=None,
                last_error_code=None,
            )
        )
        if result.rowcount != 1:
            raise ValueError("Unpublished outbox event was not found")

    async def mark_failed(
        self,
        event_id: UUID,
        error_code: str,
        next_attempt_at: datetime,
    ) -> None:
        """Record a safe failure code and schedule a bounded retry."""
        require_aware(next_attempt_at, "next_attempt_at")
        if not error_code.strip():
            raise ValueError("Safe outbox error code is required")
        result = await self._session.execute(
            update(OutboxEventORM)
            .where(
                OutboxEventORM.id == event_id,
                OutboxEventORM.published_at.is_(None),
            )
            .values(
                attempt_count=OutboxEventORM.attempt_count + 1,
                last_error_code=error_code.strip(),
                next_attempt_at=next_attempt_at,
                locked_at=None,
                locked_by=None,
            )
        )
        if result.rowcount != 1:
            raise ValueError("Unpublished outbox event was not found")

    async def release_expired_locks(self, before: datetime) -> int:
        """Release abandoned worker claims older than the supplied boundary."""
        require_aware(before, "before")
        result = await self._session.execute(
            update(OutboxEventORM)
            .where(
                OutboxEventORM.published_at.is_(None),
                OutboxEventORM.locked_at < before,
            )
            .values(locked_at=None, locked_by=None)
        )
        return result.rowcount or 0

    async def list_repeated_failures(
        self, minimum_attempts: int, *, limit: int
    ) -> list[OutboxEvent]:
        """Return a bounded diagnostic list without raw exception text."""
        if minimum_attempts < 1 or limit < 1:
            raise ValueError("Attempts and limit must be positive")
        statement = (
            select(OutboxEventORM)
            .where(
                OutboxEventORM.published_at.is_(None),
                OutboxEventORM.attempt_count >= minimum_attempts,
            )
            .order_by(OutboxEventORM.attempt_count.desc(), OutboxEventORM.id)
            .limit(limit)
        )
        return [
            self._to_domain(record)
            for record in (await self._session.scalars(statement)).all()
        ]

    async def delete_old_published(self, before: datetime, *, limit: int) -> int:
        """Delete only a bounded batch of published retention candidates."""
        require_aware(before, "before")
        if limit < 1:
            raise ValueError("Cleanup limit must be positive")
        ids = list(
            (
                await self._session.scalars(
                    select(OutboxEventORM.id)
                    .where(
                        OutboxEventORM.published_at.is_not(None),
                        OutboxEventORM.published_at < before,
                    )
                    .order_by(OutboxEventORM.published_at, OutboxEventORM.id)
                    .limit(limit)
                )
            ).all()
        )
        if not ids:
            return 0
        result = await self._session.execute(
            delete(OutboxEventORM).where(OutboxEventORM.id.in_(ids))
        )
        return result.rowcount or 0

    async def count_unpublished(self) -> int:
        """Return the current durable delivery backlog size."""
        value = await self._session.scalar(
            select(func.count())
            .select_from(OutboxEventORM)
            .where(OutboxEventORM.published_at.is_(None))
        )
        return int(value or 0)

    @staticmethod
    def _to_domain(record: OutboxEventORM) -> OutboxEvent:
        return OutboxEvent(
            id=record.id,
            created_at=record.created_at,
            updated_at=record.published_at or record.locked_at or record.created_at,
            event_type=record.event_type,
            aggregate_type=record.aggregate_type,
            aggregate_id=record.aggregate_id,
            protocol_version=record.protocol_version,
            payload=record.payload,
            available_at=record.next_attempt_at or record.created_at,
            published_at=record.published_at,
            attempts=record.attempt_count,
        )
