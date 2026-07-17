"""Identity, role, permission, and local-credential persistence mappings."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from bluebubbles.server.database.base import (
    Base,
    CreatedAtMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VersionMixin,
)


class RoleORM(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Map an application role and its privilege-comparison priority."""

    __tablename__ = "roles"
    __table_args__ = (CheckConstraint("priority >= 0", name="priority_non_negative"),)

    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    is_system_role: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )


class PermissionORM(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """Map one stable application permission name."""

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)


class RolePermissionORM(Base, CreatedAtMixin):
    """Map the many-to-many grant between roles and permissions."""

    __tablename__ = "role_permissions"

    role_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    permission_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("permissions.id", ondelete="RESTRICT"),
        primary_key=True,
    )


class UserORM(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    """Map authoritative local and directory-backed user metadata."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint(
            "authentication_source IN ('local', 'directory')",
            name="authentication_source_valid",
        ),
        CheckConstraint(
            "directory_state IN ('active', 'disabled', 'missing', 'local')",
            name="directory_state_valid",
        ),
        Index(
            "uq_users_directory_guid",
            "directory_guid",
            unique=True,
            postgresql_where=text("directory_guid IS NOT NULL"),
        ),
        Index("ix_users_email", "email"),
        Index("ix_users_department", "department"),
        Index("ix_users_role_id", "role_id"),
    )

    username: Mapped[str] = mapped_column(String(150), nullable=False)
    normalised_username: Mapped[str] = mapped_column(
        String(150), nullable=False, unique=True
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    department: Mapped[str | None] = mapped_column(String(200))
    job_title: Mapped[str | None] = mapped_column(String(200))
    directory_guid: Mapped[str | None] = mapped_column(String(200))
    distinguished_name: Mapped[str | None] = mapped_column(String(1000))
    authentication_source: Mapped[str] = mapped_column(String(30), nullable=False)
    role_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    directory_state: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active", server_default="active"
    )
    avatar_reference: Mapped[str | None] = mapped_column(String(500))
    status_message: Mapped[str | None] = mapped_column(String(500))
    last_directory_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LocalCredentialORM(Base, TimestampMixin):
    """Map an Argon2id password verifier for a deliberately local account."""

    __tablename__ = "local_credentials"
    __table_args__ = (
        CheckConstraint("failed_login_count >= 0", name="failed_logins_non_negative"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    failed_login_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
