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
    severity: str = "warning"
    title: str = "Security alert"
    source_component: str = "application"
    occurrence_count: int = 1
    acknowledged_by: UUID | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    resolved_by: UUID | None = None
    resolution_notes: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if (
            not self.code.strip()
            or not self.summary.strip()
            or self.occurrence_count < 1
        ):
            raise ValueError(
                "Alert code, summary and positive occurrence count required"
            )

    def acknowledge(self, administrator_id: UUID, at: datetime) -> None:
        """Acknowledge an open alert."""
        if self.state is not SecurityAlertState.OPEN:
            raise ValueError("Only an open alert can be acknowledged")
        self.state = SecurityAlertState.ACKNOWLEDGED
        self.acknowledged_by = administrator_id
        self.acknowledged_at = at
        self.touch(at)

    def resolve(
        self,
        at: datetime,
        administrator_id: UUID | None = None,
        notes: str | None = None,
    ) -> None:
        """Resolve an open or acknowledged alert."""
        if self.state is SecurityAlertState.RESOLVED:
            return
        self.state = SecurityAlertState.RESOLVED
        self.resolved_at = at
        self.resolved_by = administrator_id
        self.resolution_notes = notes
        self.touch(at)

    def recur(self, at: datetime) -> None:
        """Increment a deduplicated alert and reopen a resolved occurrence."""
        self.occurrence_count += 1
        if self.state is SecurityAlertState.RESOLVED:
            self.state = SecurityAlertState.OPEN
            self.resolved_at = None
            self.resolved_by = None
            self.resolution_notes = None
        self.touch(at)
