"""Server-side conversation membership and ownership domain rules."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from bluebubbles.server.domain.common import BaseEntity
from bluebubbles.shared.models.conversations import ConversationType, GroupRole


class ConversationEventType(StrEnum):
    """Name server-visible conversation membership events."""

    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"
    ROLE_CHANGED = "role_changed"
    OWNERSHIP_TRANSFERRED = "ownership_transferred"
    RENAMED = "renamed"
    GROUP_CREATED = "group_created"
    MEMBER_LEFT = "member_left"
    CONVERSATION_CREATED = "conversation_created"


@dataclass(kw_only=True)
class ConversationMember(BaseEntity):
    """Represent one user's current or historical conversation membership."""

    conversation_id: UUID
    user_id: UUID
    role: GroupRole = GroupRole.MEMBER
    joined_at: datetime
    left_at: datetime | None = None
    is_muted: bool = False
    is_pinned: bool = False
    is_archived: bool = False

    @property
    def active(self) -> bool:
        """Return whether the membership currently grants conversation access."""
        return self.left_at is None and not self.is_deleted

    def leave(self, at: datetime) -> None:
        """Close an active membership exactly once."""
        if at.tzinfo is None:
            raise ValueError("Leave timestamp must be timezone-aware")
        if self.left_at is None:
            self.left_at = at
            self.touch(at)


@dataclass(kw_only=True)
class Conversation(BaseEntity):
    """Represent server-visible conversation metadata and memberships."""

    conversation_type: ConversationType
    created_by: UUID
    last_activity: datetime
    title: str | None = None
    description: str | None = None
    archived: bool = False
    members: dict[UUID, ConversationMember] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.last_activity.tzinfo is None:
            raise ValueError("Last activity must be timezone-aware")
        if (
            self.conversation_type is ConversationType.GROUP
            and not (self.title or "").strip()
        ):
            raise ValueError("Group conversations require a title")
        if self.title is not None:
            self.title = _normalise_title(self.title)

    def active_member(self, user_id: UUID) -> ConversationMember | None:
        """Return the active membership for ``user_id`` if one exists."""
        member = self.members.get(user_id)
        return member if member is not None and member.active else None

    def rename(self, title: str, at: datetime) -> None:
        """Rename a group conversation."""
        if self.conversation_type is not ConversationType.GROUP:
            raise ValueError("Direct conversations cannot be renamed")
        self.title = _normalise_title(title)
        self.last_activity = at
        self.touch(at)

    def add_member(self, member: ConversationMember, at: datetime) -> None:
        """Add a member while preventing duplicate active membership."""
        if member.conversation_id != self.id:
            raise ValueError("Membership belongs to a different conversation")
        if self.active_member(member.user_id) is not None:
            raise ValueError("User is already an active member")
        self.members[member.user_id] = member
        self.last_activity = at
        self.touch(at)

    def remove_member(self, user_id: UUID, at: datetime) -> None:
        """Remove a member without allowing the current owner to disappear."""
        member = self.active_member(user_id)
        if member is None:
            raise ValueError("User is not an active member")
        if member.role is GroupRole.OWNER:
            raise ValueError("Transfer ownership before removing the owner")
        member.leave(at)
        self.last_activity = at
        self.touch(at)

    def transfer_ownership(
        self, current_owner_id: UUID, target_id: UUID, at: datetime
    ) -> None:
        """Atomically transfer ownership between active group members."""
        current = self.active_member(current_owner_id)
        target = self.active_member(target_id)
        validate_group_owner_transition(current, target)
        assert current is not None and target is not None
        current.role = GroupRole.MODERATOR
        target.role = GroupRole.OWNER
        current.touch(at)
        target.touch(at)
        self.last_activity = at
        self.touch(at)


@dataclass(frozen=True, slots=True)
class DirectConversationPair:
    """Store an order-independent pair used to enforce direct uniqueness."""

    first_user_id: UUID
    second_user_id: UUID

    def __post_init__(self) -> None:
        if self.first_user_id == self.second_user_id:
            raise ValueError("A direct conversation requires two distinct users")

    @classmethod
    def create(cls, user_one: UUID, user_two: UUID) -> DirectConversationPair:
        """Return a deterministically ordered direct-conversation pair."""
        first, second = sorted((user_one, user_two), key=str)
        return cls(first, second)

    def contains(self, user_id: UUID) -> bool:
        """Return whether the user belongs to this pair."""
        return user_id in (self.first_user_id, self.second_user_id)

    def other_user(self, user_id: UUID) -> UUID:
        """Return the other participant or reject a non-member."""
        if user_id == self.first_user_id:
            return self.second_user_id
        if user_id == self.second_user_id:
            return self.first_user_id
        raise ValueError("User is not part of this direct conversation")


@dataclass(kw_only=True)
class ConversationEvent(BaseEntity):
    """Record safe, server-visible conversation metadata changes."""

    conversation_id: UUID
    event_type: ConversationEventType
    actor_id: UUID
    subject_id: UUID | None
    occurred_at: datetime


def is_active_member(conversation: Conversation, user_id: UUID) -> bool:
    """Return whether a user currently belongs to a conversation."""
    return conversation.active_member(user_id) is not None


def can_add_member(conversation: Conversation, actor_id: UUID) -> bool:
    """Return whether an active owner or administrator may add a member."""
    actor = conversation.active_member(actor_id)
    return actor is not None and actor.role in {GroupRole.OWNER, GroupRole.MODERATOR}


def can_remove_member(
    conversation: Conversation, actor_id: UUID, target_id: UUID
) -> bool:
    """Return whether ``actor_id`` may remove ``target_id``."""
    actor = conversation.active_member(actor_id)
    target = conversation.active_member(target_id)
    if actor is None or target is None or target.role is GroupRole.OWNER:
        return False
    return actor_id == target_id or actor.role in {
        GroupRole.OWNER,
        GroupRole.MODERATOR,
    }


def can_transfer_ownership(
    conversation: Conversation, actor_id: UUID, target_id: UUID
) -> bool:
    """Return whether an owner can transfer to another active member."""
    actor = conversation.active_member(actor_id)
    target = conversation.active_member(target_id)
    return (
        actor is not None
        and actor.role is GroupRole.OWNER
        and target is not None
        and actor_id != target_id
    )


def validate_group_owner_transition(
    current: ConversationMember | None, target: ConversationMember | None
) -> None:
    """Validate a group ownership transition without repository access."""
    if current is None or current.role is not GroupRole.OWNER:
        raise ValueError("Current owner membership is required")
    if target is None or target.user_id == current.user_id:
        raise ValueError("Ownership target must be another active member")


def _normalise_title(value: str) -> str:
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise ValueError("Conversation titles cannot contain control characters")
    normalised = " ".join(value.split())
    if not normalised:
        raise ValueError("Conversation title is required")
    return normalised
