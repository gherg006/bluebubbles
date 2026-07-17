"""Validated data models corresponding to Version 1 WebSocket event types."""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import Field, SecretStr

from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.errors.models import WebSocketErrorEventData
from bluebubbles.shared.models.announcements import AnnouncementResponse
from bluebubbles.shared.models.messages import EncryptedMessageResponse
from bluebubbles.shared.models.users import PresenceState
from bluebubbles.shared.security.key_models import PublicKeyType


class AuthenticationEventData(ContractModel):
    """Authenticate a socket using an application access token."""

    access_token: SecretStr


class AuthenticatedEventData(ContractModel):
    """Confirm socket authentication and identify the bound session."""

    user_id: UUID
    session_id: UUID


class HeartbeatEventData(ContractModel):
    """Carry heartbeat timing without mutable connection state."""

    sent_at: datetime


class MessageReceivedEventData(ContractModel):
    """Deliver one recipient-specific encrypted message."""

    message: EncryptedMessageResponse


class MessageUpdatedEventData(MessageReceivedEventData):
    """Deliver replacement encrypted fields for an edited message."""


class MessageDeletedEventData(ContractModel):
    """Notify a client that a message was soft-deleted."""

    message_id: UUID
    conversation_id: UUID
    deleted_at: datetime


class MessageStatusEventData(ContractModel):
    """Report delivery or read progress for one encrypted message."""

    message_id: UUID
    conversation_id: UUID
    user_id: UUID
    occurred_at: datetime


class TypingEventData(ContractModel):
    """Report transient typing state without transmitting draft content."""

    conversation_id: UUID
    user_id: UUID
    is_typing: bool


class PresenceEventData(ContractModel):
    """Report a user's visible presence state."""

    user_id: UUID
    state: PresenceState
    changed_at: datetime
    status_message: Annotated[str, Field(max_length=280)] | None = None


class GroupMembershipEventData(ContractModel):
    """Report addition or removal of a group member."""

    conversation_id: UUID
    user_id: UUID
    actor_id: UUID
    changed_at: datetime


class ConversationChangedEventData(ContractModel):
    """Report creation or metadata/role changes without message content."""

    conversation_id: UUID
    actor_id: UUID
    user_id: UUID | None = None
    changed_at: datetime


class PublicKeyChangedEventData(ContractModel):
    """Tell clients to invalidate one user's cached public-key purpose."""

    user_id: UUID
    key_type: PublicKeyType
    key_version: Annotated[int, Field(ge=1)]
    fingerprint: Annotated[str, Field(min_length=1, max_length=128)]
    changed_at: datetime


class SessionRevokedEventData(ContractModel):
    """Notify a client that an application session is no longer valid."""

    session_id: UUID
    revoked_at: datetime
    reason: Annotated[str, Field(min_length=1, max_length=500)]


class PolicyUpdatedEventData(ContractModel):
    """Notify clients to refresh server-visible policies."""

    revision: Annotated[int, Field(ge=1)]
    changed_keys: tuple[str, ...]


class AnnouncementPublishedEventData(ContractModel):
    """Deliver one newly visible plain-text announcement."""

    announcement: AnnouncementResponse


class ServerShutdownEventData(ContractModel):
    """Announce a controlled shutdown and optional reconnect delay."""

    reason: Annotated[str, Field(min_length=1, max_length=500)]
    reconnect_after_seconds: Annotated[int, Field(ge=0)] | None = None


EVENT_DATA_MODELS: dict[str, type[ContractModel]] = {
    "AUTHENTICATE": AuthenticationEventData,
    "AUTHENTICATED": AuthenticatedEventData,
    "HEARTBEAT": HeartbeatEventData,
    "MESSAGE_RECEIVED": MessageReceivedEventData,
    "MESSAGE_UPDATED": MessageUpdatedEventData,
    "MESSAGE_DELETED": MessageDeletedEventData,
    "MESSAGE_DELIVERED": MessageStatusEventData,
    "MESSAGE_READ": MessageStatusEventData,
    "TYPING_CHANGED": TypingEventData,
    "PRESENCE_CHANGED": PresenceEventData,
    "GROUP_MEMBER_ADDED": GroupMembershipEventData,
    "GROUP_MEMBER_REMOVED": GroupMembershipEventData,
    "CONVERSATION_CREATED": ConversationChangedEventData,
    "GROUP_UPDATED": ConversationChangedEventData,
    "GROUP_ROLE_UPDATED": ConversationChangedEventData,
    "KEY_CHANGED": PublicKeyChangedEventData,
    "SESSION_REVOKED": SessionRevokedEventData,
    "ANNOUNCEMENT_PUBLISHED": AnnouncementPublishedEventData,
    "POLICY_UPDATED": PolicyUpdatedEventData,
    "SERVER_SHUTDOWN": ServerShutdownEventData,
    "ERROR": WebSocketErrorEventData,
}


def validate_event_data(event_type: str, data: dict[str, Any]) -> ContractModel:
    """Validate data against its registered event model.

    Raises:
        ValueError: If no event-data contract is registered.
        pydantic.ValidationError: If ``data`` violates the registered contract.
    """
    model = EVENT_DATA_MODELS.get(event_type)
    if model is None:
        raise ValueError(f"No data model registered for event type: {event_type}")
    return model.model_validate(data)
