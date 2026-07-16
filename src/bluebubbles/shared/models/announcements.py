"""Safe plain-text announcement request and response contracts."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator

from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.constants import MAX_ANNOUNCEMENT_LENGTH
from bluebubbles.shared.models.pagination import CursorPageMetadata


class AnnouncementPriority(StrEnum):
    """Classify announcement urgency."""

    NORMAL = "normal"
    IMPORTANT = "important"
    URGENT = "urgent"


class AnnouncementTargetType(StrEnum):
    """Identify the population targeted by an announcement."""

    ALL_USERS = "all_users"
    DEPARTMENT = "department"
    GROUP = "group"


class CreateAnnouncementRequest(ContractModel):
    """Create a validated plain-text announcement."""

    title: Annotated[str, Field(min_length=1, max_length=200)]
    body: Annotated[str, Field(min_length=1, max_length=MAX_ANNOUNCEMENT_LENGTH)]
    priority: AnnouncementPriority = AnnouncementPriority.NORMAL
    target_type: AnnouncementTargetType
    target_ids: tuple[UUID, ...] = ()
    expires_at: datetime | None = None

    @field_validator("title", "body")
    @classmethod
    def _reject_control_characters(cls, value: str) -> str:
        if any(
            ord(character) < 32 and character not in "\r\n\t" for character in value
        ):
            raise ValueError("Announcement text contains control characters")
        return value


class AnnouncementResponse(ContractModel):
    """Return a published announcement and acknowledgement state."""

    id: UUID
    author_id: UUID
    title: str
    body: str
    priority: AnnouncementPriority
    target_type: AnnouncementTargetType
    published_at: datetime
    expires_at: datetime | None = None
    acknowledged_at: datetime | None = None


class AnnouncementAcknowledgementRequest(ContractModel):
    """Acknowledge one visible announcement as the authenticated user."""

    announcement_id: UUID


class AnnouncementListResponse(ContractModel):
    """Return a cursor page of visible announcements."""

    announcements: tuple[AnnouncementResponse, ...]
    page: CursorPageMetadata
