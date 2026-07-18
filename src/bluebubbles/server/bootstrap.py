"""Server dependency construction and startup validation boundary."""

from datetime import UTC, datetime, timedelta

from bluebubbles.server.authentication.directory_sync import (
    DirectorySynchronisationService,
)
from bluebubbles.server.authentication.ldap_provider import LDAPAuthenticationProvider
from bluebubbles.server.authentication.local_provider import LocalAuthenticationProvider
from bluebubbles.server.authentication.mock_provider import MockAuthenticationProvider
from bluebubbles.server.authentication.password_hashing import PasswordHasher
from bluebubbles.server.authentication.providers import AuthenticationProvider
from bluebubbles.server.authentication.tokens import TokenManager
from bluebubbles.server.configuration.settings import (
    AuthenticationProviderName,
    ServerSettings,
)
from bluebubbles.server.configuration.validation import validate_server_settings
from bluebubbles.server.container import ServerContainer, ServerServices
from bluebubbles.server.database.engine import DatabaseManager
from bluebubbles.server.database.unit_of_work import (
    SqlAlchemyRepositoryFactory,
    UnitOfWorkFactory,
)
from bluebubbles.server.monitoring.checks import (
    BackupStatusHealthCheck,
    OutboxHealthCheck,
    TLSCertificateHealthCheck,
    WebSocketHealthCheck,
    WorkerHealthCheck,
)
from bluebubbles.server.monitoring.health import HealthAggregator
from bluebubbles.server.monitoring.metrics import MetricsService
from bluebubbles.server.monitoring.storage import StorageHealthCheck
from bluebubbles.server.redis import RedisManager
from bluebubbles.server.services.administration import (
    AdminService,
    ConnectionAdministrationService,
    RoleAdministrationPolicy,
    SessionAdministrationService,
    UserAdministrationService,
)
from bluebubbles.server.services.alerts import SecurityAlertService
from bluebubbles.server.services.announcements import AnnouncementService
from bluebubbles.server.services.attachments import AttachmentService
from bluebubbles.server.services.audit import (
    AuditIntegrityService,
    AuditService,
    AuthenticationAuditWriter,
)
from bluebubbles.server.services.authentication import AuthenticationService
from bluebubbles.server.services.configuration import ConfigurationService
from bluebubbles.server.services.contacts import ContactService
from bluebubbles.server.services.conversations import ConversationService
from bluebubbles.server.services.diagnostics import ServerDiagnosticService
from bluebubbles.server.services.events import EventFactory
from bluebubbles.server.services.exports import AuditExportService
from bluebubbles.server.services.groups import GroupService
from bluebubbles.server.services.keys import PublicKeyService
from bluebubbles.server.services.login_attempts import LoginAttemptService
from bluebubbles.server.services.maintenance import MaintenanceService
from bluebubbles.server.services.messaging import (
    MessageEnvelopeValidator,
    MessagingService,
)
from bluebubbles.server.services.monitoring import (
    AdminDashboardService,
    MonitoringService,
)
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.server.services.sessions import SessionService
from bluebubbles.server.services.users import UserService
from bluebubbles.server.storage import (
    AttachmentPathBuilder,
    ChecksumService,
    LocalFileStorage,
)
from bluebubbles.server.websocket.dispatcher import (
    WebSocketEventDispatcher,
    WebSocketRateLimiter,
)
from bluebubbles.server.websocket.handlers import WebSocketHandlers
from bluebubbles.server.websocket.manager import WebSocketConnectionManager
from bluebubbles.server.websocket.publisher import EventPublisher
from bluebubbles.server.workers.base import BackgroundWorker
from bluebubbles.server.workers.manager import WorkerManager
from bluebubbles.server.workers.outbox import OutboxPublisherWorker
from bluebubbles.shared.logging import configure_logging


def build_server_container(settings: ServerSettings) -> ServerContainer:
    """Validate settings and construct each application singleton explicitly."""
    validate_startup_dependencies(settings)
    logger = configure_logging(settings.logging.level.value)
    database_manager = DatabaseManager(settings.database, logger)
    redis_manager = RedisManager(settings.redis, logger)
    storage_health = StorageHealthCheck(settings.storage, logger)
    unit_of_work_factory = UnitOfWorkFactory(
        database_manager.create_session, SqlAlchemyRepositoryFactory()
    )
    websocket_manager = WebSocketConnectionManager()
    audit_writer = AuthenticationAuditWriter()
    token_manager = TokenManager(settings.tokens)
    session_service = SessionService(
        unit_of_work_factory,
        token_manager,
        settings.tokens,
        audit_writer,
        notifier=websocket_manager,
    )
    provider_name = settings.authentication.provider
    authentication_provider: AuthenticationProvider
    if provider_name is AuthenticationProviderName.DIRECTORY:
        authentication_provider = LDAPAuthenticationProvider(settings.directory)
    elif provider_name is AuthenticationProviderName.LOCAL:
        authentication_provider = LocalAuthenticationProvider(
            unit_of_work_factory,
            PasswordHasher(),
            enabled=settings.authentication.allow_local_accounts,
        )
    else:
        authentication_provider = MockAuthenticationProvider({})
    login_attempt_service = LoginAttemptService(
        unit_of_work_factory,
        settings.authentication,
        settings.rate_limits,
    )
    authentication_service = AuthenticationService(
        authentication_provider,
        unit_of_work_factory,
        session_service,
        login_attempt_service,
        DirectorySynchronisationService(settings.authentication),
        audit_writer,
        settings.authentication,
        settings.directory,
    )
    permission_service = PermissionService(unit_of_work_factory)
    checksum_service = ChecksumService()
    attachment_storage = LocalFileStorage(
        AttachmentPathBuilder(
            settings.storage.root_path, settings.storage.temporary_path
        ),
        checksum_service,
    )
    attachment_service = AttachmentService(
        unit_of_work_factory,
        permission_service,
        attachment_storage,
        checksum_service,
        audit_writer,
        settings.attachments,
        settings.storage,
    )
    user_service = UserService(unit_of_work_factory)
    contact_service = ContactService(unit_of_work_factory)
    public_key_service = PublicKeyService(unit_of_work_factory, audit_writer)
    conversation_service = ConversationService(
        unit_of_work_factory,
        permission_service,
        audit_writer,
        maximum_group_members=settings.messaging.maximum_group_members,
    )
    group_service = GroupService(
        unit_of_work_factory,
        permission_service,
        audit_writer,
        maximum_group_members=settings.messaging.maximum_group_members,
    )
    event_factory = EventFactory(settings.protocol.current_version)
    messaging_service = MessagingService(
        unit_of_work_factory,
        permission_service,
        audit_writer,
        event_factory,
        MessageEnvelopeValidator(
            settings.messaging, set(settings.protocol.supported_versions)
        ),
        settings.messaging,
    )
    event_publisher = EventPublisher(websocket_manager)
    websocket_handlers = WebSocketHandlers(
        unit_of_work_factory, messaging_service, event_publisher
    )
    websocket_dispatcher = WebSocketEventDispatcher(
        websocket_handlers.mapping(),
        WebSocketRateLimiter(settings.rate_limits.websocket_events_per_minute),
        set(settings.protocol.supported_versions),
    )
    outbox_worker = OutboxPublisherWorker(
        unit_of_work_factory, event_publisher, settings.workers, logger
    )
    audit_integrity = AuditIntegrityService(unit_of_work_factory, permission_service)

    async def clean_expired_sessions() -> int:
        async with unit_of_work_factory() as unit_of_work:
            removed = await unit_of_work.sessions.delete_expired(
                datetime.now(UTC), limit=500
            )
            await unit_of_work.commit()
        return removed

    async def verify_recent_audit_chain() -> int:
        result = await audit_integrity.verify(full=False)
        if not result.valid:
            raise RuntimeError("audit_integrity_failed")
        return result.checked_events

    session_cleanup_worker = BackgroundWorker(
        "session_cleanup",
        settings.workers.session_cleanup_interval_seconds,
        clean_expired_sessions,
    )
    audit_verification_worker = BackgroundWorker(
        "audit_verification",
        settings.workers.audit_recent_check_interval_seconds,
        verify_recent_audit_chain,
        pausable=False,
    )
    worker_manager = WorkerManager(
        (outbox_worker, session_cleanup_worker, audit_verification_worker),
        unit_of_work_factory,
        permission_service,
        audit_writer,
    )
    tls_health = TLSCertificateHealthCheck(
        settings.tls.certificate_path, enabled=settings.tls.enabled
    )
    outbox_health = OutboxHealthCheck(unit_of_work_factory)
    worker_health = WorkerHealthCheck(
        worker_manager,
        repeated_failure_threshold=settings.monitoring.repeated_failure_alert_threshold,
    )
    websocket_health = WebSocketHealthCheck(websocket_manager)
    backup_health = BackupStatusHealthCheck(
        settings.monitoring.backup_status_path,
        maximum_age=timedelta(hours=settings.monitoring.backup_maximum_age_hours),
    )
    health = HealthAggregator(
        (
            database_manager,
            redis_manager,
            storage_health,
            authentication_provider,
            tls_health,
            outbox_health,
            worker_health,
            websocket_health,
            backup_health,
        ),
        timeout_seconds=float(
            min(
                settings.database.connection_timeout_seconds,
                settings.redis.operation_timeout_seconds,
            )
        ),
        application_version=settings.application.version,
        protocol_versions=settings.protocol.supported_versions,
        latency_warning_ms={
            "database": settings.monitoring.database_latency_warning_ms,
            "redis": settings.monitoring.redis_latency_warning_ms,
        },
    )
    role_policy = RoleAdministrationPolicy()
    audit_service = AuditService(unit_of_work_factory, permission_service)
    monitoring_service = MonitoringService(health, permission_service)
    metrics_service = MetricsService(websocket_manager, settings.storage.root_path)
    dashboard_service = AdminDashboardService(
        metrics_service, monitoring_service, permission_service
    )
    maintenance_service = MaintenanceService(
        unit_of_work_factory,
        permission_service,
        health.detailed_health,
        audit_writer,
    )
    diagnostic_service = ServerDiagnosticService(
        {
            "database": database_manager,
            "redis": redis_manager,
            "storage": storage_health,
            "directory": authentication_provider,
            "tls": tls_health,
            "outbox": outbox_health,
            "workers": worker_health,
            "websocket": websocket_health,
            "backup": backup_health,
        },
        permission_service,
    )
    export_service = AuditExportService(
        unit_of_work_factory,
        permission_service,
        settings.storage.export_path,
        audit_writer,
        lifetime=timedelta(hours=settings.retention.export_file_hours),
    )
    user_administration = UserAdministrationService(
        unit_of_work_factory,
        permission_service,
        role_policy,
        websocket_manager,
        audit_writer,
    )
    session_administration = SessionAdministrationService(
        unit_of_work_factory,
        permission_service,
        role_policy,
        websocket_manager,
        audit_writer,
    )
    connection_administration = ConnectionAdministrationService(
        unit_of_work_factory,
        permission_service,
        websocket_manager,
        audit_writer,
    )
    return ServerContainer(
        settings=settings,
        database_manager=database_manager,
        redis_manager=redis_manager,
        storage_health=storage_health,
        unit_of_work_factory=unit_of_work_factory,
        services=ServerServices(
            health=health,
            authentication=authentication_service,
            sessions=session_service,
            permissions=permission_service,
            users=user_service,
            contacts=contact_service,
            public_keys=public_key_service,
            conversations=conversation_service,
            groups=group_service,
            messaging=messaging_service,
            attachments=attachment_service,
            admin=AdminService(),
            user_administration=user_administration,
            session_administration=session_administration,
            connection_administration=connection_administration,
            audit=audit_service,
            audit_integrity=audit_integrity,
            alerts=SecurityAlertService(
                unit_of_work_factory, permission_service, audit_writer
            ),
            announcements=AnnouncementService(
                unit_of_work_factory, permission_service, audit_writer
            ),
            configuration=ConfigurationService(
                unit_of_work_factory, permission_service, audit_writer
            ),
            monitoring=monitoring_service,
            dashboard=dashboard_service,
            maintenance=maintenance_service,
            diagnostics=diagnostic_service,
            workers=worker_manager,
            exports=export_service,
        ),
        logger=logger,
        websocket_manager=websocket_manager,
        websocket_dispatcher=websocket_dispatcher,
        additional_components=(websocket_manager, worker_manager, export_service),
    )


def validate_startup_dependencies(settings: ServerSettings) -> None:
    """Fail before construction when cross-setting safety checks do not pass."""
    validate_server_settings(settings)


async def run_startup_checks(container: ServerContainer) -> None:
    """Run the complete ordered dependency verification through the container."""
    await container.start()


async def verify_migration_state(database_manager: DatabaseManager) -> None:
    """Connect and verify that PostgreSQL is at the application-compatible head."""
    await database_manager.start()


async def verify_storage_paths(storage_health: StorageHealthCheck) -> None:
    """Verify configured encrypted-file storage writability and reserves."""
    await storage_health.start()
