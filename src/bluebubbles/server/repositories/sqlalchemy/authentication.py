"""SQLAlchemy authentication metadata repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.identity import (
    LocalCredentialORM,
    PermissionORM,
    RoleORM,
    RolePermissionORM,
    UserORM,
)
from bluebubbles.server.database.models.sessions import LoginAttemptORM
from bluebubbles.server.domain.users import (
    LocalCredential,
    Permission,
    User,
    normalise_username,
)
from bluebubbles.server.repositories.mapping.users import UserMapper
from bluebubbles.server.repositories.sqlalchemy._common import (
    flush_changes,
    require_aware,
)


class SqlAlchemyAuthenticationRepository:
    """Persist authentication metadata through a caller-owned transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_local_identity(
        self, username: str
    ) -> tuple[User, LocalCredential] | None:
        """Return one local user and verifier without plaintext password data."""
        statement = (
            select(UserORM, LocalCredentialORM)
            .join(LocalCredentialORM, LocalCredentialORM.user_id == UserORM.id)
            .where(
                UserORM.normalised_username == normalise_username(username),
                UserORM.authentication_source == "local",
                UserORM.deleted_at.is_(None),
            )
        )
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        user_record, credential_record = row
        return (
            UserMapper.to_domain(user_record),
            LocalCredential(
                id=credential_record.user_id,
                created_at=credential_record.created_at,
                updated_at=credential_record.updated_at,
                user_id=credential_record.user_id,
                password_hash=credential_record.password_hash,
                failed_attempts=credential_record.failed_login_count,
                locked_until=credential_record.locked_until,
            ),
        )

    async def update_local_credential(self, credential: LocalCredential) -> None:
        """Persist a verifier rehash or lockout state without committing."""
        result = await self._session.execute(
            update(LocalCredentialORM)
            .where(LocalCredentialORM.user_id == credential.user_id)
            .values(
                password_hash=credential.password_hash,
                failed_login_count=credential.failed_attempts,
                locked_until=credential.locked_until,
                updated_at=credential.updated_at,
            )
        )
        if result.rowcount != 1:
            raise ValueError("Local credential was not found")

    async def add_login_attempt(
        self,
        *,
        attempt_id: UUID,
        normalised_username: str,
        source_ip: str | None,
        result: str,
        failure_category: str | None,
        attempted_at: datetime,
        correlation_id: UUID,
    ) -> None:
        """Stage password-free attempt metadata for durable throttling evidence."""
        require_aware(attempted_at, "attempted_at")
        self._session.add(
            LoginAttemptORM(
                id=attempt_id,
                normalised_username=normalise_username(normalised_username),
                source_ip=source_ip,
                result=result,
                failure_category=failure_category,
                attempted_at=attempted_at,
                correlation_id=correlation_id,
            )
        )
        await flush_changes(self._session)

    async def count_recent_failures(
        self, *, normalised_username: str, source_ip: str | None, since: datetime
    ) -> tuple[int, int]:
        """Count recent failures independently by username and source address."""
        require_aware(since, "since")
        common = (
            LoginAttemptORM.attempted_at >= since,
            LoginAttemptORM.result == "failed",
        )
        username_count = await self._session.scalar(
            select(func.count())
            .select_from(LoginAttemptORM)
            .where(
                *common,
                LoginAttemptORM.normalised_username
                == normalise_username(normalised_username),
            )
        )
        source_count = 0
        if source_ip is not None:
            source_count = int(
                await self._session.scalar(
                    select(func.count())
                    .select_from(LoginAttemptORM)
                    .where(*common, LoginAttemptORM.source_ip == source_ip)
                )
                or 0
            )
        return int(username_count or 0), source_count

    async def permissions_for_role(self, role_id: UUID) -> frozenset[Permission]:
        """Return recognised stable permissions granted to one role."""
        names = (
            await self._session.scalars(
                select(PermissionORM.name)
                .join(
                    RolePermissionORM,
                    RolePermissionORM.permission_id == PermissionORM.id,
                )
                .where(RolePermissionORM.role_id == role_id)
            )
        ).all()
        return frozenset(Permission(name) for name in names)

    async def role_name(self, role_id: UUID) -> str | None:
        """Return the display name of one role for a safe profile response."""
        value = await self._session.scalar(
            select(RoleORM.name).where(RoleORM.id == role_id)
        )
        return str(value) if value is not None else None
