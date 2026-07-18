"""Security-alert repository protocol."""

from typing import Protocol
from uuid import UUID

from bluebubbles.server.domain.alerts import SecurityAlert


class SecurityAlertRepository(Protocol):
    """Define deduplicated alert persistence without transition policy."""

    async def get_by_id(
        self, alert_id: UUID, *, for_update: bool = False
    ) -> SecurityAlert | None: ...
    async def get_open_by_code(
        self, code: str, *, for_update: bool = False
    ) -> SecurityAlert | None: ...
    async def add(self, alert: SecurityAlert) -> SecurityAlert: ...
    async def update(
        self, alert: SecurityAlert, *, expected_version: int
    ) -> SecurityAlert: ...
    async def list_recent(self, *, limit: int) -> tuple[SecurityAlert, ...]: ...
