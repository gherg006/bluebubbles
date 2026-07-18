"""Task 19 administration, audit, alert, configuration, and route evidence."""

# mypy: disable-error-code="arg-type"

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from bluebubbles.server.authentication.providers import DirectoryUser
from bluebubbles.server.configuration.settings import (
    AuthenticationSettings,
    RateLimitSettings,
)
from bluebubbles.server.domain.alerts import SecurityAlert, SecurityAlertState
from bluebubbles.server.domain.audit import (
    AuditChainState,
    AuditEvent,
    AuditSeverity,
    build_canonical_audit_data,
    calculate_audit_hash,
)
from bluebubbles.server.domain.sessions import AuthenticatedUser, Session
from bluebubbles.server.domain.users import Permission, Role, User
from bluebubbles.server.repositories.types import CursorPage
from bluebubbles.server.routes.administration import router
from bluebubbles.server.routes.authentication import current_authenticated_user
from bluebubbles.server.services.administration import (
    AdminService,
    ConnectionAdministrationService,
    RoleAdministrationPolicy,
    SessionAdministrationService,
    UserAdministrationService,
)
from bluebubbles.server.services.alerts import SecurityAlertService
from bluebubbles.server.services.announcements import AnnouncementService
from bluebubbles.server.services.audit import (
    AuditIntegrityService,
    AuditService,
    AuditVisibilityFilter,
    AuditWriter,
    sanitise_audit_details,
)
from bluebubbles.server.services.bootstrap_administration import (
    InitialAdministratorService,
)
from bluebubbles.server.services.configuration import ConfigurationService
from bluebubbles.server.services.exports import AuditExportService
from bluebubbles.server.services.login_attempts import LoginAttemptService
from bluebubbles.shared.errors.exceptions import (
    AccountLockedError,
    ConflictError,
    RateLimitError,
)
from bluebubbles.shared.models.administration import (
    AdminDashboardResponse,
    AdminUserPageResponse,
    AdminUserSummary,
    AuditPageResponse,
    AuditVerificationResponse,
    ConfigurationSummary,
    ConnectionListResponse,
    DataExportJobResponse,
    DiagnosticCheckResult,
    JobState,
    MaintenanceState,
    MaintenanceStateResponse,
    SecurityAlertResponse,
    ServerDiagnosticReport,
    SessionRevocationResult,
    UserAdministrationResult,
    WorkerListResponse,
    WorkerStatusResponse,
)
from bluebubbles.shared.models.announcements import (
    AnnouncementPriority,
    AnnouncementResponse,
    AnnouncementTargetType,
    CreateAnnouncementRequest,
)
from bluebubbles.shared.models.health import (
    DetailedHealthResponse,
    HealthState,
)
from bluebubbles.shared.models.pagination import CursorPageMetadata
from bluebubbles.shared.models.users import PresenceState

NOW = datetime(2026, 7, 18, 12, tzinfo=UTC)
ACTOR_ID = UUID("10000000-0000-0000-0000-000000000001")
TARGET_ID = UUID("10000000-0000-0000-0000-000000000002")
SESSION_ID = UUID("20000000-0000-0000-0000-000000000001")
ROLE_ID = UUID("30000000-0000-0000-0000-000000000001")
TARGET_ROLE_ID = UUID("30000000-0000-0000-0000-000000000002")


class FakeUow(SimpleNamespace):
    """Expose injected repositories through the Unit-of-Work context API."""

    committed: bool = False

    async def __aenter__(self) -> FakeUow:
        return self

    async def __aexit__(self, *args: object) -> None:
        del args

    async def commit(self) -> None:
        self.committed = True


class FakeFactory:
    """Return one deterministic fake Unit of Work."""

    def __init__(self, uow: FakeUow) -> None:
        self.uow = uow

    def __call__(self) -> FakeUow:
        return self.uow


def _requester(*permissions: Permission) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=ACTOR_ID,
        session_id=SESSION_ID,
        username="admin",
        role_id=ROLE_ID,
        permissions=frozenset(permission.value for permission in permissions),
    )


def _user(
    identifier: UUID, role_id: UUID, *, enabled: bool = True, version: int = 1
) -> User:
    return User(
        id=identifier,
        created_at=NOW,
        updated_at=NOW,
        version=version,
        username=f"user-{identifier.int}",
        display_name="Test User",
        role_id=role_id,
        is_enabled=enabled,
        presence=PresenceState.OFFLINE,
    )


def _session() -> Session:
    return Session(
        id=SESSION_ID,
        created_at=NOW,
        updated_at=NOW,
        user_id=TARGET_ID,
        refresh_token_hash="hash",
        expires_at=NOW.replace(year=2027),
        idle_expires_at=NOW.replace(year=2027),
        ip_address="192.0.2.1",
        device_name="Desktop",
        platform="Windows",
        login_time=NOW,
    )


def _permissions() -> SimpleNamespace:
    return SimpleNamespace(require_authenticated_permission=AsyncMock())


def _audit_writer() -> SimpleNamespace:
    return SimpleNamespace(append=AsyncMock(return_value=SimpleNamespace(id=uuid4())))


@pytest.mark.asyncio
async def test_audit_writer_redacts_and_integrity_detects_chain_failures() -> None:
    repository = SimpleNamespace()
    repository.lock_chain_state = AsyncMock(return_value=AuditChainState(None, None, 0))
    repository.append = AsyncMock(side_effect=lambda event: event)
    event = await AuditWriter().append(
        repository,
        event_type="user.disabled",
        occurred_at=NOW,
        actor_id=ACTOR_ID,
        source_ip="192.0.2.1",
        severity=AuditSeverity.WARNING,
        details={"reason": "policy", "password": "never", "nested": {"token": "x"}},
    )
    assert event.sequence_number == 1
    assert event.details["password"] == "[redacted]"
    assert cast(dict[str, object], event.details["nested"])["token"] == "[redacted]"
    assert sanitise_audit_details({"plainText": "secret"}) == {
        "plainText": "[redacted]"
    }

    audit_repository = SimpleNamespace(
        get_latest_chain_state=AsyncMock(
            return_value=AuditChainState(event.id, event.event_hash, 1)
        ),
        verify_range_data=AsyncMock(return_value=[event]),
        get_by_sequence=AsyncMock(return_value=None),
    )
    service = AuditIntegrityService(
        cast(object, FakeFactory(FakeUow(audit=audit_repository))),
        clock=lambda: NOW,
    )
    assert (await service.verify(full=True)).valid
    audit_repository.get_latest_chain_state.return_value = AuditChainState(
        event.id, "0" * 64, 1
    )
    assert (await service.verify(full=True)).reason_code == "chain_state_mismatch"
    audit_repository.verify_range_data.return_value = []
    assert (await service.verify(full=True)).reason_code == "missing_sequence"


@pytest.mark.asyncio
async def test_audit_query_applies_limited_visibility() -> None:
    event_id = uuid4()
    canonical = build_canonical_audit_data(
        event_id=event_id,
        event_type="session.revoked",
        occurred_at=NOW,
        actor_id=ACTOR_ID,
        source_address=None,
        severity=AuditSeverity.WARNING,
        details={"reason": "private", "session_id": str(SESSION_ID)},
        previous_hash=None,
        sequence_number=1,
    )
    event = AuditEvent(
        event_id,
        "session.revoked",
        NOW,
        ACTOR_ID,
        None,
        AuditSeverity.WARNING,
        {"reason": "private", "session_id": str(SESSION_ID)},
        None,
        calculate_audit_hash(canonical),
        1,
    )
    repository = SimpleNamespace(
        list_events=AsyncMock(return_value=CursorPage((event,), "next"))
    )
    service = AuditService(
        cast(object, FakeFactory(FakeUow(audit=repository))),
        cast(object, _permissions()),
        AuditVisibilityFilter(),
    )
    response = await service.query(_requester(Permission.AUDIT_VIEW_LIMITED), limit=1)
    assert response.page.has_more
    assert "reason" not in response.events[0].details


@pytest.mark.asyncio
async def test_audit_integrity_recent_missing_predecessor_and_hash_mismatch() -> None:
    event_id = uuid4()
    event = AuditEvent(
        id=event_id,
        event_type="test",
        occurred_at=NOW,
        actor_id=None,
        source_address=None,
        severity=AuditSeverity.INFORMATIONAL,
        details={},
        previous_hash="a" * 64,
        event_hash="b" * 64,
        sequence_number=2,
    )
    repository = SimpleNamespace(
        get_latest_chain_state=AsyncMock(
            return_value=AuditChainState(event_id, event.event_hash, 2)
        ),
        verify_range_data=AsyncMock(return_value=[event]),
        get_by_sequence=AsyncMock(return_value=None),
    )
    service = AuditIntegrityService(
        cast(object, FakeFactory(FakeUow(audit=repository))), clock=lambda: NOW
    )
    missing = await service.verify(recent_count=1)
    assert missing.reason_code == "missing_sequence"
    predecessor = AuditEvent(
        id=uuid4(),
        event_type="first",
        occurred_at=NOW,
        actor_id=None,
        source_address=None,
        severity=AuditSeverity.INFORMATIONAL,
        details={},
        previous_hash=None,
        event_hash="a" * 64,
        sequence_number=1,
    )
    repository.get_by_sequence.return_value = predecessor
    mismatch = await service.verify(recent_count=1)
    assert mismatch.reason_code == "hash_mismatch"


def test_audit_domain_and_alert_invalid_transitions_are_rejected() -> None:
    with pytest.raises(ValueError):
        AuditChainState(None, None, -1)
    with pytest.raises(ValueError):
        AuditEvent(
            uuid4(),
            "",
            NOW,
            None,
            None,
            AuditSeverity.WARNING,
            {},
            None,
            "hash",
        )
    with pytest.raises(ValueError):
        SecurityAlert(
            id=uuid4(), created_at=NOW, updated_at=NOW, code="", summary="bad"
        )
    alert = SecurityAlert(
        id=uuid4(), created_at=NOW, updated_at=NOW, code="test", summary="test"
    )
    alert.acknowledge(ACTOR_ID, NOW)
    with pytest.raises(ValueError):
        alert.acknowledge(ACTOR_ID, NOW)
    alert.resolve(NOW, ACTOR_ID, "done")
    alert.resolve(NOW, ACTOR_ID, "duplicate")
    alert.recur(NOW)
    assert alert.state is SecurityAlertState.OPEN


def test_capabilities_and_role_policy_enforce_named_authority() -> None:
    capabilities = AdminService.capabilities(
        _requester(
            Permission.ADMIN_DASHBOARD,
            Permission.USER_DISABLE,
            Permission.AUDIT_VIEW,
            Permission.SYSTEM_MAINTENANCE,
        )
    )
    assert capabilities.can_open_admin and capabilities.can_manage_users
    assert capabilities.can_control_maintenance and not capabilities.can_run_workers
    policy = RoleAdministrationPolicy()
    admin = Role(ROLE_ID, "Administrator", frozenset({Permission.USER_ASSIGN_ROLE}))
    employee = Role(TARGET_ROLE_ID, "Employee")
    super_role = Role(uuid4(), "SuperAdministrator")
    assert policy.can_assign_role(admin, employee, employee)
    assert not policy.can_assign_role(admin, employee, super_role)
    assert not policy.can_disable_user(
        _user(ACTOR_ID, ROLE_ID), _user(ACTOR_ID, ROLE_ID), admin, 2
    )
    assert not policy.can_disable_user(
        _user(ACTOR_ID, ROLE_ID), _user(TARGET_ID, super_role.id), super_role, 1
    )
    assert policy.can_revoke_session(
        Role(uuid4(), "Admin", frozenset({Permission.SESSION_REVOKE})), employee
    )
    assert not policy.can_revoke_session(admin, super_role)


@pytest.mark.asyncio
async def test_user_administration_search_disable_enable_and_change_role() -> None:
    actor = _user(ACTOR_ID, ROLE_ID)
    target = _user(TARGET_ID, TARGET_ROLE_ID)
    admin_role = Role(
        ROLE_ID,
        "Administrator",
        frozenset(
            {
                Permission.USER_ASSIGN_ROLE,
                Permission.SESSION_REVOKE,
            }
        ),
    )
    employee_role = Role(TARGET_ROLE_ID, "Employee")
    helpdesk_role = Role(uuid4(), "Helpdesk")
    users = SimpleNamespace(
        search=AsyncMock(return_value=CursorPage((target,), None)),
        get_by_id=AsyncMock(side_effect=[actor, target, target, actor, target]),
        set_enabled=AsyncMock(return_value=True),
        set_role=AsyncMock(return_value=True),
    )
    authentication = SimpleNamespace(
        role_name=AsyncMock(return_value="Employee"),
        get_role=AsyncMock(
            side_effect=[employee_role, admin_role, employee_role, helpdesk_role]
        ),
        count_enabled_users_with_role=AsyncMock(return_value=2),
    )
    sessions = SimpleNamespace(
        list_active_for_user=AsyncMock(return_value=[]),
        invalidate_all_for_user=AsyncMock(return_value=2),
    )
    uow = FakeUow(
        users=users,
        authentication=authentication,
        sessions=sessions,
        audit=object(),
    )
    connections = SimpleNamespace(disconnect_user=AsyncMock(return_value=1))
    service = UserAdministrationService(
        cast(object, FakeFactory(uow)),
        cast(object, _permissions()),
        RoleAdministrationPolicy(),
        cast(object, connections),
        cast(object, _audit_writer()),
        lambda: NOW,
    )
    page = await service.search_users(_requester(Permission.USER_SEARCH), term="test")
    assert page.users[0].role == "Employee"
    disabled = await service.disable_user(
        _requester(Permission.USER_DISABLE),
        TARGET_ID,
        expected_version=1,
        reason="HR request",
    )
    assert not disabled.user.is_enabled and disabled.invalidated_sessions == 2
    target.is_enabled = False
    target.version = 2
    enabled = await service.enable_user(
        _requester(Permission.USER_ENABLE),
        TARGET_ID,
        expected_version=2,
        reason="HR reversal",
    )
    assert enabled.user.is_enabled
    target.version = 3
    changed = await service.change_role(
        _requester(Permission.USER_ASSIGN_ROLE),
        TARGET_ID,
        helpdesk_role.id,
        expected_version=3,
        reason="Support duties",
    )
    assert changed.user.role == "Helpdesk"
    assert connections.disconnect_user.await_count == 2


@pytest.mark.asyncio
async def test_session_and_connection_administration_commit_before_disconnect() -> None:
    actor = _user(ACTOR_ID, ROLE_ID)
    target = _user(TARGET_ID, TARGET_ROLE_ID)
    admin_role = Role(
        ROLE_ID,
        "Administrator",
        frozenset({Permission.SESSION_REVOKE}),
    )
    target_role = Role(TARGET_ROLE_ID, "Employee")
    session = _session()
    uow = FakeUow(
        users=SimpleNamespace(
            get_by_id=AsyncMock(side_effect=[actor, target, actor, target])
        ),
        authentication=SimpleNamespace(
            get_role=AsyncMock(
                side_effect=[admin_role, target_role, admin_role, target_role]
            )
        ),
        sessions=SimpleNamespace(
            list_active_for_user=AsyncMock(return_value=[session]),
            get_active=AsyncMock(return_value=session),
            invalidate=AsyncMock(return_value=True),
        ),
        audit=object(),
    )
    connection = SimpleNamespace(
        connection_id=uuid4(),
        user_id=TARGET_ID,
        session_id=SESSION_ID,
        connected_at=NOW,
        last_heartbeat=NOW,
    )
    connections = SimpleNamespace(
        disconnect_session=AsyncMock(return_value=1),
        list_connections=AsyncMock(return_value=(connection,)),
        disconnect_connection=AsyncMock(return_value=True),
    )
    session_service = SessionAdministrationService(
        cast(object, FakeFactory(uow)),
        cast(object, _permissions()),
        RoleAdministrationPolicy(),
        cast(object, connections),
        cast(object, _audit_writer()),
        lambda: NOW,
    )
    listed = await session_service.list_sessions(
        _requester(Permission.SESSION_VIEW), TARGET_ID
    )
    assert listed[0].device_name == "Desktop"
    revoked = await session_service.revoke_session(
        _requester(Permission.SESSION_REVOKE), SESSION_ID, "Lost device"
    )
    assert revoked.disconnected_connection_count == 1 and uow.committed
    connection_service = ConnectionAdministrationService(
        cast(object, FakeFactory(uow)),
        cast(object, _permissions()),
        cast(object, connections),
        cast(object, _audit_writer()),
        lambda: NOW,
    )
    assert (
        len((await connection_service.list_connections(_requester())).connections) == 1
    )
    assert await connection_service.disconnect_connection(
        _requester(), connection.connection_id, "Troubleshooting"
    )
    uow.sessions.invalidate.assert_awaited_once()


@pytest.mark.asyncio
async def test_alert_lifecycle_deduplicates_reopens_and_audits() -> None:
    repository = SimpleNamespace(
        get_open_by_code=AsyncMock(return_value=None),
        add=AsyncMock(),
        update=AsyncMock(),
        list_recent=AsyncMock(),
        get_by_id=AsyncMock(),
    )
    uow = FakeUow(security_alerts=repository, audit=object())
    service = SecurityAlertService(
        cast(object, FakeFactory(uow)),
        cast(object, _permissions()),
        cast(object, _audit_writer()),
        lambda: NOW,
    )
    created = await service.create_or_update(
        code="login_failures",
        title="Repeated failures",
        summary="Threshold exceeded",
        severity="warning",
        source_component="authentication",
    )
    alert = repository.add.await_args.args[0]
    assert created.occurrence_count == 1
    alert.resolve(NOW, ACTOR_ID, "Recovered")
    repository.get_open_by_code.return_value = alert
    recurrent = await service.create_or_update(
        code=alert.code,
        title=alert.title,
        summary=alert.summary,
        severity=alert.severity,
        source_component=alert.source_component,
    )
    assert recurrent.status == "open" and recurrent.occurrence_count == 2
    repository.list_recent.return_value = (alert,)
    assert len(await service.list_alerts(_requester(Permission.ALERT_VIEW))) == 1
    repository.get_by_id.return_value = alert
    acknowledged = await service.acknowledge(_requester(), alert.id, "Investigating")
    assert acknowledged.status == "acknowledged"
    resolved = await service.resolve(_requester(), alert.id, "Cause removed")
    assert resolved.status == "resolved"


@pytest.mark.asyncio
async def test_announcement_and_configuration_services_are_audited_and_versioned() -> (
    None
):
    announcement_repository = SimpleNamespace(
        add=AsyncMock(), get_by_id=AsyncMock(), update=AsyncMock()
    )
    configuration_repository = SimpleNamespace(
        get_latest=AsyncMock(return_value=None),
        append=AsyncMock(),
        list_history=AsyncMock(return_value=()),
    )
    uow = FakeUow(
        announcements=announcement_repository,
        configuration=configuration_repository,
        audit=object(),
    )
    audit = _audit_writer()
    announcements = AnnouncementService(
        cast(object, FakeFactory(uow)),
        cast(object, _permissions()),
        cast(object, audit),
        lambda: NOW,
    )
    published = await announcements.publish(
        _requester(Permission.ANNOUNCEMENT_MANAGE),
        CreateAnnouncementRequest(
            title="Maintenance",
            body="Planned maintenance tonight.",
            priority=AnnouncementPriority.IMPORTANT,
            target_type=AnnouncementTargetType.ALL_USERS,
        ),
    )
    announcement = announcement_repository.add.await_args.args[0]
    announcement_repository.get_by_id.return_value = announcement
    withdrawn = await announcements.withdraw(_requester(), published.id, "Rescheduled")
    assert withdrawn.id == published.id and announcement.withdrawn_at == NOW

    applied = Mock()
    configuration = ConfigurationService(
        cast(object, FakeFactory(uow)),
        cast(object, _permissions()),
        cast(object, audit),
        applied,
        lambda: NOW,
    )
    assert (await configuration.latest(_requester())).values == {}
    assert await configuration.history(_requester()) == ()
    updated = await configuration.update(
        _requester(Permission.CONFIGURATION_MODIFY),
        expected_revision=0,
        values={"messaging.edit_window_seconds": 600},
        reason="Policy update",
    )
    assert updated.revision == 1
    applied.assert_called_once_with({"messaging.edit_window_seconds": 600})
    configuration_repository.get_latest.return_value = SimpleNamespace(revision=2)
    with pytest.raises(ConflictError):
        await configuration.update(
            _requester(),
            expected_revision=1,
            values={"features.read_receipts": True},
            reason="Stale",
        )


@pytest.mark.asyncio
async def test_audit_export_is_generated_owned_and_sanitised(tmp_path: Path) -> None:
    event = AuditEvent(
        id=uuid4(),
        event_type="=formula",
        occurred_at=NOW,
        actor_id=ACTOR_ID,
        source_address=None,
        severity=AuditSeverity.WARNING,
        details={"password": "never", "reason": "review"},
        previous_hash=None,
        event_hash="a" * 64,
        sequence_number=1,
    )
    jobs: dict[UUID, tuple[DataExportJobResponse, UUID, datetime, str | None]] = {}

    async def add_job(
        job: DataExportJobResponse,
        *,
        requested_by: UUID,
        export_type: str,
        filters: dict[str, object],
        expires_at: datetime,
    ) -> None:
        del export_type, filters
        jobs[job.id] = (job, requested_by, expires_at, None)

    async def complete_job(
        job_id: UUID,
        *,
        completed_at: datetime,
        storage_reference: str | None,
        failure_code: str | None,
    ) -> None:
        job, owner, expiry, _ = jobs[job_id]
        jobs[job_id] = (
            job.model_copy(
                update={
                    "state": (
                        JobState.SUCCEEDED if failure_code is None else JobState.FAILED
                    ),
                    "completed_at": completed_at,
                    "failure_code": failure_code,
                }
            ),
            owner,
            expiry,
            storage_reference,
        )

    administration = SimpleNamespace(
        add_export_job=add_job,
        complete_export_job=complete_job,
        get_export_job=AsyncMock(side_effect=lambda identifier: jobs.get(identifier)),
    )
    audit = SimpleNamespace(
        get_latest_chain_state=AsyncMock(
            return_value=AuditChainState(event.id, event.event_hash, 1)
        ),
        list_range=AsyncMock(return_value=[event]),
    )
    service = AuditExportService(
        cast(object, FakeFactory(FakeUow(administration=administration, audit=audit))),
        cast(object, _permissions()),
        tmp_path,
        cast(object, _audit_writer()),
        lifetime=timedelta(hours=1),
        clock=lambda: NOW,
    )
    await service.start()
    job = await service.create(_requester(Permission.AUDIT_EXPORT), "csv")
    await service._queue.join()  # noqa: SLF001 - deterministic worker evidence
    completed = await service.get(_requester(Permission.AUDIT_EXPORT), job.id)
    path = await service.download_path(_requester(Permission.AUDIT_EXPORT), job.id)
    await service.stop()
    content = path.read_text(encoding="utf-8")
    assert completed.state is JobState.SUCCEEDED
    assert "'=formula" in content
    assert "never" not in content and "[redacted]" in content


@pytest.mark.asyncio
async def test_initial_local_administrator_is_hashed_and_audited() -> None:
    users = SimpleNamespace(
        get_by_normalised_username=AsyncMock(return_value=None),
        create=AsyncMock(side_effect=lambda user: user),
    )
    authentication = SimpleNamespace(
        count_enabled_users_with_role=AsyncMock(return_value=0),
        create_local_credential=AsyncMock(),
    )
    hasher = SimpleNamespace(hash_password=Mock(return_value="argon2id-hash"))
    uow = FakeUow(
        users=users,
        authentication=authentication,
        audit=SimpleNamespace(),
    )
    service = InitialAdministratorService(
        cast(object, FakeFactory(uow)),
        cast(object, _audit_writer()),
        cast(object, hasher),
    )
    identifier = await service.create_local(
        username="first-admin",
        display_name="First Admin",
        password=SecretStr("correct horse battery staple"),
    )
    assert identifier == users.create.await_args.args[0].id
    assert authentication.create_local_credential.await_args.args[0].password_hash == (
        "argon2id-hash"
    )
    assert uow.committed
    with pytest.raises(ValueError):
        await service.create_local(
            username="short", display_name="Short", password=SecretStr("too-short")
        )
    users.get_by_normalised_username.return_value = users.create.await_args.args[0]
    with pytest.raises(ConflictError):
        await service.create_local(
            username="first-admin",
            display_name="Duplicate",
            password=SecretStr("correct horse battery staple"),
        )


@pytest.mark.asyncio
async def test_initial_directory_administrator_is_validated_and_promoted() -> None:
    users = SimpleNamespace(
        get_by_directory_guid=AsyncMock(return_value=None),
        get_by_normalised_username=AsyncMock(return_value=None),
        create=AsyncMock(side_effect=lambda user: user),
        update=AsyncMock(side_effect=lambda user, **kwargs: user),
    )
    uow = FakeUow(
        users=users,
        authentication=SimpleNamespace(
            count_enabled_users_with_role=AsyncMock(return_value=0)
        ),
        audit=SimpleNamespace(),
    )
    service = InitialAdministratorService(
        cast(object, FakeFactory(uow)), cast(object, _audit_writer())
    )
    identity = DirectoryUser(
        username="directory-admin",
        display_name="Directory Admin",
        directory_guid="external-guid",
    )
    identifier = await service.create_directory(identity, AuthenticationSettings())
    assert identifier == users.create.await_args.args[0].id
    users.update.assert_awaited_once()
    assert uow.committed
    with pytest.raises(ConflictError):
        await service.create_directory(
            DirectoryUser(
                username="disabled", display_name="Disabled", is_enabled=False
            ),
            AuthenticationSettings(),
        )
    uow.authentication.count_enabled_users_with_role.return_value = 1
    with pytest.raises(ConflictError):
        await service.create_directory(identity, AuthenticationSettings())


@pytest.mark.asyncio
async def test_login_attempt_throttling_and_durable_failure_evidence() -> None:
    authentication = SimpleNamespace(
        count_recent_failures=AsyncMock(return_value=(0, 0)),
        add_login_attempt=AsyncMock(),
    )
    uow = FakeUow(authentication=authentication)
    service = LoginAttemptService(
        cast(object, FakeFactory(uow)),
        AuthenticationSettings(failed_login_limit=2),
        RateLimitSettings(login_requests_per_window=3),
        clock=lambda: NOW,
    )
    await service.require_allowed("Alice", "192.0.2.1")
    authentication.count_recent_failures.return_value = (2, 0)
    with pytest.raises(AccountLockedError):
        await service.require_allowed("Alice", "192.0.2.1")
    authentication.count_recent_failures.return_value = (0, 3)
    with pytest.raises(RateLimitError):
        await service.require_allowed("Alice", "192.0.2.1")
    await service.record_failure("Alice", "192.0.2.1", uuid4(), "invalid")
    assert (
        authentication.add_login_attempt.await_args.kwargs["normalised_username"]
        == "alice"
    )
    assert uow.committed


def test_administration_routes_cover_all_server_service_boundaries() -> None:
    """Every administrative endpoint delegates only through its service boundary."""
    event_id = uuid4()
    summary = AdminUserSummary(
        id=TARGET_ID,
        username="employee",
        display_name="Employee",
        role="Employee",
        is_enabled=True,
        active_sessions=0,
    )
    user_result = UserAdministrationResult(user=summary, audit_event_id=event_id)
    health = DetailedHealthResponse(
        status=HealthState.HEALTHY,
        timestamp=NOW,
        application_version="1.0",
        protocol_versions=(1,),
        components=(),
    )
    announcement = AnnouncementResponse(
        id=uuid4(),
        author_id=ACTOR_ID,
        title="Notice",
        body="Body",
        priority=AnnouncementPriority.NORMAL,
        target_type=AnnouncementTargetType.ALL_USERS,
        published_at=NOW,
    )
    export_job = DataExportJobResponse(
        id=uuid4(), state=JobState.QUEUED, requested_at=NOW
    )
    services = SimpleNamespace(
        admin=SimpleNamespace(
            capabilities=Mock(return_value=AdminService.capabilities(_requester()))
        ),
        dashboard=SimpleNamespace(
            build_dashboard=AsyncMock(
                return_value=AdminDashboardResponse(
                    connected_users=0,
                    messages_today=0,
                    active_uploads=0,
                    cpu_percent=0,
                    memory_percent=0,
                    disk_percent=0,
                    components=(),
                    generated_at=NOW,
                )
            )
        ),
        user_administration=SimpleNamespace(
            search_users=AsyncMock(
                return_value=AdminUserPageResponse(
                    users=(summary,), page=CursorPageMetadata(has_more=False)
                )
            ),
            disable_user=AsyncMock(return_value=user_result),
            enable_user=AsyncMock(return_value=user_result),
            change_role=AsyncMock(return_value=user_result),
        ),
        session_administration=SimpleNamespace(
            list_sessions=AsyncMock(return_value=()),
            revoke_session=AsyncMock(
                return_value=SessionRevocationResult(
                    session_id=SESSION_ID,
                    user_id=TARGET_ID,
                    invalidated_at=NOW,
                    disconnected_connection_count=0,
                    audit_event_id=event_id,
                )
            ),
        ),
        connection_administration=SimpleNamespace(
            list_connections=AsyncMock(
                return_value=ConnectionListResponse(connections=(), generated_at=NOW)
            ),
            disconnect_connection=AsyncMock(return_value=True),
        ),
        audit=SimpleNamespace(
            query=AsyncMock(
                return_value=AuditPageResponse(
                    events=(), page=CursorPageMetadata(has_more=False)
                )
            )
        ),
        audit_integrity=SimpleNamespace(
            verify=AsyncMock(
                return_value=AuditVerificationResponse(
                    valid=True, mode="recent", checked_events=0, verified_at=NOW
                )
            )
        ),
        alerts=SimpleNamespace(
            list_alerts=AsyncMock(return_value=()),
            acknowledge=AsyncMock(
                return_value=SecurityAlertResponse(
                    id=uuid4(),
                    alert_type="test",
                    severity="warning",
                    summary="Test",
                    created_at=NOW,
                )
            ),
            resolve=AsyncMock(
                return_value=SecurityAlertResponse(
                    id=uuid4(),
                    alert_type="test",
                    severity="warning",
                    summary="Test",
                    created_at=NOW,
                    status="resolved",
                )
            ),
        ),
        monitoring=SimpleNamespace(get_detailed_health=AsyncMock(return_value=health)),
        workers=SimpleNamespace(
            list_workers=AsyncMock(
                return_value=WorkerListResponse(workers=(), generated_at=NOW)
            ),
            run_worker_now=AsyncMock(
                return_value=WorkerStatusResponse(
                    name="outbox", state=JobState.SUCCEEDED
                )
            ),
        ),
        configuration=SimpleNamespace(
            latest=AsyncMock(
                return_value=ConfigurationSummary(revision=1, values={}, updated_at=NOW)
            ),
            update=AsyncMock(
                return_value=ConfigurationSummary(revision=2, values={}, updated_at=NOW)
            ),
            history=AsyncMock(return_value=()),
        ),
        announcements=SimpleNamespace(
            publish=AsyncMock(return_value=announcement),
            withdraw=AsyncMock(return_value=announcement),
        ),
        maintenance=SimpleNamespace(
            view_state=AsyncMock(
                return_value=MaintenanceStateResponse(
                    state=MaintenanceState.NORMAL, changed_at=NOW
                )
            ),
            change_state=AsyncMock(
                return_value=MaintenanceStateResponse(
                    state=MaintenanceState.READ_ONLY, changed_at=NOW
                )
            ),
        ),
        diagnostics=SimpleNamespace(
            run=AsyncMock(
                return_value=ServerDiagnosticReport(
                    generated_at=NOW,
                    checks=(
                        DiagnosticCheckResult(
                            name="database", state="healthy", duration_ms=1
                        ),
                    ),
                )
            )
        ),
        exports=SimpleNamespace(
            create=AsyncMock(return_value=export_job),
            get=AsyncMock(return_value=export_job),
            download_path=AsyncMock(),
        ),
    )
    app = FastAPI()
    app.state.container = SimpleNamespace(services=services)
    app.include_router(router)
    app.dependency_overrides[current_authenticated_user] = lambda: _requester()
    client = TestClient(app)
    reason = {"reason": "Required", "expected_user_version": 1}
    assert client.get("/api/v1/admin/capabilities").status_code == 200
    assert client.get("/api/v1/admin/dashboard").status_code == 200
    assert client.get("/api/v1/admin/users").status_code == 200
    assert (
        client.post(f"/api/v1/admin/users/{TARGET_ID}/disable", json=reason).status_code
        == 200
    )
    assert (
        client.post(f"/api/v1/admin/users/{TARGET_ID}/enable", json=reason).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/admin/users/{TARGET_ID}/role",
            json={**reason, "role_id": str(TARGET_ROLE_ID)},
        ).status_code
        == 200
    )
    assert client.get(f"/api/v1/admin/users/{TARGET_ID}/sessions").status_code == 200
    assert (
        client.post(
            f"/api/v1/admin/sessions/{SESSION_ID}/revoke", json={"reason": "Lost"}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/admin/connections").status_code == 200
    assert (
        client.post(
            f"/api/v1/admin/connections/{uuid4()}/disconnect",
            json={"reason": "Reset"},
        ).status_code
        == 200
    )
    assert client.get("/api/v1/admin/audit").status_code == 200
    assert client.post("/api/v1/admin/audit/verify").status_code == 200
    assert client.get("/api/v1/admin/alerts").status_code == 200
    alert_id = uuid4()
    assert (
        client.post(
            f"/api/v1/admin/alerts/{alert_id}/acknowledge", json={"notes": "Review"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/admin/alerts/{alert_id}/resolve", json={"notes": "Fixed"}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/admin/health").status_code == 200
    assert client.get("/api/v1/admin/workers").status_code == 200
    assert (
        client.post(
            "/api/v1/admin/workers/outbox/run", json={"reason": "Retry"}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/admin/configuration").status_code == 200
    assert client.get("/api/v1/admin/configuration/history").status_code == 200
    assert (
        client.post(
            "/api/v1/admin/configuration",
            json={"expected_revision": 1, "values": {}, "reason": "Review"},
        ).status_code
        == 200
    )
    announcement_request = {
        "title": "Notice",
        "body": "Body",
        "target_type": "all_users",
    }
    assert (
        client.post(
            "/api/v1/admin/announcements", json=announcement_request
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/admin/announcements/{announcement.id}/withdraw",
            json={"reason": "Done"},
        ).status_code
        == 200
    )
    assert client.get("/api/v1/admin/maintenance").status_code == 200
    assert (
        client.post(
            "/api/v1/admin/maintenance",
            json={"state": "read_only", "reason": "Upgrade"},
        ).status_code
        == 200
    )
    assert client.get("/api/v1/admin/diagnostics?checks=database").status_code == 200
    assert client.post("/api/v1/admin/exports?export_format=json").status_code == 202
    assert client.get(f"/api/v1/admin/exports/{export_job.id}").status_code == 200
