"""Task 09 service, provider-adapter, and route collaboration tests."""

# mypy: disable-error-code="no-untyped-def,arg-type,no-untyped-call"

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from ldap3.core.exceptions import LDAPException
from pydantic import SecretStr

from bluebubbles.server.application import create_application
from bluebubbles.server.authentication.ldap_provider import LDAPAuthenticationProvider
from bluebubbles.server.authentication.local_provider import LocalAuthenticationProvider
from bluebubbles.server.authentication.password_hashing import (
    PasswordHasher,
    PasswordHashingParameters,
)
from bluebubbles.server.authentication.providers import DirectoryUser, LoginCredentials
from bluebubbles.server.authentication.tokens import TokenManager
from bluebubbles.server.configuration.settings import (
    AuthenticationSettings,
    DirectorySettings,
    ServerSettings,
    TokenSettings,
)
from bluebubbles.server.container import ServerContainer
from bluebubbles.server.database.seed import stable_seed_id
from bluebubbles.server.domain.sessions import AuthenticatedUser, Session
from bluebubbles.server.domain.users import LocalCredential, Permission, User
from bluebubbles.server.routes.authentication import (
    current_authenticated_user,
    current_profile,
    list_sessions,
    login,
    logout,
    logout_all,
    refresh,
    revoke_session,
)
from bluebubbles.server.services.authentication import (
    AuthenticationService,
    LoginContext,
)
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.server.services.sessions import DeviceDescriptor, SessionService
from bluebubbles.shared.errors.exceptions import (
    AccountDisabledError,
    AccountLockedError,
    InvalidCredentialsError,
    InvalidTokenError,
    RefreshTokenReuseError,
    SessionExpiredError,
)
from bluebubbles.shared.models.health import HealthState
from bluebubbles.shared.models.sessions import (
    LoginRequest,
    RefreshTokenRequest,
    SessionSummary,
)

NOW = datetime(2026, 7, 17, 12, tzinfo=UTC)
USER_ID = UUID("10000000-0000-0000-0000-000000000001")
SESSION_ID = UUID("20000000-0000-0000-0000-000000000002")


def _user(*, enabled: bool = True) -> User:
    return User(
        id=USER_ID,
        created_at=NOW,
        updated_at=NOW,
        username="employee1",
        display_name="Employee One",
        role_id=stable_seed_id("role", "Employee"),
        is_enabled=enabled,
    )


class _Sessions:
    def __init__(self) -> None:
        self.values: dict[UUID, Session] = {}

    async def create(self, session: Session) -> Session:
        self.values[session.id] = session
        return session

    async def get_active_by_id(self, session_id: UUID, **_kwargs):
        return self.values.get(session_id)

    async def get_by_id(self, session_id: UUID):
        return self.values.get(session_id)

    async def list_active_for_user(self, user_id: UUID):
        return [item for item in self.values.values() if item.user_id == user_id]

    async def rotate_refresh_token(
        self, session_id, token_hash, version, at, access_expires_at=None
    ):
        assert session_id in self.values and token_hash and version > 1
        assert at.tzinfo is not None and access_expires_at is not None
        return True

    async def invalidate(self, session_id, at, reason):
        session = self.values.get(session_id)
        if session is None or session.invalidated_at is not None:
            return False
        session.invalidated_at = at
        session.invalidation_reason = reason
        return True

    async def invalidate_all_for_user(self, user_id, at, reason):
        count = 0
        for session in self.values.values():
            if session.user_id == user_id and session.invalidated_at is None:
                session.invalidated_at = at
                session.invalidation_reason = reason
                count += 1
        return count


class _Users:
    def __init__(self, user: User | None) -> None:
        self.user = user

    async def get_by_id(self, user_id: UUID):
        return self.user if self.user is not None and self.user.id == user_id else None


class _AuthenticationRepo:
    async def permissions_for_role(self, _role_id):
        return frozenset({Permission.SEND_MESSAGE})


class _AuditWriter:
    def __init__(self) -> None:
        self.events: list[str] = []

    async def append(self, _repository, **values):
        self.events.append(values["event_type"])


class _Unit:
    def __init__(self, sessions: _Sessions, user: User | None) -> None:
        self.sessions = sessions
        self.users = _Users(user)
        self.authentication = _AuthenticationRepo()
        self.audit = object()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def commit(self):
        self.committed = True


class _Factory:
    def __init__(self, sessions: _Sessions, user: User | None) -> None:
        self.sessions = sessions
        self.user = user
        self.units: list[_Unit] = []

    def __call__(self):
        unit = _Unit(self.sessions, self.user)
        self.units.append(unit)
        return unit


class _Notifier:
    def __init__(self) -> None:
        self.sessions: list[UUID] = []
        self.users: list[UUID] = []

    async def session_revoked(self, session_id: UUID):
        self.sessions.append(session_id)

    async def user_sessions_revoked(self, user_id: UUID):
        self.users.append(user_id)


@pytest.mark.asyncio
async def test_session_issue_validate_rotate_reuse_and_revocation() -> None:
    settings = TokenSettings(signing_secret=SecretStr("s" * 32))
    random_values = iter((b"r" * 32, b"n" * 32))
    token_manager = TokenManager(
        settings, clock=lambda: NOW, random_bytes=lambda _size: next(random_values)
    )
    sessions = _Sessions()
    factory = _Factory(sessions, _user())
    audit = _AuditWriter()
    notifier = _Notifier()
    service = SessionService(
        factory,
        token_manager,
        settings,
        audit,
        notifier=notifier,
        clock=lambda: NOW,
    )
    unit = factory()
    pair = await service.issue_in_transaction(
        unit,
        _user(),
        DeviceDescriptor(uuid4(), "Office PC", "0.1.0"),
        "192.0.2.1",
    )
    authenticated = await service.authenticate_access_token(pair.access_token)
    assert authenticated.user_id == USER_ID
    summaries = await service.list_for_user(authenticated)
    assert summaries[0].current and summaries[0].source_ip == "192.0.2.1"
    first_refresh = pair.refresh_token
    rotated = await service.refresh(
        RefreshTokenRequest(
            refresh_token=SecretStr(first_refresh), session_id=pair.session.id
        )
    )
    assert rotated.refresh_token != first_refresh
    with pytest.raises(RefreshTokenReuseError):
        await service.refresh(
            RefreshTokenRequest(
                refresh_token=SecretStr(first_refresh), session_id=pair.session.id
            )
        )
    assert notifier.sessions == [pair.session.id]

    pair.session.invalidated_at = None
    pair.session.invalidation_reason = None
    with pytest.raises(InvalidTokenError):
        await service.refresh(
            RefreshTokenRequest(
                refresh_token=SecretStr("arbitrary"), session_id=pair.session.id
            )
        )
    await service.invalidate(authenticated, pair.session.id, "logout")
    assert notifier.sessions[-1] == pair.session.id
    pair.session.invalidated_at = None
    assert await service.invalidate_all_for_user(USER_ID, "all") == 1
    assert notifier.users == [USER_ID]


@pytest.mark.asyncio
async def test_session_validation_rejects_missing_disabled_and_wrong_version() -> None:
    settings = TokenSettings(signing_secret=SecretStr("s" * 32))
    manager = TokenManager(settings, clock=lambda: NOW)
    sessions = _Sessions()
    session = Session(
        id=SESSION_ID,
        created_at=NOW,
        updated_at=NOW,
        user_id=USER_ID,
        refresh_token_hash="00" * 32,
        expires_at=NOW + timedelta(days=1),
        idle_expires_at=NOW + timedelta(minutes=15),
        ip_address="unknown",
        device_name="PC",
        platform="0.1.0",
        login_time=NOW,
    )
    sessions.values[SESSION_ID] = session
    token = manager.create_access_token(_user(), session)
    service = SessionService(
        _Factory(sessions, _user(enabled=False)),
        manager,
        settings,
        _AuditWriter(),
        clock=lambda: NOW,
    )
    with pytest.raises(SessionExpiredError):
        await service.authenticate_access_token(token)
    service = SessionService(
        _Factory(sessions, _user()),
        manager,
        settings,
        _AuditWriter(),
        clock=lambda: NOW,
    )
    session.version = 2
    with pytest.raises(InvalidTokenError):
        await service.authenticate_access_token(token)


class _Entry:
    entry_dn = "CN=Employee,DC=example,DC=test"
    entry_attributes_as_dict = {
        "sAMAccountName": ["employee1"],
        "displayName": ["Employee One"],
        "mail": ["e@example.test"],
        "department": ["IT"],
        "title": ["Engineer"],
        "objectGUID": ["guid"],
        "memberOf": ["Staff"],
        "userAccountControl": [512],
    }


class _LdapConnection:
    def __init__(self, entries=None, *, search_result=True) -> None:
        self.entries = list(entries or [])
        self.search_result = search_result
        self.filter = ""
        self.unbound = False

    def search(self, _base, selected_filter, **_kwargs):
        self.filter = selected_filter
        return self.search_result

    def unbind(self):
        self.unbound = True


class _LdapFactory:
    def __init__(self, connection: _LdapConnection) -> None:
        self.connection = connection
        self.user = _LdapConnection()

    def service_connection(self):
        return self.connection

    def user_connection(self, distinguished_name: str, password: str):
        assert distinguished_name.startswith("CN=") and password == "password"
        return self.user


def _directory_settings() -> DirectorySettings:
    return DirectorySettings(
        provider="ldap",
        server="directory.example.test",
        port=636,
        bind_dn="CN=service",
        bind_password=SecretStr("service-password"),
        base_dn="DC=example,DC=test",
        connection_timeout_seconds=1,
        search_timeout_seconds=1,
    )


@pytest.mark.asyncio
async def test_ldap_provider_escapes_maps_binds_and_reports_health() -> None:
    connection = _LdapConnection([_Entry()])
    factory = _LdapFactory(connection)
    ticks = iter((1.0, 1.002))
    provider = LDAPAuthenticationProvider(
        _directory_settings(), factory, clock=lambda: next(ticks)
    )
    identity = await provider.authenticate(
        SimpleNamespace(username="emp*)(uid=*)", password=SecretStr("password"))
    )
    assert identity.username == "employee1" and identity.groups == ("Staff",)
    assert "\\2a" in connection.filter and factory.user.unbound
    assert await provider.get_user_by_identifier("employee1") == identity
    health = await provider.check_health()
    assert health.state is HealthState.HEALTHY and health.latency_ms == pytest.approx(2)
    missing = LDAPAuthenticationProvider(
        _directory_settings(), _LdapFactory(_LdapConnection())
    )
    with pytest.raises(InvalidCredentialsError):
        await missing.authenticate(
            SimpleNamespace(username="missing", password=SecretStr("password"))
        )


@pytest.mark.asyncio
async def test_ldap_provider_rejects_disabled_and_translates_outage() -> None:
    disabled = _Entry()
    disabled.entry_attributes_as_dict = {
        **_Entry.entry_attributes_as_dict,
        "userAccountControl": [514],
    }
    provider = LDAPAuthenticationProvider(
        _directory_settings(), _LdapFactory(_LdapConnection([disabled]))
    )
    with pytest.raises(AccountDisabledError):
        await provider.authenticate(
            SimpleNamespace(username="employee1", password=SecretStr("password"))
        )

    class _BrokenFactory(_LdapFactory):
        def service_connection(self):
            raise LDAPException("offline")

    broken = LDAPAuthenticationProvider(
        _directory_settings(), _BrokenFactory(_LdapConnection())
    )
    with pytest.raises(Exception, match="Directory unavailable"):
        await broken.get_user_by_identifier("employee1")
    assert (await broken.check_health()).state is HealthState.UNHEALTHY


class _RouteAuthentication:
    async def validate_current_user(self, token):
        if token != "valid":
            raise InvalidTokenError()
        return AuthenticatedUser(USER_ID, SESSION_ID, "employee1", uuid4(), frozenset())

    async def login(self, request, context):
        user = _user()
        token_data = SimpleNamespace(
            access_token="access",
            refresh_token="refresh",
            access_expires_at=NOW + timedelta(minutes=15),
            refresh_expires_at=NOW + timedelta(days=7),
            session=SimpleNamespace(id=SESSION_ID),
        )
        return SimpleNamespace(
            user=user,
            role_name="Employee",
            permissions=("send_message",),
            tokens=token_data,
        )

    async def get_profile(self, _current):
        return _user(), "Employee"


class _RouteSessions:
    def __init__(self) -> None:
        self.actions: list[str] = []

    async def refresh(self, _request):
        return SimpleNamespace(
            access_token="access2",
            refresh_token="refresh2",
            access_expires_at=NOW + timedelta(minutes=15),
            refresh_expires_at=NOW + timedelta(days=7),
            session=SimpleNamespace(id=SESSION_ID),
        )

    async def invalidate(self, _current, _session_id, reason):
        self.actions.append(reason)

    async def invalidate_all_for_user(self, _user_id, reason):
        self.actions.append(reason)
        return 1

    async def list_for_user(self, _current):
        return (
            SessionSummary(
                id=SESSION_ID,
                device_name="PC",
                platform="0.1.0",
                created_at=NOW,
                last_seen_at=NOW,
                expires_at=NOW + timedelta(days=1),
            ),
        )


@pytest.mark.asyncio
async def test_authentication_routes_delegate_without_implementing_policy() -> None:
    route_sessions = _RouteSessions()
    container = SimpleNamespace(
        settings=SimpleNamespace(
            tokens=SimpleNamespace(access_token_lifetime_seconds=900)
        ),
        services=SimpleNamespace(
            authentication=_RouteAuthentication(), sessions=route_sessions
        ),
    )
    request = SimpleNamespace(client=SimpleNamespace(host="192.0.2.1"))
    login_response = await login(
        LoginRequest(
            username="employee1", password=SecretStr("password"), device_name="PC"
        ),
        request,
        container,
    )
    assert login_response.session_id == SESSION_ID
    current = await current_authenticated_user(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid"), container
    )
    assert (await current_profile(current, container)).role == "Employee"
    refreshed = await refresh(
        RefreshTokenRequest(refresh_token=SecretStr("refresh"), session_id=SESSION_ID),
        container,
    )
    assert refreshed.access_token.get_secret_value() == "access2"
    assert len((await list_sessions(current, container)).sessions) == 1
    assert (await logout(current, container)).status_code == 204
    assert (await logout_all(current, container)).status_code == 204
    assert (
        await revoke_session(str(SESSION_ID), current, container)
    ).status_code == 204
    assert route_sessions.actions == [
        "user_logout",
        "user_logout_all",
        "user_device_revocation",
    ]
    with pytest.raises(InvalidTokenError):
        await current_authenticated_user(None, container)
    with pytest.raises(InvalidTokenError):
        await revoke_session("bad", current, container)


def test_fastapi_login_serialises_real_tokens_and_logout_revokes() -> None:
    """Exercise the complete HTTP model/dependency/serialization boundary."""
    route_sessions = _RouteSessions()

    class Container:
        def __init__(self) -> None:
            self.settings = ServerSettings()
            self.services = SimpleNamespace(
                authentication=_RouteAuthentication(),
                sessions=route_sessions,
                health=SimpleNamespace(),
            )

        async def start(self) -> None:
            return None

        async def stop(self) -> None:
            return None

    application = create_application(
        ServerSettings(), container=cast(ServerContainer, Container())
    )
    with TestClient(application) as client:
        logged_in = client.post(
            "/api/v1/auth/login",
            json={
                "username": "employee1",
                "password": "password",
                "device_name": "Office PC",
            },
        )
        logged_out = client.post(
            "/api/v1/auth/logout", headers={"Authorization": "Bearer valid"}
        )
        rejected = client.get("/api/v1/auth/me")
    assert logged_in.status_code == 200
    assert logged_in.json()["access_token"] == "access"
    assert logged_in.json()["refresh_token"] == "refresh"
    assert logged_out.status_code == 204
    assert rejected.status_code == 401
    assert rejected.json()["error"]["code"] == "INVALID_TOKEN"


class _LocalAuthenticationRepo(_AuthenticationRepo):
    def __init__(self, user: User, credential: LocalCredential) -> None:
        self.user = user
        self.credential = credential
        self.updated = False

    async def get_local_identity(self, _username):
        return self.user, self.credential

    async def update_local_credential(self, credential):
        self.credential = credential
        self.updated = True


class _LocalUnit(_Unit):
    def __init__(self, repository: _LocalAuthenticationRepo) -> None:
        super().__init__(_Sessions(), repository.user)
        self.authentication = repository


class _LocalFactory:
    def __init__(self, repository: _LocalAuthenticationRepo) -> None:
        self.repository = repository

    def __call__(self):
        return _LocalUnit(self.repository)


@pytest.mark.asyncio
async def test_local_provider_verifies_enabled_accounts_and_safe_failures() -> None:
    hasher = PasswordHasher(
        PasswordHashingParameters(
            time_cost=1,
            memory_cost_kib=1024,
            parallelism=1,
            hash_length=16,
            salt_length=8,
        )
    )
    password = SecretStr("local-password")
    credential = LocalCredential(
        id=USER_ID,
        created_at=NOW,
        updated_at=NOW,
        user_id=USER_ID,
        password_hash=hasher.hash_password(password),
    )
    repository = _LocalAuthenticationRepo(_user(), credential)
    provider = LocalAuthenticationProvider(
        _LocalFactory(repository), hasher, enabled=True, clock=lambda: NOW
    )
    identity = await provider.authenticate(LoginCredentials("employee1", password))
    assert identity.username == "employee1"
    assert await provider.get_user_by_identifier("employee1") == identity
    assert (await provider.check_health()).state is HealthState.HEALTHY
    with pytest.raises(InvalidCredentialsError):
        await provider.authenticate(
            LoginCredentials("employee1", SecretStr("incorrect"))
        )
    repository.user = _user(enabled=False)
    with pytest.raises(AccountDisabledError):
        await provider.authenticate(LoginCredentials("employee1", password))
    repository.user = _user()
    repository.credential.locked_until = NOW + timedelta(minutes=1)
    with pytest.raises(AccountLockedError):
        await provider.authenticate(LoginCredentials("employee1", password))
    disabled = LocalAuthenticationProvider(
        _LocalFactory(repository), hasher, enabled=False
    )
    with pytest.raises(InvalidCredentialsError):
        await disabled.authenticate(LoginCredentials("employee1", password))
    assert await disabled.get_user_by_identifier("employee1") is None
    assert (await disabled.check_health()).state is HealthState.DEGRADED


class _PermissionConversation:
    def __init__(self, member) -> None:
        self.member = member

    async def get_active_membership(self, _conversation_id, _user_id):
        return self.member


@pytest.mark.asyncio
async def test_permission_service_checks_database_and_resource_membership() -> None:
    from bluebubbles.server.domain.conversations import ConversationMember
    from bluebubbles.shared.errors.exceptions import (
        AuthorisationError,
        ResourceNotFoundError,
    )
    from bluebubbles.shared.models.conversations import GroupRole

    member = ConversationMember(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        conversation_id=uuid4(),
        user_id=USER_ID,
        role=GroupRole.ADMIN,
        joined_at=NOW,
    )
    factory = _Factory(_Sessions(), _user())
    original_call = factory.__call__

    def unit_with_conversation():
        unit = original_call()
        unit.conversations = _PermissionConversation(member)
        return unit

    service = PermissionService(SimpleNamespace(__call__=unit_with_conversation))
    # Special methods are resolved on the class, so use a small callable wrapper.
    service = PermissionService(
        type("Factory", (), {"__call__": lambda _self: unit_with_conversation()})()
    )
    await service.require_permission(_user(), Permission.SEND_MESSAGE)
    authenticated = AuthenticatedUser(
        USER_ID, SESSION_ID, "employee1", _user().role_id, frozenset()
    )
    await service.require_authenticated_permission(
        authenticated, Permission.SEND_MESSAGE
    )
    assert (
        await service.require_conversation_access(USER_ID, member.conversation_id)
        == member
    )
    assert (
        await service.require_group_role(
            USER_ID, member.conversation_id, GroupRole.MEMBER
        )
        == member
    )
    with pytest.raises(AuthorisationError):
        await service.require_group_role(
            USER_ID, member.conversation_id, GroupRole.OWNER
        )
    member_holder = _PermissionConversation(None)

    def missing_unit():
        unit = original_call()
        unit.conversations = member_holder
        return unit

    missing_service = PermissionService(
        type("Factory", (), {"__call__": lambda _self: missing_unit()})()
    )
    with pytest.raises(ResourceNotFoundError):
        await missing_service.require_conversation_access(USER_ID, uuid4())


@pytest.mark.asyncio
async def test_authentication_service_login_and_username_normalisation() -> None:
    class Provider:
        async def authenticate(self, credentials):
            assert credentials.username == "employee1"
            return DirectoryUser("employee1", "Employee One")

    class Attempts:
        def __init__(self):
            self.results = []

        async def require_allowed(self, username, source):
            assert username == "employee1" and source == "192.0.2.1"

        async def record(self, _unit, **values):
            self.results.append(values["result"])

        async def record_failure(self, *_args):
            self.results.append("failed")

    class Sync:
        async def synchronise_user(self, _unit, _identity, _at):
            return _user(), "Employee"

    class Sessions:
        async def issue_in_transaction(self, _unit, user, device, source):
            assert user.id == USER_ID and source == "192.0.2.1"
            return SimpleNamespace(session=SimpleNamespace(id=SESSION_ID))

        async def authenticate_access_token(self, _token):
            return AuthenticatedUser(
                USER_ID, SESSION_ID, "employee1", _user().role_id, frozenset()
            )

    attempts = Attempts()
    service = AuthenticationService(
        Provider(),
        _Factory(_Sessions(), _user()),
        Sessions(),
        attempts,
        Sync(),
        _AuditWriter(),
        AuthenticationSettings(
            username_domain_prefix="COMPANY", username_upn_suffix="example.test"
        ),
        DirectorySettings(),
        clock=lambda: NOW,
    )
    result = await service.login(
        LoginRequest(
            username="COMPANY\\Employee1",
            password=SecretStr("password"),
            device_name="PC",
        ),
        LoginContext("192.0.2.1", uuid4()),
    )
    assert result.user.id == USER_ID and attempts.results == ["success"]
    assert service.normalise_login_username("employee1@example.test") == "employee1"
    with pytest.raises(InvalidCredentialsError):
        service.normalise_login_username("OTHER\\employee1")
    with pytest.raises(InvalidCredentialsError):
        service.normalise_login_username("employee1@other.test")
    assert (await service.validate_current_user("access")).user_id == USER_ID
