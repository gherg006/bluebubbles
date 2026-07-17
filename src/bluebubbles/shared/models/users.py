"""API-facing user summaries, profiles, searches, and public keys."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import Field, model_validator

from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.constants import MAX_DISPLAY_NAME_LENGTH, MAX_STATUS_LENGTH
from bluebubbles.shared.models.pagination import CursorPageMetadata, PageRequest
from bluebubbles.shared.security.key_models import PublicKeyDescriptor


class PresenceState(StrEnum):
    """Represent a user-visible presence state."""

    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    OFFLINE = "offline"
    INVISIBLE = "invisible"


class UserSummary(ContractModel):
    """Expose the minimum user identity needed in lists."""

    id: UUID
    username: Annotated[str, Field(min_length=1, max_length=128)]
    display_name: Annotated[
        str, Field(min_length=1, max_length=MAX_DISPLAY_NAME_LENGTH)
    ]
    department: Annotated[str, Field(max_length=100)] | None = None
    presence: PresenceState = PresenceState.OFFLINE
    avatar_url: Annotated[str, Field(max_length=2048)] | None = None


class UserProfileResponse(UserSummary):
    """Return a client-safe user profile."""

    email: Annotated[str, Field(max_length=320)] | None = None
    job_title: Annotated[str, Field(max_length=100)] | None = None
    status_message: Annotated[str, Field(max_length=MAX_STATUS_LENGTH)] | None = None
    role: Annotated[str, Field(min_length=1, max_length=100)]
    is_enabled: bool
    last_login: datetime | None = None


class UpdateUserProfileRequest(ContractModel):
    """Update only client-editable profile fields."""

    display_name: (
        Annotated[str, Field(min_length=1, max_length=MAX_DISPLAY_NAME_LENGTH)] | None
    ) = None
    status_message: Annotated[str, Field(max_length=MAX_STATUS_LENGTH)] | None = None
    avatar: Annotated[str, Field(max_length=500)] | None = None

    @model_validator(mode="after")
    def _require_change(self) -> "UpdateUserProfileRequest":
        if not self.model_fields_set:
            raise ValueError("At least one profile field is required")
        if "display_name" in self.model_fields_set and self.display_name is None:
            raise ValueError("Display name cannot be cleared")
        return self


class UserSearchRequest(PageRequest):
    """Search users by safe public fields."""

    query: Annotated[str, Field(min_length=1, max_length=100)]
    department: Annotated[str, Field(min_length=1, max_length=100)] | None = None


class UserSearchResponse(ContractModel):
    """Return a cursor page of matching users."""

    users: tuple[UserSummary, ...]
    page: CursorPageMetadata


class PublicUserKeyResponse(ContractModel):
    """Return active public keys and no private-key material."""

    user_id: UUID
    keys: tuple[PublicKeyDescriptor, ...]
