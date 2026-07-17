"""Timeout-bounded LDAP/Active Directory authentication adapter."""

from __future__ import annotations

import asyncio
import ssl
import time
from collections.abc import Callable
from typing import Protocol, cast

from ldap3 import ALL, AUTO_BIND_TLS_BEFORE_BIND, Connection, Server, Tls
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars

from bluebubbles.server.authentication.providers import (
    AuthenticatedDirectoryIdentity,
    DirectoryUser,
    LoginCredentials,
)
from bluebubbles.server.configuration.settings import DirectorySettings
from bluebubbles.shared.errors.exceptions import (
    AccountDisabledError,
    DirectoryUnavailableError,
    InvalidCredentialsError,
)
from bluebubbles.shared.models.health import ComponentHealth, HealthState


class LDAPConnectionFactory(Protocol):
    """Construct ldap3 connections so tests never require a live directory."""

    def service_connection(self) -> Connection: ...

    def user_connection(self, distinguished_name: str, password: str) -> Connection: ...


class DefaultLDAPConnectionFactory:
    """Create certificate-validating LDAPS connections from protected settings."""

    def __init__(self, settings: DirectorySettings) -> None:
        self._settings = settings
        assert settings.server is not None and settings.port is not None
        self._server = Server(
            settings.server,
            port=settings.port,
            use_ssl=settings.use_tls,
            connect_timeout=settings.connection_timeout_seconds,
            get_info=ALL,
            tls=Tls(validate=ssl.CERT_REQUIRED),
        )

    def service_connection(self) -> Connection:
        """Return a service-account connection used only for directory reads."""
        assert self._settings.bind_dn is not None
        assert self._settings.bind_password is not None
        return Connection(
            self._server,
            user=self._settings.bind_dn,
            password=self._settings.bind_password.get_secret_value(),
            receive_timeout=self._settings.search_timeout_seconds,
            auto_bind=(True if self._settings.use_tls else AUTO_BIND_TLS_BEFORE_BIND),
            raise_exceptions=True,
        )

    def user_connection(self, distinguished_name: str, password: str) -> Connection:
        """Return a short-lived connection used only for the credential bind."""
        return Connection(
            self._server,
            user=distinguished_name,
            password=password,
            receive_timeout=self._settings.search_timeout_seconds,
            auto_bind=(True if self._settings.use_tls else AUTO_BIND_TLS_BEFORE_BIND),
            raise_exceptions=True,
        )


class LDAPAuthenticationProvider:
    """Authenticate through escaped searches and a separate end-user LDAP bind."""

    def __init__(
        self,
        settings: DirectorySettings,
        connection_factory: LDAPConnectionFactory | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._settings = settings
        self._connections = connection_factory or DefaultLDAPConnectionFactory(settings)
        self._clock = clock or time.perf_counter

    async def authenticate(
        self, credentials: LoginCredentials
    ) -> AuthenticatedDirectoryIdentity:
        """Search safely, reject disabled accounts, then bind as the user."""
        try:
            identity = await asyncio.wait_for(
                asyncio.to_thread(self._lookup_sync, credentials.username),
                timeout=self._settings.search_timeout_seconds,
            )
            if identity is None:
                raise InvalidCredentialsError()
            if not identity.is_enabled:
                raise AccountDisabledError()
            await asyncio.wait_for(
                asyncio.to_thread(
                    self._bind_sync,
                    identity.distinguished_name or "",
                    credentials.password.get_secret_value(),
                ),
                timeout=self._settings.connection_timeout_seconds,
            )
            return identity
        except (InvalidCredentialsError, AccountDisabledError):
            raise
        except (TimeoutError, LDAPException, OSError) as error:
            raise DirectoryUnavailableError() from error

    async def get_user_by_identifier(self, identifier: str) -> DirectoryUser | None:
        """Read one directory identity through the service account."""
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._lookup_sync, identifier),
                timeout=self._settings.search_timeout_seconds,
            )
        except (TimeoutError, LDAPException, OSError) as error:
            raise DirectoryUnavailableError() from error

    async def check_health(self) -> ComponentHealth:
        """Perform a bounded bind and return no directory topology details."""
        started = self._clock()
        try:
            await asyncio.wait_for(
                asyncio.to_thread(self._health_sync),
                timeout=self._settings.connection_timeout_seconds,
            )
        except (TimeoutError, LDAPException, OSError):
            return ComponentHealth(
                name="authentication_directory", state=HealthState.UNHEALTHY
            )
        return ComponentHealth(
            name="authentication_directory",
            state=HealthState.HEALTHY,
            latency_ms=max(0.0, (self._clock() - started) * 1000),
        )

    def _lookup_sync(self, identifier: str) -> DirectoryUser | None:
        connection = self._connections.service_connection()
        try:
            search_base = self._settings.user_search_base or self._settings.base_dn
            assert search_base is not None
            found = connection.search(
                search_base,
                self._build_user_search_filter(identifier),
                attributes=[
                    self._settings.username_attribute,
                    "displayName",
                    self._settings.email_attribute,
                    self._settings.department_attribute,
                    self._settings.job_title_attribute,
                    self._settings.guid_attribute,
                    self._settings.group_membership_attribute,
                    "userAccountControl",
                ],
                size_limit=1,
                time_limit=self._settings.search_timeout_seconds,
            )
            if not found or not connection.entries:
                return None
            entry = connection.entries[0]
            attributes = cast(dict[str, object], entry.entry_attributes_as_dict)
            account_control = self._first(attributes.get("userAccountControl"), 0)
            return DirectoryUser(
                username=str(
                    self._first(
                        attributes.get(self._settings.username_attribute), identifier
                    )
                ).casefold(),
                display_name=str(
                    self._first(attributes.get("displayName"), identifier)
                ),
                email=self._optional(attributes.get(self._settings.email_attribute)),
                department=self._optional(
                    attributes.get(self._settings.department_attribute)
                ),
                job_title=self._optional(
                    attributes.get(self._settings.job_title_attribute)
                ),
                directory_guid=self._optional(
                    attributes.get(self._settings.guid_attribute)
                ),
                distinguished_name=str(entry.entry_dn),
                groups=tuple(
                    str(value)
                    for value in self._values(
                        attributes.get(self._settings.group_membership_attribute)
                    )
                ),
                is_enabled=(int(str(account_control)) & 2) == 0,
            )
        finally:
            connection.unbind()

    def _bind_sync(self, distinguished_name: str, password: str) -> None:
        if not distinguished_name:
            raise InvalidCredentialsError()
        try:
            connection = self._connections.user_connection(distinguished_name, password)
        except LDAPException as error:
            if "invalidCredentials" in str(error):
                raise InvalidCredentialsError() from error
            raise
        connection.unbind()

    def _health_sync(self) -> None:
        connection = self._connections.service_connection()
        connection.unbind()

    def _build_user_search_filter(self, identifier: str) -> str:
        escaped = escape_filter_chars(identifier)
        return f"({self._settings.username_attribute}={escaped})"

    @staticmethod
    def _values(value: object) -> list[object]:
        if isinstance(value, list | tuple):
            return list(value)
        return [] if value is None else [value]

    @classmethod
    def _first(cls, value: object, default: object) -> object:
        values = cls._values(value)
        return values[0] if values else default

    @classmethod
    def _optional(cls, value: object) -> str | None:
        selected = cls._first(value, None)
        return str(selected) if selected is not None else None
