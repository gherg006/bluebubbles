"""Application authentication workflow and safe result construction."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from pydantic import SecretStr

from bluebubbles.server.authentication.directory_sync import (
    DirectorySynchronisationService,
)
from bluebubbles.server.authentication.providers import (
    AuthenticationProvider,
    LoginCredentials,
)
from bluebubbles.server.configuration.settings import (
    AuthenticationSettings,
    DirectorySettings,
)
from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.audit import AuditSeverity
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import User, normalise_username
from bluebubbles.server.services.audit import AuthenticationAuditWriter
from bluebubbles.server.services.login_attempts import LoginAttemptService
from bluebubbles.server.services.sessions import (
    DeviceDescriptor,
    SessionService,
    SessionTokenPair,
)
from bluebubbles.shared.errors.exceptions import (
    AccountDisabledError,
    AuthenticationError,
    DirectoryUnavailableError,
    InvalidCredentialsError,
)
from bluebubbles.shared.models.sessions import LoginRequest


@dataclass(frozen=True, slots=True)
class LoginContext:
    """Carry request metadata that must never be accepted from the login body."""

    source_ip: str | None
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class AuthenticationResult:
    """Contain one committed identity, session, and permission snapshot."""

    user: User
    role_name: str
    permissions: tuple[str, ...]
    tokens: SessionTokenPair


class AuthenticationService:
    """Coordinate provider verification, user sync, audit, and session creation."""

    def __init__(
        self,
        provider: AuthenticationProvider,
        unit_of_work_factory: UnitOfWorkFactory,
        session_service: SessionService,
        login_attempt_service: LoginAttemptService,
        directory_sync: DirectorySynchronisationService,
        audit_writer: AuthenticationAuditWriter,
        authentication_settings: AuthenticationSettings,
        directory_settings: DirectorySettings,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._provider = provider
        self._unit_of_work_factory = unit_of_work_factory
        self._sessions = session_service
        self._attempts = login_attempt_service
        self._directory_sync = directory_sync
        self._audit = audit_writer
        self._authentication = authentication_settings
        self._directory = directory_settings
        self._clock = clock or (lambda: datetime.now(UTC))

    async def login(
        self, request: LoginRequest, context: LoginContext
    ) -> AuthenticationResult:
        """Authenticate and commit user, session, attempt, and audit atomically.

        Credential failures are recorded in their own transaction because no business
        transaction exists. Passwords and raw tokens never enter persistence or audit.
        """
        username = self.normalise_login_username(request.username)
        await self._attempts.require_allowed(username, context.source_ip)
        credentials = LoginCredentials(
            username, SecretStr(request.password.get_secret_value())
        )
        try:
            timeout = float(
                self._directory.connection_timeout_seconds
                + self._directory.search_timeout_seconds
            )
            identity = await asyncio.wait_for(
                self._provider.authenticate(credentials), timeout=timeout
            )
        except TimeoutError as error:
            await self._attempts.record_failure(
                username,
                context.source_ip,
                context.correlation_id,
                "directory_unavailable",
            )
            raise DirectoryUnavailableError() from error
        except AuthenticationError as error:
            await self._attempts.record_failure(
                username,
                context.source_ip,
                context.correlation_id,
                error.code.value,
            )
            raise
        if not identity.is_enabled:
            await self._attempts.record_failure(
                username, context.source_ip, context.correlation_id, "account_disabled"
            )
            raise AccountDisabledError()
        now = self._clock()
        async with self._unit_of_work_factory() as unit_of_work:
            user, role_name = await self._directory_sync.synchronise_user(
                unit_of_work, identity, now
            )
            if not user.is_enabled:
                raise InvalidCredentialsError()
            device = DeviceDescriptor(
                device_id=request.device_id or context.correlation_id,
                device_name=request.device_name,
                client_version=request.client_version,
            )
            tokens = await self._sessions.issue_in_transaction(
                unit_of_work, user, device, context.source_ip
            )
            permissions = await unit_of_work.authentication.permissions_for_role(
                user.role_id
            )
            await self._attempts.record(
                unit_of_work,
                username=username,
                source_ip=context.source_ip,
                correlation_id=context.correlation_id,
                result="success",
                failure_category=None,
            )
            await self._audit.append(
                unit_of_work.audit,
                event_type="authentication.login_succeeded",
                occurred_at=now,
                actor_id=user.id,
                source_ip=context.source_ip,
                severity=AuditSeverity.INFORMATIONAL,
                details={
                    "session_id": str(tokens.session.id),
                    "device_id": str(device.device_id),
                },
            )
            await unit_of_work.commit()
        return AuthenticationResult(
            user=user,
            role_name=role_name,
            permissions=tuple(sorted(permission.value for permission in permissions)),
            tokens=tokens,
        )

    async def validate_current_user(self, access_token: str) -> AuthenticatedUser:
        """Validate both the signed token and authoritative server-side session."""
        return await self._sessions.authenticate_access_token(access_token)

    async def get_profile(self, authenticated: AuthenticatedUser) -> tuple[User, str]:
        """Return the current enabled user and safe role name for `/auth/me`."""
        async with self._unit_of_work_factory() as unit_of_work:
            user = await unit_of_work.users.get_by_id(authenticated.user_id)
            if user is None or not user.is_enabled:
                raise InvalidCredentialsError()
            role_name = await unit_of_work.authentication.role_name(user.role_id)
        if role_name is None:
            raise InvalidCredentialsError()
        return user, role_name

    def normalise_login_username(self, value: str) -> str:
        """Canonicalise configured domain and UPN forms without touching passwords."""
        selected = value.strip()
        if "\\" in selected:
            prefix, selected = selected.split("\\", 1)
            configured = self._authentication.username_domain_prefix
            if configured is not None and prefix.casefold() != configured.casefold():
                raise InvalidCredentialsError()
        if "@" in selected:
            selected, suffix = selected.rsplit("@", 1)
            configured_suffix = self._authentication.username_upn_suffix
            if (
                configured_suffix is not None
                and suffix.casefold() != configured_suffix.casefold()
            ):
                raise InvalidCredentialsError()
        return normalise_username(selected)
