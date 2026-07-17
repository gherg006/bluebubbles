"""Async SQLAlchemy append-only audit repository."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.audit import AuditChainStateORM, AuditEventORM
from bluebubbles.server.domain.audit import AuditChainState, AuditEvent
from bluebubbles.server.repositories.mapping.audit import AuditMapper
from bluebubbles.server.repositories.sqlalchemy._common import flush_changes
from bluebubbles.server.repositories.types import (
    AuditQuery,
    CursorPage,
    decode_cursor,
    encode_cursor,
)
from bluebubbles.shared.errors.exceptions import RepositoryError


class SqlAlchemyAuditRepository:
    """Append immutable audit events under a singleton chain-head row lock."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def lock_chain_state(self) -> AuditChainState:
        """Lock and return the singleton chain head for the current transaction."""
        statement = (
            select(AuditChainStateORM)
            .where(AuditChainStateORM.id == 1)
            .with_for_update()
        )
        record = (await self._session.execute(statement)).scalar_one_or_none()
        if record is None:
            raise RepositoryError(
                user_message="The audit chain is not initialized.",
                technical_message="The audit_chain_state singleton row is missing.",
            )
        last_event_id = None
        if record.latest_sequence_number:
            last_event_id = await self._session.scalar(
                select(AuditEventORM.id).where(
                    AuditEventORM.sequence_number == record.latest_sequence_number
                )
            )
        return AuditChainState(
            last_event_id=last_event_id,
            last_hash=record.latest_hash,
            event_count=record.latest_sequence_number,
        )

    async def get_latest_chain_state(self) -> AuditChainState:
        """Return and lock the latest chain state for safe append coordination."""
        return await self.lock_chain_state()

    async def append(self, event: AuditEvent) -> AuditEvent:
        """Append one immutable event after validating the locked chain link."""
        state = await self.lock_chain_state()
        if event.previous_hash != state.last_hash:
            raise ValueError("Audit event does not extend the current chain head")
        sequence = state.event_count + 1
        self._session.add(
            AuditEventORM(
                sequence_number=sequence,
                id=event.id,
                category="application",
                action=event.event_type,
                severity=event.severity.value,
                actor_user_id=event.actor_id,
                target_type=None,
                target_id=None,
                session_id=None,
                source_ip=event.source_address,
                result="success",
                details=dict(event.details),
                timestamp=event.occurred_at,
                correlation_id=event.id,
                previous_hash=event.previous_hash,
                entry_hash=event.event_hash,
            )
        )
        await self._session.execute(
            update(AuditChainStateORM)
            .where(AuditChainStateORM.id == 1)
            .values(
                latest_sequence_number=sequence,
                latest_hash=event.event_hash,
                updated_at=event.occurred_at,
            )
        )
        await flush_changes(self._session)
        return event

    async def update_chain_state(self, state: AuditChainState) -> None:
        """Persist a validated chain head while retaining append-only events."""
        result = await self._session.execute(
            update(AuditChainStateORM)
            .where(AuditChainStateORM.id == 1)
            .values(
                latest_sequence_number=state.event_count,
                latest_hash=state.last_hash,
            )
        )
        if result.rowcount != 1:
            raise ValueError("Audit chain state is not initialized")

    async def list_events(self, query: AuditQuery) -> CursorPage[AuditEvent]:
        """Return a stable forward sequence page of immutable audit events."""
        statement = select(AuditEventORM)
        minimum = query.minimum_sequence
        if query.cursor is not None:
            (value,) = decode_cursor(query.cursor, 1)
            if not isinstance(value, int):
                raise ValueError("Invalid audit cursor")
            minimum = max(minimum or 1, value + 1)
        if minimum is not None:
            statement = statement.where(AuditEventORM.sequence_number >= minimum)
        if query.category is not None:
            statement = statement.where(AuditEventORM.category == query.category)
        if query.actor_user_id is not None:
            statement = statement.where(
                AuditEventORM.actor_user_id == query.actor_user_id
            )
        statement = statement.order_by(AuditEventORM.sequence_number).limit(
            query.limit + 1
        )
        records = list((await self._session.scalars(statement)).all())
        has_more = len(records) > query.limit
        selected = records[: query.limit]
        cursor = (
            encode_cursor(selected[-1].sequence_number)
            if has_more and selected
            else None
        )
        return CursorPage(
            items=tuple(AuditMapper.to_domain(record) for record in selected),
            next_cursor=cursor,
        )

    async def get_by_sequence(self, sequence: int) -> AuditEvent | None:
        """Return one immutable event by chain sequence."""
        if sequence < 1:
            raise ValueError("Audit sequence must be positive")
        record = await self._session.get(AuditEventORM, sequence)
        return AuditMapper.to_domain(record) if record is not None else None

    async def list_range(
        self, first_sequence: int, last_sequence: int
    ) -> list[AuditEvent]:
        """Return one inclusive sequence range in chain order."""
        if first_sequence < 1 or last_sequence < first_sequence:
            raise ValueError("Invalid audit sequence range")
        statement = (
            select(AuditEventORM)
            .where(
                AuditEventORM.sequence_number >= first_sequence,
                AuditEventORM.sequence_number <= last_sequence,
            )
            .order_by(AuditEventORM.sequence_number)
        )
        return [
            AuditMapper.to_domain(record)
            for record in (await self._session.scalars(statement)).all()
        ]

    async def verify_range_data(
        self, first_sequence: int, last_sequence: int
    ) -> list[AuditEvent]:
        """Return immutable range data for domain-level hash verification."""
        return await self.list_range(first_sequence, last_sequence)
