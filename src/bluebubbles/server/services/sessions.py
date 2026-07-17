"""Server-side session issuance, validation, rotation, and revocation."""

from __future__ import annotations

import hmac
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4

from bluebubbles.server.authentication.tokens import AccessTokenClaims, TokenManager
from bluebubbles.server.configuration.settings import TokenSettings
from bluebubbles.server.database.unit_of_work import UnitOfWork, UnitOfWorkFactory
from bluebubbles.server.domain.audit import AuditSeverity
from bluebubbles.server.domain.sessions import AuthenticatedUser, Session
from bluebubbles.server.domain.users import User
from bluebubbles.server.services.audit import AuthenticationAuditWriter
from bluebubbles.shared.errors.exceptions import (
    AuthorisationError,
    InvalidTokenError,
    RefreshTokenReuseError,
    SessionExpiredError,
)
from bluebubbles.shared.models.sessions import RefreshTokenRequest, SessionSummary


@dataclass(frozen=True, slots=True)
class DeviceDescriptor:
    """Describe a client installation without hardware fingerprinting."""

    device_id: UUID
    device_name: str
    client_version: str


@dataclass(frozen=True, slots=True)
class SessionTokenPair:
    """Return raw token material once alongside its persisted session."""

    session: Session
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime


class SessionRevocationNotifier(Protocol):
    """Disconnect sockets after committed revocation without owning sessions."""

    async def session_revoked(self, session_id: UUID) -> None: ...

    async def user_sessions_revoked(self, user_id: UUID) -> None: ...


class SessionService:
    """Manage rotating, server-revocable sessions through short transactions."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        token_manager: TokenManager,
        token_settings: TokenSettings,
        audit_writer: AuthenticationAuditWriter,
        *,
        notifier: SessionRevocationNotifier | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._token_manager = token_manager
        self._settings = token_settings
        self._audit = audit_writer
        self._notifier = notifier
        self._clock = clock or (lambda: datetime.now(UTC))

    async def issue_in_transaction(
        self,
        unit_of_work: UnitOfWork,
        user: User,
        device: DeviceDescriptor,
        source_ip: str | None,
    ) -> SessionTokenPair:
        """Stage a hashed session in a caller-owned uncommitted transaction."""
        now = self._clock()
        refresh_token = self._token_manager.create_refresh_token()
        access_expires = now + timedelta(
            seconds=self._settings.access_token_lifetime_seconds
        )
        refresh_expires = now + timedelta(
            seconds=self._settings.refresh_token_lifetime_seconds
        )
        session = Session(
            id=uuid4(),
            created_at=now,
            updated_at=now,
            user_id=user.id,
            refresh_token_hash=self._token_manager.hash_refresh_token(
                refresh_token
            ).hex(),
            expires_at=refresh_expires,
            idle_expires_at=access_expires,
            ip_address=source_ip or "unknown",
            device_name=device.device_name,
            platform=device.client_version,
            login_time=now,
            device_id=device.device_id,
        )
        await unit_of_work.sessions.create(session)
        return SessionTokenPair(
            session=session,
            access_token=self._token_manager.create_access_token(user, session),
            refresh_token=refresh_token,
            access_expires_at=access_expires,
            refresh_expires_at=refresh_expires,
        )

    async def refresh(self, request: RefreshTokenRequest) -> SessionTokenPair:
        """Rotate one refresh token atomically and detect immediate token reuse."""
        submitted = self._token_manager.hash_refresh_token(
            request.refresh_token.get_secret_value()
        )
        compromised_user: UUID | None = None
        async with self._unit_of_work_factory() as unit_of_work:
            session = await unit_of_work.sessions.get_active_by_id(
                request.session_id, for_update=True
            )
            if session is None or not session.can_refresh(self._clock()):
                raise SessionExpiredError()
            current = bytes.fromhex(session.refresh_token_hash)
            previous = (
                bytes.fromhex(session.previous_refresh_token_hash)
                if session.previous_refresh_token_hash is not None
                else None
            )
            if not hmac.compare_digest(submitted, current):
                if previous is not None and hmac.compare_digest(submitted, previous):
                    await unit_of_work.sessions.invalidate(
                        session.id, self._clock(), "refresh_token_reuse"
                    )
                    await self._audit.append(
                        unit_of_work.audit,
                        event_type="session.refresh_token_reuse",
                        occurred_at=self._clock(),
                        actor_id=session.user_id,
                        source_ip=session.ip_address,
                        severity=AuditSeverity.CRITICAL,
                        details={"session_id": str(session.id)},
                    )
                    await unit_of_work.commit()
                    compromised_user = session.user_id
                else:
                    raise InvalidTokenError()
            if compromised_user is None:
                user = await unit_of_work.users.get_by_id(session.user_id)
                if user is None or not user.is_enabled:
                    raise SessionExpiredError()
                refresh_token = self._token_manager.create_refresh_token()
                new_hash = self._token_manager.hash_refresh_token(refresh_token)
                now = self._clock()
                next_version = session.version + 1
                access_expires_at = min(
                    now
                    + timedelta(seconds=self._settings.access_token_lifetime_seconds),
                    session.expires_at,
                )
                rotated = await unit_of_work.sessions.rotate_refresh_token(
                    session.id,
                    new_hash,
                    next_version,
                    now,
                    access_expires_at,
                )
                if not rotated:
                    raise InvalidTokenError()
                session.previous_refresh_token_hash = session.refresh_token_hash
                session.refresh_token_hash = new_hash.hex()
                session.version = next_version
                session.updated_at = now
                session.idle_expires_at = access_expires_at
                await unit_of_work.commit()
                return SessionTokenPair(
                    session=session,
                    access_token=self._token_manager.create_access_token(user, session),
                    refresh_token=refresh_token,
                    access_expires_at=session.idle_expires_at,
                    refresh_expires_at=session.expires_at,
                )
        assert compromised_user is not None
        if self._notifier is not None:
            await self._notifier.session_revoked(request.session_id)
        raise RefreshTokenReuseError()

    async def authenticate_access_token(self, token: str) -> AuthenticatedUser:
        """Require valid claims, active matching session, and enabled user state."""
        claims: AccessTokenClaims = self._token_manager.decode_access_token(token)
        async with self._unit_of_work_factory() as unit_of_work:
            session = await unit_of_work.sessions.get_active_by_id(claims.session_id)
            if session is None or session.user_id != claims.user_id:
                raise SessionExpiredError()
            if session.version != claims.token_version:
                raise InvalidTokenError()
            user = await unit_of_work.users.get_by_id(claims.user_id)
            if user is None or not user.is_enabled:
                raise SessionExpiredError()
            permissions = await unit_of_work.authentication.permissions_for_role(
                user.role_id
            )
            return AuthenticatedUser(
                user_id=user.id,
                session_id=session.id,
                username=user.username,
                role_id=user.role_id,
                permissions=frozenset(item.value for item in permissions),
            )

    async def invalidate(
        self,
        requester: AuthenticatedUser,
        session_id: UUID,
        reason: str,
    ) -> None:
        """Revoke an owned session or one covered by user-management authority."""
        async with self._unit_of_work_factory() as unit_of_work:
            session = await unit_of_work.sessions.get_by_id(session_id)
            if session is None:
                return
            if (
                session.user_id != requester.user_id
                and "manage_users" not in requester.permissions
            ):
                raise AuthorisationError()
            changed = await unit_of_work.sessions.invalidate(
                session_id, self._clock(), reason
            )
            if changed:
                await self._audit.append(
                    unit_of_work.audit,
                    event_type="session.revoked",
                    occurred_at=self._clock(),
                    actor_id=requester.user_id,
                    source_ip=session.ip_address,
                    severity=AuditSeverity.WARNING,
                    details={"session_id": str(session_id), "reason": reason},
                )
            await unit_of_work.commit()
        if self._notifier is not None:
            await self._notifier.session_revoked(session_id)

    async def invalidate_all_for_user(self, user_id: UUID, reason: str) -> int:
        """Revoke all active sessions and notify sockets only after commit."""
        async with self._unit_of_work_factory() as unit_of_work:
            count = await unit_of_work.sessions.invalidate_all_for_user(
                user_id, self._clock(), reason
            )
            await unit_of_work.commit()
        if count and self._notifier is not None:
            await self._notifier.user_sessions_revoked(user_id)
        return count

    async def list_for_user(
        self, user: AuthenticatedUser
    ) -> tuple[SessionSummary, ...]:
        """Return token-free active-session summaries for the authenticated owner."""
        async with self._unit_of_work_factory() as unit_of_work:
            sessions = await unit_of_work.sessions.list_active_for_user(user.user_id)
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
                current=session.id == user.session_id,
            )
            for session in sessions
        )
