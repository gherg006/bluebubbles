"""Direct and group conversation API contracts."""

import unicodedata
from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.constants import MAX_GROUP_NAME_LENGTH
from bluebubbles.shared.models.users import UserSummary


class ConversationType(StrEnum):
    """Distinguish direct and group conversations."""

    DIRECT = "direct"
    GROUP = "group"
    SYSTEM = "system"


class GroupRole(StrEnum):
    """Represent a member's authority within a group conversation."""

    OWNER = "owner"
    MODERATOR = "moderator"
    ADMIN = "moderator"  # Backwards-compatible source alias.
    MEMBER = "member"


class ConversationParticipantResponse(ContractModel):
    """Return public participant information and group role."""

    user: UserSummary
    role: GroupRole = GroupRole.MEMBER
    joined_at: datetime


class ConversationSummaryResponse(ContractModel):
    """Return list-level conversation metadata without message plaintext."""

    id: UUID
    type: ConversationType
    title: (
        Annotated[str, Field(min_length=1, max_length=MAX_GROUP_NAME_LENGTH)] | None
    ) = None
    participants: tuple[UserSummary, ...]
    last_activity: datetime
    unread_count: Annotated[int, Field(ge=0)] = 0
    archived: bool = False


class ConversationResponse(ConversationSummaryResponse):
    """Return complete client-visible conversation metadata."""

    created_by: UUID
    created_at: datetime
    participant_details: tuple[ConversationParticipantResponse, ...]
    description: Annotated[str, Field(max_length=1000)] | None = None


class CreateDirectConversationRequest(ContractModel):
    """Create a direct conversation with another user."""

    target_user_id: UUID


class CreateGroupConversationRequest(ContractModel):
    """Create a named group with unique initial members."""

    name: Annotated[str, Field(min_length=1, max_length=MAX_GROUP_NAME_LENGTH)]
    member_ids: Annotated[tuple[UUID, ...], Field(min_length=1, max_length=249)]
    description: Annotated[str, Field(max_length=500)] | None = None

    @field_validator("name")
    @classmethod
    def _normalise_name(cls, value: str) -> str:
        return _normalise_group_name(value)

    @model_validator(mode="after")
    def _unique_members(self) -> "CreateGroupConversationRequest":
        if len(set(self.member_ids)) != len(self.member_ids):
            raise ValueError("Group members must be unique")
        return self


class UpdateGroupRequest(ContractModel):
    """Patch group metadata; omitted and explicitly cleared fields remain distinct."""

    name: (
        Annotated[str, Field(min_length=1, max_length=MAX_GROUP_NAME_LENGTH)] | None
    ) = None
    description: Annotated[str, Field(max_length=500)] | None = None

    @field_validator("name")
    @classmethod
    def _normalise_name(cls, value: str | None) -> str | None:
        return _normalise_group_name(value) if value is not None else None

    @model_validator(mode="after")
    def _require_change(self) -> "UpdateGroupRequest":
        if not self.model_fields_set:
            raise ValueError("At least one group field is required")
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("Group name cannot be cleared")
        return self


class AddGroupMemberRequest(ContractModel):
    """Add one user to a group."""

    user_id: UUID


class ChangeGroupRoleRequest(ContractModel):
    """Assign a non-owner group role to one member."""

    user_id: UUID
    role: GroupRole

    @model_validator(mode="after")
    def _reject_owner_assignment(self) -> "ChangeGroupRoleRequest":
        if self.role is GroupRole.OWNER:
            raise ValueError("Use TransferOwnershipRequest to assign the owner role")
        return self


class TransferOwnershipRequest(ContractModel):
    """Transfer group ownership to an existing member."""

    new_owner_id: UUID


class ArchiveConversationRequest(ContractModel):
    """Set the authenticated member's private archive preference."""

    archived: bool = True


def _normalise_group_name(value: str) -> str:
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise ValueError("Group names cannot contain control characters")
    normalised = " ".join(value.split())
    if not normalised:
        raise ValueError("Group name is required")
    return normalised
