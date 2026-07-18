"""Audited in-process maintenance state and write-availability guard."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from uuid import UUID

from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.audit import AuditSeverity
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission
from bluebubbles.server.services.audit import AuditWriter
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.shared.errors.exceptions import ConflictError
from bluebubbles.shared.models.administration import (
    MaintenanceState,
    MaintenanceStateResponse,
)
from bluebubbles.shared.models.health import DetailedHealthResponse, HealthState


class MaintenanceService:
    """Own controlled server maintenance transitions without global mutable state."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        health_provider: Callable[[], Awaitable[DetailedHealthResponse]],
        audit_writer: AuditWriter | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._uow_factory = unit_of_work_factory
        self._permissions = permission_service
        self._health_provider = health_provider
        self._audit = audit_writer or AuditWriter()
        self._clock = clock
        self._state = MaintenanceState.NORMAL
        self._changed_at = clock()
        self._changed_by: UUID | None = None
        self._lock = asyncio.Lock()

    def get_state(self) -> MaintenanceStateResponse:
        """Return the current state without exposing transition reasons."""
        return MaintenanceStateResponse(
            state=self._state,
            changed_at=self._changed_at,
            changed_by=self._changed_by,
        )

    async def view_state(
        self, requester: AuthenticatedUser
    ) -> MaintenanceStateResponse:
        """Return state only to an administrator with maintenance authority."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.SYSTEM_MAINTENANCE
        )
        return self.get_state()

    async def change_state(
        self,
        requester: AuthenticatedUser,
        state: MaintenanceState,
        reason: str,
    ) -> MaintenanceStateResponse:
        """Commit an audited transition and require healthy dependencies to exit."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.SYSTEM_MAINTENANCE
        )
        reason = reason.strip()
        if not reason or len(reason) > 1000:
            raise ValueError("A maintenance reason is required")
        async with self._lock:
            if (
                state is MaintenanceState.NORMAL
                and self._state is not MaintenanceState.NORMAL
            ):
                health = await self._health_provider()
                if (
                    getattr(health, "status", HealthState.UNHEALTHY)
                    is HealthState.UNHEALTHY
                ):
                    raise ConflictError(
                        user_message=(
                            "Maintenance cannot end while dependencies are unhealthy."
                        )
                    )
            now = self._clock()
            async with self._uow_factory() as uow:
                await self._audit.append(
                    uow.audit,
                    event_type="system.maintenance_changed",
                    occurred_at=now,
                    actor_id=requester.user_id,
                    source_ip=None,
                    severity=AuditSeverity.WARNING,
                    details={
                        "previous_state": self._state.value,
                        "new_state": state.value,
                        "reason": reason,
                    },
                )
                await uow.commit()
            self._state = state
            self._changed_at = now
            self._changed_by = requester.user_id
            return self.get_state()

    def require_write_available(self) -> None:
        """Reject ordinary writes whenever either maintenance mode is active."""
        if self._state is not MaintenanceState.NORMAL:
            raise ConflictError(
                user_message="The server is currently in maintenance mode."
            )
