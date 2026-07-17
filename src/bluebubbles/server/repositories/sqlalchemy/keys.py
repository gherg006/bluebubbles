"""Async SQLAlchemy public-key repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.keys import UserPublicKeyORM
from bluebubbles.server.domain.users import PublicKeyRecord
from bluebubbles.server.repositories.sqlalchemy._common import (
    flush_changes,
    require_aware,
)


class SqlAlchemyPublicKeyRepository:
    """Persist public-only, versioned user keys; never private material."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, key: PublicKeyRecord, *, key_type: str) -> PublicKeyRecord:
        """Stage one public key revision."""
        if key_type not in {"encryption", "signing"}:
            raise ValueError("Key type must be encryption or signing")
        self._session.add(
            UserPublicKeyORM(
                id=key.id,
                user_id=key.user_id,
                key_type=key_type,
                key_version=key.key_version,
                public_key=key.public_key,
                fingerprint=key.fingerprint,
                algorithm=key.algorithm,
                expires_at=None,
                revoked_at=key.revoked_at,
                revocation_reason=None,
                is_primary=key.revoked_at is None,
                created_at=key.created_at,
            )
        )
        await flush_changes(self._session)
        return key

    async def get_active(
        self, user_id: UUID, *, key_type: str
    ) -> PublicKeyRecord | None:
        """Return the active primary key of one type."""
        statement = select(UserPublicKeyORM).where(
            UserPublicKeyORM.user_id == user_id,
            UserPublicKeyORM.key_type == key_type,
            UserPublicKeyORM.is_primary.is_(True),
            UserPublicKeyORM.revoked_at.is_(None),
        )
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return self._to_domain(record) if record is not None else None

    async def list_for_user(self, user_id: UUID) -> list[PublicKeyRecord]:
        """Return all retained public key revisions newest first."""
        statement = (
            select(UserPublicKeyORM)
            .where(UserPublicKeyORM.user_id == user_id)
            .order_by(UserPublicKeyORM.key_version.desc(), UserPublicKeyORM.id)
        )
        return [
            self._to_domain(record)
            for record in (await self._session.scalars(statement)).all()
        ]

    async def revoke(self, key_id: UUID, revoked_at: datetime, reason: str) -> bool:
        """Irreversibly revoke one active public key revision."""
        require_aware(revoked_at, "revoked_at")
        if not reason.strip():
            raise ValueError("Key revocation reason is required")
        result = await self._session.execute(
            update(UserPublicKeyORM)
            .where(
                UserPublicKeyORM.id == key_id,
                UserPublicKeyORM.revoked_at.is_(None),
            )
            .values(
                revoked_at=revoked_at,
                revocation_reason=reason.strip(),
                is_primary=False,
            )
        )
        return result.rowcount == 1

    @staticmethod
    def _to_domain(record: UserPublicKeyORM) -> PublicKeyRecord:
        return PublicKeyRecord(
            id=record.id,
            created_at=record.created_at,
            updated_at=record.revoked_at or record.created_at,
            user_id=record.user_id,
            key_version=record.key_version,
            algorithm=record.algorithm,
            public_key=record.public_key,
            fingerprint=record.fingerprint,
            revoked_at=record.revoked_at,
        )
