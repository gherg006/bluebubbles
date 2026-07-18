"""Authorised detailed monitoring and dashboard aggregation services."""

from collections.abc import Callable
from datetime import UTC, datetime

from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission
from bluebubbles.server.monitoring.health import HealthAggregator
from bluebubbles.server.monitoring.metrics import MetricsService
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.shared.models.administration import AdminDashboardResponse
from bluebubbles.shared.models.health import DetailedHealthResponse


class MonitoringService:
    """Expose detailed dependency health only after current permission checks."""

    def __init__(
        self, health: HealthAggregator, permission_service: PermissionService
    ) -> None:
        self._health = health
        self._permissions = permission_service

    async def get_detailed_health(
        self, requester: AuthenticatedUser
    ) -> DetailedHealthResponse:
        """Return safe component detail to an authorised administrator."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.HEALTH_VIEW_DETAILED
        )
        return await self._health.detailed_health()


class AdminDashboardService:
    """Build one timestamped aggregate operational dashboard snapshot."""

    def __init__(
        self,
        metrics_service: MetricsService,
        monitoring_service: MonitoringService,
        permission_service: PermissionService,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._metrics = metrics_service
        self._monitoring = monitoring_service
        self._permissions = permission_service
        self._clock = clock

    async def build_dashboard(
        self, requester: AuthenticatedUser
    ) -> AdminDashboardResponse:
        """Aggregate current health and metrics without inspecting user content."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.ADMIN_DASHBOARD
        )
        metrics = await self._metrics.snapshot()
        health = await self._monitoring.get_detailed_health(requester)
        return AdminDashboardResponse(
            connected_users=metrics.connected_users,
            messages_today=0,
            active_uploads=0,
            cpu_percent=metrics.cpu_percent,
            memory_percent=metrics.memory_percent,
            disk_percent=metrics.disk_percent,
            components=health.components,
            generated_at=self._clock(),
        )
