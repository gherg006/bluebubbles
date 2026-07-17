"""Pure user ORM/domain conversions."""

from uuid import UUID

from bluebubbles.server.database.models.identity import UserORM
from bluebubbles.server.domain.users import User
from bluebubbles.shared.models.users import PresenceState


class UserMapper:
    """Convert user records without querying or applying authorization."""

    @staticmethod
    def to_domain(record: UserORM) -> User:
        """Return a detached domain user from one ORM row."""
        directory_guid = UUID(record.directory_guid) if record.directory_guid else None
        return User(
            id=record.id,
            created_at=record.created_at,
            updated_at=record.updated_at,
            deleted_at=record.deleted_at,
            version=record.version,
            username=record.normalised_username,
            display_name=record.display_name,
            role_id=record.role_id,
            email=record.email,
            department=record.department,
            job_title=record.job_title,
            active_directory_guid=directory_guid,
            profile_picture_reference=record.avatar_reference,
            status_message=record.status_message,
            presence=PresenceState.OFFLINE,
            is_enabled=record.is_enabled,
            last_login=record.last_login_at,
        )

    @staticmethod
    def to_orm(user: User) -> UserORM:
        """Return a new ORM row containing safe persistent user fields."""
        is_directory = user.active_directory_guid is not None
        return UserORM(
            id=user.id,
            created_at=user.created_at,
            updated_at=user.updated_at,
            deleted_at=user.deleted_at,
            version=user.version,
            username=user.username,
            normalised_username=user.username,
            display_name=user.display_name,
            email=user.email,
            department=user.department,
            job_title=user.job_title,
            directory_guid=(
                str(user.active_directory_guid)
                if user.active_directory_guid is not None
                else None
            ),
            distinguished_name=None,
            authentication_source="directory" if is_directory else "local",
            role_id=user.role_id,
            is_enabled=user.is_enabled,
            directory_state="active" if is_directory else "local",
            avatar_reference=user.profile_picture_reference,
            status_message=user.status_message,
            last_directory_sync_at=None,
            last_login_at=user.last_login,
            last_seen_at=None,
        )
