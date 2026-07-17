"""Security-focused unit tests for Task 09 authentication primitives and services."""

# mypy: disable-error-code="arg-type"

import base64
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from pydantic import SecretStr

from bluebubbles.server.authentication.directory_sync import (
    DirectorySynchronisationService,
)
from bluebubbles.server.authentication.mock_provider import MockAuthenticationProvider
from bluebubbles.server.authentication.password_hashing import (
    PasswordHasher,
    PasswordHashingParameters,
)
from bluebubbles.server.authentication.providers import DirectoryUser, LoginCredentials
from bluebubbles.server.authentication.tokens import TokenManager
from bluebubbles.server.configuration.settings import (
    AuthenticationSettings,
    TokenSettings,
)
from bluebubbles.server.database.seed import stable_seed_id
from bluebubbles.server.domain.sessions import Session
from bluebubbles.server.domain.users import User
from bluebubbles.shared.errors.exceptions import (
    DirectoryUnavailableError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from bluebubbles.shared.models.health import HealthState

NOW = datetime(2026, 7, 17, 12, tzinfo=UTC)
USER_ID = UUID("10000000-0000-0000-0000-000000000001")
SESSION_ID = UUID("20000000-0000-0000-0000-000000000002")


def _user(*, user_id: UUID = USER_ID) -> User:
    return User(
        id=user_id,
        created_at=NOW,
        updated_at=NOW,
        username="employee1",
        display_name="Employee One",
        role_id=stable_seed_id("role", "Employee"),
    )


def _session(*, version: int = 1) -> Session:
    return Session(
        id=SESSION_ID,
        created_at=NOW,
        updated_at=NOW,
        version=version,
        user_id=USER_ID,
        refresh_token_hash="00" * 32,
        expires_at=NOW + timedelta(days=7),
        idle_expires_at=NOW + timedelta(minutes=15),
        ip_address="192.0.2.1",
        device_name="Office PC",
        platform="0.1.0",
        login_time=NOW,
        device_id=uuid4(),
    )


def _token_manager(now: datetime = NOW) -> TokenManager:
    return TokenManager(
        TokenSettings(signing_secret=SecretStr("s" * 32)),
        clock=lambda: now,
        random_bytes=lambda size: b"r" * size,
    )


def test_password_hasher_uses_argon2id_and_supports_rehash() -> None:
    fast = PasswordHasher(
        PasswordHashingParameters(
            time_cost=1,
            memory_cost_kib=1024,
            parallelism=1,
            hash_length=16,
            salt_length=8,
        )
    )
    password = SecretStr("correct horse battery staple")
    encoded = fast.hash_password(password)
    assert encoded.startswith("$argon2id$")
    assert fast.verify_password(password, encoded)
    assert not fast.verify_password(SecretStr("wrong"), encoded)
    assert not fast.verify_password(password, "not-an-argon-hash")
    stronger = PasswordHasher(
        PasswordHashingParameters(
            time_cost=2,
            memory_cost_kib=1024,
            parallelism=1,
            hash_length=16,
            salt_length=8,
        )
    )
    assert stronger.needs_rehash(encoded)
    assert stronger.requires_rehash("invalid")
    assert stronger.verify_password(password, stronger.rehash_password(password))
    with pytest.raises(ValueError, match="positive"):
        PasswordHashingParameters(time_cost=0)


def test_token_manager_round_trip_hashing_and_strict_validation() -> None:
    manager = _token_manager()
    session = _session()
    token = manager.create_access_token(_user(), session)
    claims = manager.decode_access_token(token)
    assert claims.user_id == USER_ID and claims.session_id == SESSION_ID
    assert claims.token_version == 1 and claims.expires_at == session.idle_expires_at
    assert (
        manager.create_refresh_token()
        == base64.urlsafe_b64encode(b"r" * 32).rstrip(b"=").decode()
    )
    assert manager.hash_refresh_token("refresh") == manager.hash_refresh_token(
        "refresh"
    )
    with pytest.raises(InvalidTokenError):
        manager.hash_refresh_token("")
    with pytest.raises(InvalidTokenError):
        manager.decode_access_token(token + "tampered")
    with pytest.raises(InvalidTokenError):
        _token_manager(NOW + timedelta(hours=1)).decode_access_token(token)
    with pytest.raises(ValueError, match="HS256"):
        TokenManager(TokenSettings(signing_algorithm="RS256"))


def test_token_manager_rejects_algorithm_and_claim_type_confusion() -> None:
    manager = _token_manager()
    token = manager.create_access_token(_user(), _session())
    header, payload, _signature = token.split(".")
    decoded_header = json.loads(base64.urlsafe_b64decode(header + "=="))
    decoded_header["alg"] = "none"
    bad_header = (
        base64.urlsafe_b64encode(
            json.dumps(decoded_header, sort_keys=True, separators=(",", ":")).encode()
        )
        .rstrip(b"=")
        .decode()
    )
    with pytest.raises(InvalidTokenError):
        manager.decode_access_token(f"{bad_header}.{payload}.bad")
    with pytest.raises(InvalidTokenError):
        manager.decode_access_token("not-a-jwt")


@pytest.mark.asyncio
async def test_mock_provider_success_failure_outage_delay_and_health() -> None:
    identity = DirectoryUser("employee1", "Employee One", groups=("Staff",))
    provider = MockAuthenticationProvider(
        {"employee1": ("password", identity)}, response_delay_seconds=0.001
    )
    credentials = LoginCredentials("EMPLOYEE1", SecretStr("password"))
    assert await provider.authenticate(credentials) == identity
    assert await provider.get_user_by_identifier("EMPLOYEE1") == identity
    assert await provider.get_user_by_identifier("missing") is None
    assert (await provider.check_health()).state is HealthState.HEALTHY
    with pytest.raises(InvalidCredentialsError):
        await provider.authenticate(LoginCredentials("employee1", SecretStr("bad")))
    unavailable = MockAuthenticationProvider({}, unavailable=True)
    with pytest.raises(DirectoryUnavailableError):
        await unavailable.authenticate(credentials)
    assert (await unavailable.check_health()).state is HealthState.UNHEALTHY


class _Users:
    def __init__(self, existing: User | None = None) -> None:
        self.existing = existing
        self.created: User | None = None
        self.updated: User | None = None

    async def get_by_directory_guid(self, _guid: UUID) -> User | None:
        return self.existing

    async def get_by_normalised_username(self, _username: str) -> User | None:
        return self.existing

    async def create(self, user: User) -> User:
        self.created = user
        return user

    async def update(self, user: User, *, expected_version: int) -> User:
        assert expected_version == 1
        self.updated = user
        return user


class _Roles:
    async def role_name(self, role_id: UUID) -> str | None:
        if role_id == stable_seed_id("role", "Administrator"):
            return "Administrator"
        return "Employee"


@pytest.mark.asyncio
async def test_directory_sync_creates_updates_and_maps_highest_role() -> None:
    settings = AuthenticationSettings(
        default_role="Employee",
        directory_group_role_mapping={"staff": "Helpdesk", "admins": "Administrator"},
    )
    service = DirectorySynchronisationService(settings)
    users = _Users()
    unit = SimpleNamespace(users=users, authentication=_Roles())
    identity = DirectoryUser(
        "Employee1",
        "Employee One",
        email="e@example.test",
        directory_guid="not-a-uuid",
        groups=("STAFF", "admins"),
    )
    created, role = await service.synchronise_user(unit, identity, NOW)
    assert users.created is created and role == "Administrator"
    assert created.role_id == stable_seed_id("role", "Administrator")
    assert created.active_directory_guid is not None
    users.existing = created
    changed = DirectoryUser(
        "employee1", "Changed", distinguished_name="CN=Employee", groups=()
    )
    updated, role = await service.synchronise_user(
        unit, changed, NOW + timedelta(seconds=1)
    )
    assert users.updated is updated and updated.display_name == "Changed"
    assert role == "Employee"
