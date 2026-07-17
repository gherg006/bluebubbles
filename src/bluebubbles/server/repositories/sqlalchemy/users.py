"""Async SQLAlchemy user repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.identity import UserORM
from bluebubbles.server.domain.users import User, normalise_username
from bluebubbles.server.repositories.mapping.users import UserMapper
from bluebubbles.server.repositories.sqlalchemy._common import (
    flush_changes,
    require_aware,
)
from bluebubbles.server.repositories.types import (
    CursorPage,
    UserSearchQuery,
    decode_cursor,
    encode_cursor,
)
from bluebubbles.shared.errors.exceptions import ConflictError


class SqlAlchemyUserRepository:
    """Persist users through one caller-owned asynchronous session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, user_id: UUID, *, for_update: bool = False
    ) -> User | None:
        """Return one active user, optionally row-locked for a short transaction."""
        statement = select(UserORM).where(
            UserORM.id == user_id, UserORM.deleted_at.is_(None)
        )
        if for_update:
            statement = statement.with_for_update()
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return UserMapper.to_domain(record) if record is not None else None

    async def get_by_normalised_username(self, username: str) -> User | None:
        """Return an active user by canonical case-insensitive username."""
        statement = select(UserORM).where(
            UserORM.normalised_username == normalise_username(username),
            UserORM.deleted_at.is_(None),
        )
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return UserMapper.to_domain(record) if record is not None else None

    async def get_by_directory_guid(self, directory_guid: UUID) -> User | None:
        """Return an active directory-backed user by stable directory identity."""
        statement = select(UserORM).where(
            UserORM.directory_guid == str(directory_guid),
            UserORM.deleted_at.is_(None),
        )
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return UserMapper.to_domain(record) if record is not None else None

    async def search(self, query: UserSearchQuery) -> CursorPage[User]:
        """Search users with deterministic username/UUID cursor ordering."""
        statement = select(UserORM)
        if not query.include_deleted:
            statement = statement.where(UserORM.deleted_at.is_(None))
        term = query.term.strip()
        if term:
            pattern = f"%{term.casefold()}%"
            statement = statement.where(
                or_(
                    UserORM.normalised_username.ilike(pattern),
                    UserORM.display_name.ilike(pattern),
                    UserORM.email.ilike(pattern),
                )
            )
        if query.cursor is not None:
            username_value, id_value = decode_cursor(query.cursor, 2)
            if not isinstance(username_value, str) or not isinstance(id_value, str):
                raise ValueError("Invalid user search cursor")
            cursor_id = UUID(id_value)
            statement = statement.where(
                or_(
                    UserORM.normalised_username > username_value,
                    and_(
                        UserORM.normalised_username == username_value,
                        UserORM.id > cursor_id,
                    ),
                )
            )
        statement = statement.order_by(UserORM.normalised_username, UserORM.id).limit(
            query.limit + 1
        )
        records = list((await self._session.scalars(statement)).all())
        has_more = len(records) > query.limit
        selected = records[: query.limit]
        next_cursor = None
        if has_more and selected:
            last = selected[-1]
            next_cursor = encode_cursor(last.normalised_username, last.id)
        return CursorPage(
            items=tuple(UserMapper.to_domain(record) for record in selected),
            next_cursor=next_cursor,
        )

    async def create(self, user: User) -> User:
        """Stage and flush a new user without committing the caller transaction."""
        self._session.add(UserMapper.to_orm(user))
        await flush_changes(self._session)
        return user

    async def update(self, user: User, *, expected_version: int | None = None) -> User:
        """Persist safe mutable fields using optional optimistic concurrency."""
        expected = (
            expected_version if expected_version is not None else user.version - 1
        )
        statement = (
            update(UserORM)
            .where(
                UserORM.id == user.id,
                UserORM.deleted_at.is_(None),
                UserORM.version == expected,
            )
            .values(
                username=user.username,
                normalised_username=user.username,
                display_name=user.display_name,
                email=user.email,
                department=user.department,
                job_title=user.job_title,
                role_id=user.role_id,
                directory_guid=(
                    str(user.active_directory_guid)
                    if user.active_directory_guid is not None
                    else None
                ),
                is_enabled=user.is_enabled,
                avatar_reference=user.profile_picture_reference,
                status_message=user.status_message,
                last_login_at=user.last_login,
                updated_at=user.updated_at,
                version=user.version,
            )
        )
        result = await self._session.execute(statement)
        if result.rowcount != 1:
            raise ConflictError(
                user_message="The user changed before the update could be saved."
            )
        return user

    async def update_profile(self, user: User, *, expected_version: int) -> User:
        """Persist a previously validated domain profile update."""
        return await self.update(user, expected_version=expected_version)

    async def set_enabled(
        self, user_id: UUID, enabled: bool, *, expected_version: int
    ) -> bool:
        """Set login eligibility with optimistic concurrency."""
        result = await self._session.execute(
            update(UserORM)
            .where(
                UserORM.id == user_id,
                UserORM.deleted_at.is_(None),
                UserORM.version == expected_version,
            )
            .values(is_enabled=enabled, version=expected_version + 1)
        )
        return result.rowcount == 1

    async def set_role(
        self, user_id: UUID, role_id: UUID, *, expected_version: int
    ) -> bool:
        """Persist a service-authorized role assignment."""
        result = await self._session.execute(
            update(UserORM)
            .where(
                UserORM.id == user_id,
                UserORM.deleted_at.is_(None),
                UserORM.version == expected_version,
            )
            .values(role_id=role_id, version=expected_version + 1)
        )
        return result.rowcount == 1

    async def soft_delete(
        self, user_id: UUID, deleted_at: datetime, *, expected_version: int
    ) -> bool:
        """Soft-delete one user while retaining shared historical records."""
        require_aware(deleted_at, "deleted_at")
        result = await self._session.execute(
            update(UserORM)
            .where(
                UserORM.id == user_id,
                UserORM.deleted_at.is_(None),
                UserORM.version == expected_version,
            )
            .values(
                deleted_at=deleted_at,
                updated_at=deleted_at,
                is_enabled=False,
                version=expected_version + 1,
            )
        )
        return result.rowcount == 1
