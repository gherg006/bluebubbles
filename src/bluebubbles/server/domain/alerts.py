"""Server security-alert lifecycle model."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from bluebubbles.server.domain.common import BaseEntity


class SecurityAlertState(StrEnum):
    """Define the review lifecycle of a security alert."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass(kw_only=True)
class SecurityAlert(BaseEntity):
    """Represent safe diagnostic metadata requiring administrator review."""

    code: str
    summary: str
    state: SecurityAlertState = SecurityAlertState.OPEN
    acknowledged_by: UUID | None = None
    resolved_at: datetime | None = None

    def acknowledge(self, administrator_id: UUID, at: datetime) -> None:
        """Acknowledge an open alert."""
        if self.state is not SecurityAlertState.OPEN:
            raise ValueError("Only an open alert can be acknowledged")
        self.state = SecurityAlertState.ACKNOWLEDGED
        self.acknowledged_by = administrator_id
        self.touch(at)

    def resolve(self, at: datetime) -> None:
        """Resolve an open or acknowledged alert."""
        if self.state is SecurityAlertState.RESOLVED:
            return
        self.state = SecurityAlertState.RESOLVED
        self.resolved_at = at
        self.touch(at)
