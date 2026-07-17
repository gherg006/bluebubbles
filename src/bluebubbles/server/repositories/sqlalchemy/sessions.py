"""Async SQLAlchemy session repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.sessions import SessionORM
from bluebubbles.server.domain.sessions import Session
from bluebubbles.server.repositories.mapping.sessions import SessionMapper
from bluebubbles.server.repositories.sqlalchemy._common import (
    flush_changes,
    require_aware,
)


class SqlAlchemySessionRepository:
    """Persist hashed authentication sessions through a caller-owned session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, session: Session) -> Session:
        """Stage a new hashed-token session without committing it."""
        self._session.add(SessionMapper.to_orm(session))
        await flush_changes(self._session)
        return session

    async def get_by_id(self, session_id: UUID) -> Session | None:
        """Return a session regardless of active state."""
        record = await self._session.get(SessionORM, session_id)
        return SessionMapper.to_domain(record) if record is not None else None

    async def get_active(
        self, session_id: UUID, *, for_update: bool = False
    ) -> Session | None:
        """Return a currently active, unexpired session."""
        statement = select(SessionORM).where(
            SessionORM.id == session_id,
            SessionORM.is_active.is_(True),
            SessionORM.invalidated_at.is_(None),
            SessionORM.refresh_expires_at > func.now(),
        )
        if for_update:
            statement = statement.with_for_update()
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return SessionMapper.to_domain(record) if record is not None else None

    async def get_active_by_id(
        self, session_id: UUID, *, for_update: bool = False
    ) -> Session | None:
        """Return a currently active session using the contract alias."""
        return await self.get_active(session_id, for_update=for_update)

    async def list_active_for_user(self, user_id: UUID) -> list[Session]:
        """Return all unexpired active sessions for one user."""
        statement = (
            select(SessionORM)
            .where(
                SessionORM.user_id == user_id,
                SessionORM.is_active.is_(True),
                SessionORM.invalidated_at.is_(None),
                SessionORM.refresh_expires_at > func.now(),
            )
            .order_by(SessionORM.created_at.desc(), SessionORM.id)
        )
        return [
            SessionMapper.to_domain(record)
            for record in (await self._session.scalars(statement)).all()
        ]

    async def update_last_seen(self, session_id: UUID, last_seen_at: datetime) -> bool:
        """Advance session activity without extending absolute expiry."""
        require_aware(last_seen_at, "last_seen_at")
        result = await self._session.execute(
            update(SessionORM)
            .where(SessionORM.id == session_id, SessionORM.is_active.is_(True))
            .values(last_seen_at=last_seen_at)
        )
        return result.rowcount == 1

    async def update_refresh_token(
        self,
        session_id: UUID,
        refresh_token_hash: bytes,
        token_version: int,
        last_seen_at: datetime,
    ) -> None:
        """Rotate a hash and token version for an active session."""
        updated = await self.rotate_refresh_token(
            session_id, refresh_token_hash, token_version, last_seen_at
        )
        if not updated:
            raise ValueError("Active session was not found for token rotation")

    async def rotate_refresh_token(
        self,
        session_id: UUID,
        refresh_token_hash: bytes,
        token_version: int,
        last_seen_at: datetime,
        access_expires_at: datetime | None = None,
    ) -> bool:
        """Atomically replace a refresh hash after expected version advance."""
        require_aware(last_seen_at, "last_seen_at")
        if not refresh_token_hash or token_version < 1:
            raise ValueError("Refresh hash and positive token version are required")
        values: dict[str, object] = {
            "previous_refresh_token_hash": SessionORM.refresh_token_hash,
            "refresh_token_hash": refresh_token_hash,
            "token_version": token_version,
            "last_seen_at": last_seen_at,
        }
        if access_expires_at is not None:
            require_aware(access_expires_at, "access_expires_at")
            values["access_expires_at"] = access_expires_at
        result = await self._session.execute(
            update(SessionORM)
            .where(
                SessionORM.id == session_id,
                SessionORM.is_active.is_(True),
                SessionORM.token_version < token_version,
            )
            .values(**values)
        )
        return result.rowcount == 1

    async def invalidate(
        self, session_id: UUID, invalidated_at: datetime, reason: str
    ) -> bool:
        """Irreversibly invalidate one active session."""
        require_aware(invalidated_at, "invalidated_at")
        if not reason.strip():
            raise ValueError("Invalidation reason is required")
        result = await self._session.execute(
            update(SessionORM)
            .where(SessionORM.id == session_id, SessionORM.is_active.is_(True))
            .values(
                is_active=False,
                invalidated_at=invalidated_at,
                invalidation_reason=reason.strip(),
                last_seen_at=invalidated_at,
            )
        )
        return result.rowcount == 1

    async def invalidate_all_for_user(
        self, user_id: UUID, invalidated_at: datetime, reason: str
    ) -> int:
        """Invalidate every active session belonging to one user."""
        require_aware(invalidated_at, "invalidated_at")
        if not reason.strip():
            raise ValueError("Invalidation reason is required")
        result = await self._session.execute(
            update(SessionORM)
            .where(SessionORM.user_id == user_id, SessionORM.is_active.is_(True))
            .values(
                is_active=False,
                invalidated_at=invalidated_at,
                invalidation_reason=reason.strip(),
                last_seen_at=invalidated_at,
            )
        )
        return result.rowcount or 0

    async def list_expired(self, at: datetime, *, limit: int) -> list[Session]:
        """Return a bounded oldest-first cleanup candidate batch."""
        require_aware(at, "at")
        if limit < 1:
            raise ValueError("Cleanup limit must be positive")
        statement = (
            select(SessionORM)
            .where(
                or_(
                    SessionORM.refresh_expires_at <= at,
                    SessionORM.access_expires_at <= at,
                )
            )
            .order_by(SessionORM.refresh_expires_at, SessionORM.id)
            .limit(limit)
        )
        return [
            SessionMapper.to_domain(record)
            for record in (await self._session.scalars(statement)).all()
        ]

    async def delete_expired(self, at: datetime, *, limit: int) -> int:
        """Delete only a bounded batch of already expired sessions."""
        candidates = await self.list_expired(at, limit=limit)
        if not candidates:
            return 0
        result = await self._session.execute(
            delete(SessionORM).where(
                SessionORM.id.in_([session.id for session in candidates])
            )
        )
        return result.rowcount or 0
