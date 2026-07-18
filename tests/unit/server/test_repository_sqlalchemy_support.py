"""Unit tests for Task 06 supporting SQLAlchemy repository adapters."""

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.administration import DataExportJobORM
from bluebubbles.server.database.models.announcements import AnnouncementORM
from bluebubbles.server.database.models.audit import SecurityAlertORM
from bluebubbles.server.database.models.configuration import ConfigurationVersionORM
from bluebubbles.server.database.models.contacts import ContactRelationshipORM
from bluebubbles.server.database.models.identity import UserORM
from bluebubbles.server.database.models.keys import UserPublicKeyORM
from bluebubbles.server.domain.alerts import SecurityAlert
from bluebubbles.server.domain.announcements import Announcement
from bluebubbles.server.domain.configuration import ConfigurationRevision
from bluebubbles.server.domain.contacts import Contact
from bluebubbles.server.domain.sessions import Session
from bluebubbles.server.domain.users import (
    LocalCredential,
    Permission,
    PublicKeyRecord,
    User,
)
from bluebubbles.server.repositories.mapping.sessions import SessionMapper
from bluebubbles.server.repositories.mapping.users import UserMapper
from bluebubbles.server.repositories.sqlalchemy._common import (
    flush_changes,
    require_aware,
)
from bluebubbles.server.repositories.sqlalchemy.administration import (
    SqlAlchemyAdministrationRepository,
)
from bluebubbles.server.repositories.sqlalchemy.alerts import (
    SqlAlchemySecurityAlertRepository,
)
from bluebubbles.server.repositories.sqlalchemy.announcements import (
    SqlAlchemyAnnouncementRepository,
)
from bluebubbles.server.repositories.sqlalchemy.authentication import (
    SqlAlchemyAuthenticationRepository,
)
from bluebubbles.server.repositories.sqlalchemy.configuration import (
    SqlAlchemyConfigurationRepository,
)
from bluebubbles.server.repositories.sqlalchemy.contacts import (
    SqlAlchemyContactRepository,
)
from bluebubbles.server.repositories.sqlalchemy.keys import (
    SqlAlchemyPublicKeyRepository,
)
from bluebubbles.server.repositories.sqlalchemy.sessions import (
    SqlAlchemySessionRepository,
)
from bluebubbles.server.repositories.sqlalchemy.users import SqlAlchemyUserRepository
from bluebubbles.server.repositories.types import UserSearchQuery
from bluebubbles.shared.errors.exceptions import ConflictError, RepositoryError
from bluebubbles.shared.models.administration import DataExportJobResponse, JobState
from bluebubbles.shared.models.announcements import (
    AnnouncementPriority,
    AnnouncementTargetType,
)

NOW = datetime(2026, 7, 17, 12, tzinfo=UTC)


class FakeScalarResult:
    """Provide the small scalar-result surface used by repositories."""

    def __init__(self, values: list[Any]) -> None:
        self._values = values

    def all(self) -> list[Any]:
        return self._values


class FakeResult:
    """Provide scalar and row-count result behavior."""

    def __init__(self, value: Any = None, rowcount: int = 1) -> None:
        self._value = value
        self.rowcount = rowcount

    def scalar_one_or_none(self) -> Any:
        return self._value


class FakeSession:
    """Queue deterministic results while recording staged ORM objects."""

    def __init__(self) -> None:
        self.execute_results: list[FakeResult] = []
        self.scalar_results: list[list[Any]] = []
        self.get_results: list[Any] = []
        self.single_scalar_results: list[Any] = []
        self.added: list[Any] = []
        self.flush_error: Exception | None = None
        self.flush_count = 0

    async def execute(self, statement: object) -> FakeResult:
        del statement
        return self.execute_results.pop(0) if self.execute_results else FakeResult()

    async def scalars(self, statement: object) -> FakeScalarResult:
        del statement
        values = self.scalar_results.pop(0) if self.scalar_results else []
        return FakeScalarResult(values)

    async def get(self, model: object, identity: object) -> Any:
        del model, identity
        return self.get_results.pop(0) if self.get_results else None

    async def scalar(self, statement: object) -> Any:
        del statement
        return self.single_scalar_results.pop(0)

    def add(self, value: object) -> None:
        self.added.append(value)

    def add_all(self, values: list[object]) -> None:
        self.added.extend(values)

    async def flush(self) -> None:
        self.flush_count += 1
        if self.flush_error is not None:
            raise self.flush_error


def _session(fake: FakeSession) -> AsyncSession:
    return cast(AsyncSession, fake)


def _user() -> User:
    return User(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        username="alice",
        display_name="Alice",
        role_id=uuid4(),
        email="alice@example.test",
    )


def _session_domain() -> Session:
    return Session(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        user_id=uuid4(),
        refresh_token_hash="ab" * 32,
        expires_at=NOW + timedelta(days=1),
        idle_expires_at=NOW + timedelta(hours=1),
        ip_address="127.0.0.1",
        device_name="Desktop",
        platform="1.0",
        login_time=NOW,
    )


@pytest.mark.asyncio
async def test_common_flush_translation_and_timestamp_validation() -> None:
    """Database details are translated and naive timestamps are rejected."""
    fake = FakeSession()
    await flush_changes(_session(fake))
    assert fake.flush_count == 1
    fake.flush_error = IntegrityError("insert", {}, Exception("secret detail"))
    with pytest.raises(ConflictError, match="integrity constraint"):
        await flush_changes(_session(fake))
    fake.flush_error = DBAPIError("select", {}, Exception("secret detail"), False)
    with pytest.raises(RepositoryError, match="adapter operation"):
        await flush_changes(_session(fake))
    require_aware(NOW, "now")
    with pytest.raises(ValueError, match="timezone-aware"):
        require_aware(datetime(2026, 1, 1), "now")


@pytest.mark.asyncio
async def test_user_repository_reads_searches_and_creates() -> None:
    """User adapter maps reads, stable search pages, and caller-owned writes."""
    fake = FakeSession()
    user = _user()
    record = UserMapper.to_orm(user)
    fake.execute_results = [FakeResult(record), FakeResult(record), FakeResult(record)]
    fake.scalar_results = [[record, record], [record]]
    repository = SqlAlchemyUserRepository(_session(fake))
    assert await repository.get_by_id(user.id, for_update=True) == user
    assert await repository.get_by_normalised_username(" Alice ") == user
    assert await repository.get_by_directory_guid(uuid4()) == user
    page = await repository.search(UserSearchQuery(term="ali", limit=1))
    assert page.items == (user,)
    assert page.next_cursor is not None
    final_page = await repository.search(
        UserSearchQuery(limit=1, cursor=page.next_cursor, include_deleted=True)
    )
    assert final_page.next_cursor is None
    assert await repository.create(user) is user
    assert isinstance(fake.added[-1], UserORM)


@pytest.mark.asyncio
async def test_user_repository_updates_and_conflicts() -> None:
    """User writes use optimistic versions and safe soft deletion."""
    fake = FakeSession()
    repository = SqlAlchemyUserRepository(_session(fake))
    user = _user()
    user.update_profile(display_name="Alice B", status_message="Available", at=NOW)
    fake.execute_results = [
        FakeResult(rowcount=1),
        FakeResult(rowcount=1),
        FakeResult(rowcount=1),
        FakeResult(rowcount=1),
        FakeResult(rowcount=0),
    ]
    assert await repository.update(user, expected_version=1) is user
    assert await repository.update_profile(user, expected_version=1) is user
    assert await repository.set_enabled(user.id, False, expected_version=2)
    assert await repository.set_role(user.id, uuid4(), expected_version=3)
    assert not await repository.soft_delete(user.id, NOW, expected_version=4)
    fake.execute_results = [FakeResult(rowcount=0)]
    with pytest.raises(ConflictError, match="changed"):
        await repository.update(user, expected_version=1)


@pytest.mark.asyncio
async def test_user_repository_missing_and_invalid_cursor_paths() -> None:
    """Missing users return None and malformed cursors are rejected."""
    fake = FakeSession()
    repository = SqlAlchemyUserRepository(_session(fake))
    fake.execute_results = [FakeResult(), FakeResult(), FakeResult()]
    assert await repository.get_by_id(uuid4()) is None
    assert await repository.get_by_normalised_username("nobody") is None
    assert await repository.get_by_directory_guid(uuid4()) is None
    with pytest.raises(ValueError):
        await repository.search(UserSearchQuery(cursor="bad"))


@pytest.mark.asyncio
async def test_session_repository_complete_lifecycle() -> None:
    """Session adapter covers creation, lookup, rotation, expiry, and cleanup."""
    fake = FakeSession()
    domain = _session_domain()
    record = SessionMapper.to_orm(domain)
    repository = SqlAlchemySessionRepository(_session(fake))
    assert await repository.create(domain) is domain
    fake.get_results = [record, None]
    assert await repository.get_by_id(domain.id) == domain
    assert await repository.get_by_id(uuid4()) is None
    fake.execute_results = [FakeResult(record), FakeResult(), FakeResult(record)]
    assert await repository.get_active(domain.id, for_update=True) == domain
    assert await repository.get_active_by_id(uuid4()) is None
    assert await repository.get_active_by_id(domain.id) == domain
    fake.scalar_results = [[record], [record], [record]]
    assert await repository.list_active_for_user(domain.user_id) == [domain]
    assert await repository.list_expired(NOW, limit=1) == [domain]
    fake.execute_results = [
        FakeResult(rowcount=1),
        FakeResult(rowcount=1),
        FakeResult(rowcount=1),
        FakeResult(rowcount=1),
        FakeResult(rowcount=2),
        FakeResult(rowcount=1),
    ]
    assert await repository.update_last_seen(domain.id, NOW)
    assert await repository.rotate_refresh_token(domain.id, b"hash", 2, NOW)
    await repository.update_refresh_token(domain.id, b"hash", 3, NOW)
    assert await repository.invalidate(domain.id, NOW, "logout")
    assert await repository.invalidate_all_for_user(domain.user_id, NOW, "admin") == 2
    assert await repository.delete_expired(NOW, limit=1) == 1


@pytest.mark.asyncio
async def test_session_repository_validation_and_empty_cleanup() -> None:
    """Invalid session mutation inputs and empty cleanup batches are safe."""
    fake = FakeSession()
    repository = SqlAlchemySessionRepository(_session(fake))
    fake.execute_results = [FakeResult(rowcount=0), FakeResult(rowcount=0)]
    assert not await repository.rotate_refresh_token(uuid4(), b"hash", 2, NOW)
    with pytest.raises(ValueError, match="not found"):
        await repository.update_refresh_token(uuid4(), b"hash", 2, NOW)
    with pytest.raises(ValueError, match="required"):
        await repository.rotate_refresh_token(uuid4(), b"", 0, NOW)
    with pytest.raises(ValueError, match="reason"):
        await repository.invalidate(uuid4(), NOW, " ")
    with pytest.raises(ValueError, match="reason"):
        await repository.invalidate_all_for_user(uuid4(), NOW, " ")
    with pytest.raises(ValueError, match="positive"):
        await repository.list_expired(NOW, limit=0)
    fake.scalar_results = [[]]
    assert await repository.delete_expired(NOW, limit=1) == 0


@pytest.mark.asyncio
async def test_contact_repository_lifecycle() -> None:
    """Directional contacts can be inserted, updated, listed, and removed."""
    fake = FakeSession()
    contact = Contact(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        owner_id=uuid4(),
        contact_id=uuid4(),
        is_favourite=True,
        weight_score=5,
    )
    record = ContactRelationshipORM(
        owner_user_id=contact.owner_id,
        contact_user_id=contact.contact_id,
        is_favourite=True,
        is_blocked=False,
        weight=5,
        last_contacted_at=None,
        created_at=NOW,
        updated_at=NOW,
    )
    repository = SqlAlchemyContactRepository(_session(fake))
    fake.get_results = [record, None, None, record]
    assert (await repository.get(contact.owner_id, contact.contact_id)) is not None
    assert await repository.get(uuid4(), uuid4()) is None
    fake.scalar_results = [[record]]
    assert len(await repository.list_for_owner(contact.owner_id)) == 1
    assert await repository.upsert(contact) is contact
    assert await repository.upsert(contact) is contact
    fake.execute_results = [FakeResult(rowcount=1)]
    assert await repository.delete(contact.owner_id, contact.contact_id)


def _public_key() -> PublicKeyRecord:
    return PublicKeyRecord(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        user_id=uuid4(),
        key_version=1,
        algorithm="ED25519-V1",
        public_key=b"public",
        fingerprint="fingerprint",
    )


@pytest.mark.asyncio
async def test_public_key_repository_lifecycle() -> None:
    """Public keys are versioned, listed, selected, and irreversibly revoked."""
    fake = FakeSession()
    key = _public_key()
    repository = SqlAlchemyPublicKeyRepository(_session(fake))
    assert await repository.add(key, key_type="signing") is key
    record = cast(UserPublicKeyORM, fake.added[-1])
    fake.execute_results = [FakeResult(record), FakeResult()]
    assert await repository.get_active(key.user_id, key_type="signing") == key
    assert await repository.get_active(uuid4(), key_type="signing") is None
    fake.scalar_results = [[record]]
    assert await repository.list_for_user(key.user_id) == [key]
    fake.execute_results = [FakeResult(rowcount=1)]
    assert await repository.revoke(key.id, NOW, "rotation")
    with pytest.raises(ValueError, match="Key type"):
        await repository.add(key, key_type="private")
    with pytest.raises(ValueError, match="reason"):
        await repository.revoke(key.id, NOW, " ")


def _announcement() -> Announcement:
    return Announcement(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        author_id=uuid4(),
        title="Maintenance",
        body="Planned maintenance at 18:00.",
        priority=AnnouncementPriority.IMPORTANT,
        target_type=AnnouncementTargetType.GROUP,
        target_ids=(uuid4(),),
        published_at=NOW,
        expires_at=NOW + timedelta(days=1),
    )


@pytest.mark.asyncio
async def test_announcement_repository_lifecycle() -> None:
    """Current announcements and acknowledgements map without message semantics."""
    fake = FakeSession()
    announcement = _announcement()
    repository = SqlAlchemyAnnouncementRepository(_session(fake))
    assert await repository.add(announcement) is announcement
    record = cast(AnnouncementORM, fake.added[-1])
    fake.get_results = [record, None]
    assert await repository.get_by_id(announcement.id) == announcement
    assert await repository.get_by_id(uuid4()) is None
    fake.scalar_results = [[record]]
    assert await repository.list_current(NOW, limit=1) == [announcement]
    await repository.acknowledge(announcement.id, uuid4(), NOW)
    with pytest.raises(ValueError, match="positive"):
        await repository.list_current(NOW, limit=0)


@pytest.mark.asyncio
async def test_configuration_and_administration_repositories() -> None:
    """Configuration versions and worker summaries remain bounded and secret-free."""
    fake = FakeSession()
    configuration = SqlAlchemyConfigurationRepository(_session(fake))
    revision = ConfigurationRevision(
        revision=1,
        changed_at=NOW,
        changed_by=uuid4(),
        changed_keys=frozenset({"network.port"}),
        public_values={"network.port": 8443},
    )
    fake.execute_results = [FakeResult()]
    assert (
        await configuration.append(revision, reason="Initial", restart_required=True)
        is revision
    )
    record = cast(ConfigurationVersionORM, fake.added[-1])
    fake.execute_results = [FakeResult(record), FakeResult(record)]
    assert await configuration.get_latest() == revision
    assert await configuration.get_public_values() == {"network.port": 8443}
    fake.execute_results = [FakeResult()]
    assert await configuration.get_latest() is None
    fake.execute_results = [FakeResult()]
    assert await configuration.get_public_values() is None
    with pytest.raises(ValueError, match="reason"):
        await configuration.append(revision, reason=" ", restart_required=False)

    administration = SqlAlchemyAdministrationRepository(_session(fake))
    record_id = uuid4()
    await administration.add_worker_execution(
        record_id=record_id,
        worker_name="outbox",
        started_at=NOW,
        status="running",
        details=cast(Mapping[str, object], {"batch": 1}),
    )
    fake.execute_results = [FakeResult(rowcount=1)]
    assert await administration.complete_worker_execution(
        record_id,
        completed_at=NOW,
        status="complete",
        processed_count=1,
        failure_count=0,
    )
    with pytest.raises(ValueError, match="required"):
        await administration.add_worker_execution(
            record_id=uuid4(),
            worker_name=" ",
            started_at=NOW,
            status="running",
            details={},
        )
    with pytest.raises(ValueError, match="non-negative"):
        await administration.complete_worker_execution(
            record_id,
            completed_at=NOW,
            status="complete",
            processed_count=-1,
            failure_count=0,
        )


@pytest.mark.asyncio
async def test_security_alert_repository_maps_and_updates_lifecycle() -> None:
    """Security alert persistence supports locks, bounds, and concurrency."""
    fake = FakeSession()
    repository = SqlAlchemySecurityAlertRepository(_session(fake))
    alert = SecurityAlert(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        code="audit_integrity_failed",
        title="Audit verification failed",
        summary="The recent audit chain did not verify.",
        severity="critical",
        source_component="audit",
    )
    assert await repository.add(alert) is alert
    record = cast(SecurityAlertORM, fake.added[-1])
    fake.execute_results = [FakeResult(record), FakeResult(), FakeResult(record)]
    assert await repository.get_by_id(alert.id, for_update=True) == alert
    assert await repository.get_by_id(uuid4()) is None
    assert await repository.get_open_by_code(alert.code, for_update=True) == alert
    fake.scalar_results = [[record]]
    assert await repository.list_recent(limit=1) == (alert,)
    with pytest.raises(ValueError, match="between"):
        await repository.list_recent(limit=0)
    fake.execute_results = [FakeResult(rowcount=1), FakeResult(rowcount=0)]
    assert await repository.update(alert, expected_version=1) is alert
    with pytest.raises(ValueError, match="concurrently"):
        await repository.update(alert, expected_version=1)


@pytest.mark.asyncio
async def test_export_job_and_initial_credential_persistence() -> None:
    """Export ownership/state and initial password verifiers map safely."""
    fake = FakeSession()
    administration = SqlAlchemyAdministrationRepository(_session(fake))
    job = DataExportJobResponse(id=uuid4(), state=JobState.QUEUED, requested_at=NOW)
    owner = uuid4()
    expiry = NOW + timedelta(hours=24)
    await administration.add_export_job(
        job,
        requested_by=owner,
        export_type="audit_csv",
        filters={"severity": "warning"},
        expires_at=expiry,
    )
    record = cast(DataExportJobORM, fake.added[-1])
    fake.single_scalar_results = [record, None]
    loaded = await administration.get_export_job(job.id)
    assert loaded is not None and loaded[1] == owner and loaded[2] == expiry
    assert await administration.get_export_job(uuid4()) is None
    record.status = "succeeded"
    record.completed_at = NOW
    record.storage_reference = "protected.csv"
    fake.single_scalar_results = [record]
    succeeded = await administration.get_export_job(job.id)
    assert succeeded is not None
    assert succeeded[0].progress_percent == 100
    assert succeeded[0].download_url is not None
    fake.execute_results = [FakeResult(rowcount=1)]
    assert await administration.complete_export_job(
        job.id,
        completed_at=NOW,
        storage_reference="protected.csv",
        failure_code=None,
    )

    credential = LocalCredential(
        id=owner,
        created_at=NOW,
        updated_at=NOW,
        user_id=owner,
        password_hash="argon2id-hash",
    )
    authentication = SqlAlchemyAuthenticationRepository(_session(fake))
    await authentication.create_local_credential(credential)
    assert fake.added[-1].password_hash == "argon2id-hash"


@pytest.mark.asyncio
async def test_authentication_repository_metadata_queries_and_updates() -> None:
    """Authentication metadata remains bounded and password free."""
    fake = FakeSession()
    repository = SqlAlchemyAuthenticationRepository(_session(fake))
    user_id = uuid4()
    credential = LocalCredential(
        id=user_id,
        created_at=NOW,
        updated_at=NOW,
        user_id=user_id,
        password_hash="argon2id-hash",
    )
    fake.execute_results = [FakeResult(rowcount=1), FakeResult(rowcount=0)]
    await repository.update_local_credential(credential)
    with pytest.raises(ValueError, match="not found"):
        await repository.update_local_credential(credential)
    await repository.add_login_attempt(
        attempt_id=uuid4(),
        normalised_username="Alice",
        source_ip="192.0.2.1",
        result="failed",
        failure_category="invalid",
        attempted_at=NOW,
        correlation_id=uuid4(),
    )
    fake.single_scalar_results = [2, 3]
    assert await repository.count_recent_failures(
        normalised_username="Alice", source_ip="192.0.2.1", since=NOW
    ) == (2, 3)
    fake.scalar_results = [[Permission.AUDIT_VIEW.value]]
    assert await repository.permissions_for_role(user_id) == frozenset(
        {Permission.AUDIT_VIEW}
    )
    fake.single_scalar_results = ["Administrator"]
    assert await repository.role_name(user_id) == "Administrator"
    fake.get_results = [
        SimpleNamespace(id=user_id, name="Administrator"),
        None,
    ]
    fake.scalar_results = [[Permission.AUDIT_VIEW.value]]
    assert (await repository.get_role(user_id)).name == "Administrator"  # type: ignore[union-attr]
    assert await repository.get_role(uuid4()) is None
    fake.single_scalar_results = [1]
    assert await repository.count_enabled_users_with_role(user_id) == 1
