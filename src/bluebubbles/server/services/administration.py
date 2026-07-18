"""Authoritative user, session, connection, and capability administration."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from bluebubbles.server.database.unit_of_work import UnitOfWork, UnitOfWorkFactory
from bluebubbles.server.domain.audit import AuditSeverity
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission, Role, User
from bluebubbles.server.repositories.types import UserSearchQuery
from bluebubbles.server.services.audit import AuditWriter
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.server.websocket.manager import WebSocketConnectionManager
from bluebubbles.shared.errors.exceptions import (
    AuthorisationError,
    ConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from bluebubbles.shared.models.administration import (
    AdminConnectionResponse,
    AdministrativeCapabilities,
    AdminUserPageResponse,
    AdminUserSummary,
    ConnectionListResponse,
    SessionRevocationResult,
    UserAdministrationResult,
)
from bluebubbles.shared.models.pagination import CursorPageMetadata, OpaqueCursor
from bluebubbles.shared.models.sessions import SessionSummary


def _reason(value: str) -> str:
    reason = value.strip()
    if not reason or len(reason) > 1000:
        raise ValidationError(
            user_message="A reason between 1 and 1000 characters is required."
        )
    return reason


class RoleAdministrationPolicy:
    """Validate fixed-role and self-lockout boundaries without database access."""

    def can_assign_role(
        self, requester_role: Role, target_role: Role, proposed_role: Role
    ) -> bool:
        """Allow only named assignment grants and prevent upward role escalation."""
        del target_role
        required = (
            Permission.USER_ASSIGN_SUPER_ROLE
            if proposed_role.name == "SuperAdministrator"
            else Permission.USER_ASSIGN_ROLE
        )
        return required in requester_role.permissions

    def can_disable_user(
        self,
        requester: User,
        target: User,
        target_role: Role,
        active_super_admin_count: int,
    ) -> bool:
        """Prevent self-disable and removal of the final enabled super administrator."""
        if requester.id == target.id or not target.is_enabled:
            return False
        return not (
            target_role.name == "SuperAdministrator" and active_super_admin_count <= 1
        )

    def can_revoke_session(self, requester_role: Role, target_role: Role) -> bool:
        """Prevent delegated support roles revoking a higher protected role."""
        if Permission.SESSION_REVOKE not in requester_role.permissions:
            return False
        if target_role.name == "SuperAdministrator":
            return Permission.USER_ASSIGN_SUPER_ROLE in requester_role.permissions
        return True


class AdminService:
    """Build the non-authoritative client capability response from live permissions."""

    @staticmethod
    def capabilities(requester: AuthenticatedUser) -> AdministrativeCapabilities:
        permissions = requester.permissions

        def has(*items: Permission) -> bool:
            return any(item.value in permissions for item in items)

        can_open = has(
            Permission.ADMIN_DASHBOARD,
            Permission.USER_VIEW,
            Permission.AUDIT_VIEW,
            Permission.AUDIT_VIEW_LIMITED,
        )
        return AdministrativeCapabilities(
            can_open_admin=can_open,
            can_view_dashboard=has(Permission.ADMIN_DASHBOARD),
            can_manage_users=has(
                Permission.USER_ENABLE,
                Permission.USER_DISABLE,
                Permission.USER_ASSIGN_ROLE,
            ),
            can_manage_sessions=has(Permission.SESSION_VIEW, Permission.SESSION_REVOKE),
            can_view_connections=has(Permission.CONNECTION_VIEW),
            can_view_audit=has(Permission.AUDIT_VIEW, Permission.AUDIT_VIEW_LIMITED),
            can_export_audit=has(Permission.AUDIT_EXPORT),
            can_manage_alerts=has(
                Permission.ALERT_ACKNOWLEDGE, Permission.ALERT_RESOLVE
            ),
            can_manage_announcements=has(Permission.ANNOUNCEMENT_MANAGE),
            can_view_health=has(Permission.HEALTH_VIEW_DETAILED),
            can_run_workers=has(Permission.WORKER_RUN),
            can_modify_configuration=has(Permission.CONFIGURATION_MODIFY),
            can_control_maintenance=has(Permission.SYSTEM_MAINTENANCE),
        )


class UserAdministrationService:
    """Coordinate locked account changes, sessions, audit, commit, then disconnect."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        role_policy: RoleAdministrationPolicy,
        connection_manager: WebSocketConnectionManager,
        audit_writer: AuditWriter | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._uow_factory = unit_of_work_factory
        self._permissions = permission_service
        self._policy = role_policy
        self._connections = connection_manager
        self._audit = audit_writer or AuditWriter()
        self._clock = clock

    async def search_users(
        self,
        requester: AuthenticatedUser,
        *,
        term: str = "",
        limit: int = 50,
        cursor: str | None = None,
    ) -> AdminUserPageResponse:
        """Return a bounded account search without logging the raw search term."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.USER_SEARCH
        )
        async with self._uow_factory() as uow:
            page = await uow.users.search(
                UserSearchQuery(term=term, limit=limit, cursor=cursor)
            )
            summaries = tuple([await self._summary(uow, user) for user in page.items])
        return AdminUserPageResponse(
            users=summaries,
            page=CursorPageMetadata(
                next_cursor=(
                    OpaqueCursor(page.next_cursor) if page.next_cursor else None
                ),
                has_more=page.next_cursor is not None,
            ),
        )

    async def disable_user(
        self,
        requester: AuthenticatedUser,
        user_id: UUID,
        *,
        expected_version: int,
        reason: str,
    ) -> UserAdministrationResult:
        """Disable an eligible user and revoke sessions in one audit-backed commit."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.USER_DISABLE
        )
        reason = _reason(reason)
        now = self._clock()
        async with self._uow_factory() as uow:
            actor = await uow.users.get_by_id(requester.user_id)
            target = await uow.users.get_by_id(user_id, for_update=True)
            if actor is None or target is None:
                raise ResourceNotFoundError()
            target_role = await uow.authentication.get_role(target.role_id)
            if target_role is None:
                raise ResourceNotFoundError()
            count = await uow.authentication.count_enabled_users_with_role(
                target.role_id
            )
            if not self._policy.can_disable_user(actor, target, target_role, count):
                raise AuthorisationError(
                    user_message="This account cannot be disabled."
                )
            if target.version != expected_version:
                raise ConflictError(
                    user_message="The user changed before this action was saved."
                )
            changed = await uow.users.set_enabled(
                user_id, False, expected_version=expected_version
            )
            if not changed:
                raise ConflictError(
                    user_message="The user changed before this action was saved."
                )
            invalidated = await uow.sessions.invalidate_all_for_user(
                user_id, now, reason
            )
            event = await self._audit.append(
                uow.audit,
                event_type="user.disabled",
                occurred_at=now,
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.WARNING,
                details={"target_user_id": str(user_id), "reason": reason},
            )
            target.is_enabled = False
            target.version += 1
            target.updated_at = now
            summary = await self._summary(uow, target)
            await uow.commit()
        await self._connections.disconnect_user(user_id, "Account disabled")
        return UserAdministrationResult(
            user=summary,
            invalidated_sessions=invalidated,
            audit_event_id=event.id,
        )

    async def enable_user(
        self,
        requester: AuthenticatedUser,
        user_id: UUID,
        *,
        expected_version: int,
        reason: str,
    ) -> UserAdministrationResult:
        """Enable a disabled local account after an authorised audited commit."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.USER_ENABLE
        )
        reason = _reason(reason)
        now = self._clock()
        async with self._uow_factory() as uow:
            target = await uow.users.get_by_id(user_id, for_update=True)
            if target is None:
                raise ResourceNotFoundError()
            if target.is_enabled:
                raise ConflictError(user_message="The account is already enabled.")
            if target.version != expected_version or not await uow.users.set_enabled(
                user_id, True, expected_version=expected_version
            ):
                raise ConflictError(
                    user_message="The user changed before this action was saved."
                )
            event = await self._audit.append(
                uow.audit,
                event_type="user.enabled",
                occurred_at=now,
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.WARNING,
                details={"target_user_id": str(user_id), "reason": reason},
            )
            target.is_enabled = True
            target.version += 1
            target.updated_at = now
            summary = await self._summary(uow, target)
            await uow.commit()
        return UserAdministrationResult(user=summary, audit_event_id=event.id)

    async def change_role(
        self,
        requester: AuthenticatedUser,
        user_id: UUID,
        proposed_role_id: UUID,
        *,
        expected_version: int,
        reason: str,
    ) -> UserAdministrationResult:
        """Assign an allowed fixed role and invalidate cached session authority."""
        reason = _reason(reason)
        now = self._clock()
        async with self._uow_factory() as uow:
            actor = await uow.users.get_by_id(requester.user_id)
            target = await uow.users.get_by_id(user_id, for_update=True)
            if actor is None or target is None:
                raise ResourceNotFoundError()
            actor_role = await uow.authentication.get_role(actor.role_id)
            current_role = await uow.authentication.get_role(target.role_id)
            proposed_role = await uow.authentication.get_role(proposed_role_id)
            if actor_role is None or current_role is None or proposed_role is None:
                raise ResourceNotFoundError()
            required = (
                Permission.USER_ASSIGN_SUPER_ROLE
                if proposed_role.name == "SuperAdministrator"
                else Permission.USER_ASSIGN_ROLE
            )
            await self._permissions.require_authenticated_permission(
                requester, required
            )
            if not self._policy.can_assign_role(
                actor_role, current_role, proposed_role
            ):
                raise AuthorisationError()
            if (
                current_role.name == "SuperAdministrator"
                and proposed_role.name != "SuperAdministrator"
                and await uow.authentication.count_enabled_users_with_role(
                    current_role.id
                )
                <= 1
            ):
                raise AuthorisationError(
                    user_message="The final SuperAdministrator is protected."
                )
            if target.version != expected_version or not await uow.users.set_role(
                user_id, proposed_role_id, expected_version=expected_version
            ):
                raise ConflictError(
                    user_message="The user changed before this action was saved."
                )
            invalidated = await uow.sessions.invalidate_all_for_user(
                user_id, now, "role_changed"
            )
            event = await self._audit.append(
                uow.audit,
                event_type="user.role_changed",
                occurred_at=now,
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.WARNING,
                details={
                    "target_user_id": str(user_id),
                    "previous_role": current_role.name,
                    "new_role": proposed_role.name,
                    "reason": reason,
                },
            )
            target.role_id = proposed_role_id
            target.version += 1
            target.updated_at = now
            summary = await self._summary(uow, target, proposed_role.name)
            await uow.commit()
        await self._connections.disconnect_user(user_id, "Permissions changed")
        return UserAdministrationResult(
            user=summary,
            invalidated_sessions=invalidated,
            audit_event_id=event.id,
        )

    @staticmethod
    async def _summary(
        uow: UnitOfWork, user: User, role_name: str | None = None
    ) -> AdminUserSummary:
        role = role_name or await uow.authentication.role_name(user.role_id)
        sessions = await uow.sessions.list_active_for_user(user.id)
        return AdminUserSummary(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            role=role or "Unknown",
            department=user.department,
            is_enabled=user.is_enabled,
            active_sessions=len(sessions),
            last_login=user.last_login,
            version=user.version,
        )


class SessionAdministrationService:
    """Revoke another user's session durably before disconnecting its sockets."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        role_policy: RoleAdministrationPolicy,
        connection_manager: WebSocketConnectionManager,
        audit_writer: AuditWriter | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._uow_factory = unit_of_work_factory
        self._permissions = permission_service
        self._policy = role_policy
        self._connections = connection_manager
        self._audit = audit_writer or AuditWriter()
        self._clock = clock

    async def list_sessions(
        self, requester: AuthenticatedUser, user_id: UUID
    ) -> tuple[SessionSummary, ...]:
        """Return token-free active sessions after resource-level role policy."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.SESSION_VIEW
        )
        async with self._uow_factory() as uow:
            actor = await uow.users.get_by_id(requester.user_id)
            target = await uow.users.get_by_id(user_id)
            if actor is None or target is None:
                raise ResourceNotFoundError()
            actor_role = await uow.authentication.get_role(actor.role_id)
            target_role = await uow.authentication.get_role(target.role_id)
            if (
                actor_role is None
                or target_role is None
                or not self._policy.can_revoke_session(actor_role, target_role)
            ):
                raise AuthorisationError()
            sessions = await uow.sessions.list_active_for_user(user_id)
        return tuple(
            SessionSummary(
                id=session.id,
                device_name=session.device_name,
                platform=session.platform,
                source_ip=(
                    None if session.ip_address == "unknown" else session.ip_address
                ),
                created_at=session.created_at,
                last_seen_at=session.updated_at,
                expires_at=session.expires_at,
                current=session.id == requester.session_id,
            )
            for session in sessions
        )

    async def revoke_session(
        self, requester: AuthenticatedUser, session_id: UUID, reason: str
    ) -> SessionRevocationResult:
        """Commit one policy-checked revocation, then close matching connections."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.SESSION_REVOKE
        )
        reason = _reason(reason)
        now = self._clock()
        async with self._uow_factory() as uow:
            session = await uow.sessions.get_active(session_id, for_update=True)
            actor = await uow.users.get_by_id(requester.user_id)
            if session is None or actor is None:
                raise ResourceNotFoundError()
            target = await uow.users.get_by_id(session.user_id)
            if target is None:
                raise ResourceNotFoundError()
            actor_role = await uow.authentication.get_role(actor.role_id)
            target_role = await uow.authentication.get_role(target.role_id)
            if (
                actor_role is None
                or target_role is None
                or not self._policy.can_revoke_session(actor_role, target_role)
            ):
                raise AuthorisationError()
            if not await uow.sessions.invalidate(session_id, now, reason):
                raise ConflictError(user_message="The session is already inactive.")
            event = await self._audit.append(
                uow.audit,
                event_type="session.revoked_admin",
                occurred_at=now,
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.WARNING,
                details={
                    "session_id": str(session_id),
                    "target_user_id": str(target.id),
                    "reason": reason,
                },
            )
            await uow.commit()
        disconnected = await self._connections.disconnect_session(
            session_id, "Session revoked"
        )
        return SessionRevocationResult(
            session_id=session_id,
            user_id=target.id,
            invalidated_at=now,
            disconnected_connection_count=disconnected,
            audit_event_id=event.id,
        )


class ConnectionAdministrationService:
    """List and disconnect transient sockets without altering persistent sessions."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        connection_manager: WebSocketConnectionManager,
        audit_writer: AuditWriter | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._uow_factory = unit_of_work_factory
        self._permissions = permission_service
        self._connections = connection_manager
        self._audit = audit_writer or AuditWriter()
        self._clock = clock

    async def list_connections(
        self, requester: AuthenticatedUser
    ) -> ConnectionListResponse:
        """Return safe transient connection metadata to an authorised requester."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.CONNECTION_VIEW
        )
        connections = await self._connections.list_connections()
        return ConnectionListResponse(
            connections=tuple(
                AdminConnectionResponse(
                    connection_id=item.connection_id,
                    user_id=item.user_id,
                    session_id=item.session_id,
                    connected_at=item.connected_at,
                    last_heartbeat_at=item.last_heartbeat,
                )
                for item in connections
            ),
            generated_at=self._clock(),
        )

    async def disconnect_connection(
        self, requester: AuthenticatedUser, connection_id: UUID, reason: str
    ) -> bool:
        """Audit a disconnect decision before closing only the selected socket."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.CONNECTION_DISCONNECT
        )
        reason = _reason(reason)
        connections = await self._connections.list_connections()
        if not any(item.connection_id == connection_id for item in connections):
            raise ResourceNotFoundError()
        async with self._uow_factory() as uow:
            await self._audit.append(
                uow.audit,
                event_type="connection.disconnected_admin",
                occurred_at=self._clock(),
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.WARNING,
                details={"connection_id": str(connection_id), "reason": reason},
            )
            await uow.commit()
        return await self._connections.disconnect_connection(
            connection_id, "Administrative disconnect"
        )
