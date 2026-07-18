"""Explicit ownership and lifecycle boundary for server-wide dependencies."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from bluebubbles.server.configuration.settings import ServerSettings
from bluebubbles.server.database.engine import DatabaseManager
from bluebubbles.server.database.unit_of_work import (
    ServerRepositories,
    UnitOfWorkFactory,
)
from bluebubbles.server.monitoring.health import HealthAggregator
from bluebubbles.server.monitoring.storage import StorageHealthCheck
from bluebubbles.server.redis import RedisManager
from bluebubbles.server.services.administration import (
    AdminService,
    ConnectionAdministrationService,
    SessionAdministrationService,
    UserAdministrationService,
)
from bluebubbles.server.services.alerts import SecurityAlertService
from bluebubbles.server.services.announcements import AnnouncementService
from bluebubbles.server.services.attachments import AttachmentService
from bluebubbles.server.services.audit import AuditIntegrityService, AuditService
from bluebubbles.server.services.authentication import AuthenticationService
from bluebubbles.server.services.configuration import ConfigurationService
from bluebubbles.server.services.contacts import ContactService
from bluebubbles.server.services.conversations import ConversationService
from bluebubbles.server.services.diagnostics import ServerDiagnosticService
from bluebubbles.server.services.exports import AuditExportService
from bluebubbles.server.services.groups import GroupService
from bluebubbles.server.services.keys import PublicKeyService
from bluebubbles.server.services.maintenance import MaintenanceService
from bluebubbles.server.services.messaging import MessagingService
from bluebubbles.server.services.monitoring import (
    AdminDashboardService,
    MonitoringService,
)
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.server.services.sessions import SessionService
from bluebubbles.server.services.users import UserService
from bluebubbles.server.websocket.dispatcher import (
    WebSocketEventDispatcher,
    WebSocketRateLimiter,
)
from bluebubbles.server.websocket.manager import WebSocketConnectionManager
from bluebubbles.server.workers.manager import WorkerManager
from bluebubbles.shared.models.health import DetailedHealthResponse

__all__ = [
    "LifecycleComponent",
    "ServerContainer",
    "ServerRepositories",
    "ServerServices",
]


class LifecycleComponent(Protocol):
    """Define application-owned asynchronous startup and cleanup."""

    async def start(self) -> None:
        """Start and validate this component."""
        ...

    async def stop(self) -> None:
        """Release this component's resources idempotently."""
        ...


@dataclass(frozen=True, slots=True)
class ServerServices:
    """Group constructed application services without hiding dependencies."""

    health: HealthAggregator
    authentication: AuthenticationService | None = None
    sessions: SessionService | None = None
    permissions: PermissionService | None = None
    users: UserService | None = None
    contacts: ContactService | None = None
    public_keys: PublicKeyService | None = None
    conversations: ConversationService | None = None
    groups: GroupService | None = None
    messaging: MessagingService | None = None
    attachments: AttachmentService | None = None
    admin: AdminService | None = None
    user_administration: UserAdministrationService | None = None
    session_administration: SessionAdministrationService | None = None
    connection_administration: ConnectionAdministrationService | None = None
    audit: AuditService | None = None
    audit_integrity: AuditIntegrityService | None = None
    alerts: SecurityAlertService | None = None
    announcements: AnnouncementService | None = None
    configuration: ConfigurationService | None = None
    monitoring: MonitoringService | None = None
    dashboard: AdminDashboardService | None = None
    maintenance: MaintenanceService | None = None
    diagnostics: ServerDiagnosticService | None = None
    workers: WorkerManager | None = None
    exports: AuditExportService | None = None


class ServerContainer:
    """Own application-wide dependencies and their ordered lifecycle."""

    def __init__(
        self,
        settings: ServerSettings,
        database_manager: DatabaseManager,
        redis_manager: RedisManager,
        storage_health: StorageHealthCheck,
        unit_of_work_factory: UnitOfWorkFactory,
        services: ServerServices,
        logger: logging.Logger,
        *,
        additional_components: Sequence[LifecycleComponent] = (),
        websocket_manager: WebSocketConnectionManager | None = None,
        websocket_dispatcher: WebSocketEventDispatcher | None = None,
    ) -> None:
        """Store explicit singletons without starting external resources.

        Additional components provide the ordered seam for future WebSocket and
        worker stages. They are real injected lifecycle objects, never placeholders.
        """
        self.settings = settings
        self.database_manager = database_manager
        self.redis_manager = redis_manager
        self.storage_health = storage_health
        self.unit_of_work_factory = unit_of_work_factory
        self.services = services
        self.websocket_manager = websocket_manager or WebSocketConnectionManager()
        self.websocket_dispatcher = websocket_dispatcher or WebSocketEventDispatcher(
            {}, WebSocketRateLimiter(1), {1}
        )
        self._logger = logger
        self._components: tuple[LifecycleComponent, ...] = (
            database_manager,
            redis_manager,
            storage_health,
            *additional_components,
        )
        self._started_components: list[LifecycleComponent] = []
        self._started = False
        self._stopping = False
        self._start_lock = asyncio.Lock()

    @property
    def started(self) -> bool:
        """Report whether every required lifecycle component started."""
        return self._started

    @property
    def stopping(self) -> bool:
        """Report whether graceful cleanup is currently running."""
        return self._stopping

    async def start(self) -> None:
        """Start dependencies in order and roll back a partial startup.

        Duplicate successful starts are idempotent. A failed stage stops that stage
        and every earlier stage in reverse order before re-raising the safe error.
        """
        async with self._start_lock:
            if self._started:
                return
            if self._stopping:
                raise RuntimeError("Server container is stopping")
            self._started_components.clear()
            try:
                for component in self._components:
                    self._started_components.append(component)
                    await component.start()
            except BaseException:
                await self._stop_started_components()
                raise
            self._started = True

    async def stop(self) -> None:
        """Attempt every reverse-order cleanup stage; repeated calls are safe."""
        async with self._start_lock:
            if self._stopping:
                return
            if not self._started_components:
                self._started = False
                return
            self._stopping = True
            self._started = False
            try:
                await self._stop_started_components()
            finally:
                self._stopping = False

    async def get_health(self) -> DetailedHealthResponse:
        """Return safe component health for an authorised future API boundary."""
        return await self.services.health.detailed_health()

    async def _stop_started_components(self) -> None:
        components = tuple(reversed(self._started_components))
        self._started_components.clear()
        for component in components:
            try:
                await component.stop()
            except BaseException as error:
                self._logger.error(
                    "Server component cleanup failed",
                    extra={"failure_category": type(error).__name__},
                )
        self._started = False
