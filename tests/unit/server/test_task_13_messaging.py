"""Task 13 encrypted-message transaction and authorisation evidence."""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from bluebubbles.server.configuration.settings import MessagingSettings
from bluebubbles.server.domain.conversations import Conversation, ConversationMember
from bluebubbles.server.domain.messages import Message, MessageDelivery
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.repositories.types import CursorPage, MessagePageQuery
from bluebubbles.server.services.events import EventFactory
from bluebubbles.server.services.messaging import (
    MessageEnvelopeValidator,
    MessagingService,
)
from bluebubbles.shared.errors.exceptions import (
    AuthorisationError,
    ConflictError,
    ProtocolError,
    ResourceNotFoundError,
    ValidationError,
)
from bluebubbles.shared.models.conversations import ConversationType, GroupRole
from bluebubbles.shared.models.messages import (
    EditMessageRequest,
    MarkConversationReadRequest,
    MessageDeliveryStatus,
    MessageType,
    RecipientKeyEnvelopeRequest,
    SendMessageRequest,
)
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    KeyEnvelopeAlgorithm,
    SignatureAlgorithm,
)

NOW = datetime.now(UTC)


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _key(user_id: UUID) -> RecipientKeyEnvelopeRequest:
    return RecipientKeyEnvelopeRequest(
        recipient_id=user_id,
        key_version=1,
        algorithm=KeyEnvelopeAlgorithm.X25519_HKDF_SHA256_AES_256_GCM_V1,
        ephemeral_public_key=_b64(b"p" * 32),
        nonce=_b64(b"n" * 12),
        encrypted_key=_b64(b"wrapped-key"),
    )


def _request(
    conversation_id: UUID,
    users: tuple[UUID, ...],
    *,
    message_id: UUID | None = None,
    protocol_version: int = 1,
) -> SendMessageRequest:
    return SendMessageRequest(
        client_message_id=message_id or uuid4(),
        conversation_id=conversation_id,
        message_type=MessageType.TEXT,
        content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
        ciphertext=_b64(b"ciphertext-and-tag"),
        nonce=_b64(b"m" * 12),
        signature_algorithm=SignatureAlgorithm.ED25519_V1,
        signature=_b64(b"s" * 64),
        sender_key_version=1,
        protocol_version=protocol_version,
        client_created_at=NOW,
        encrypted_keys=tuple(_key(user) for user in users),
    )


class _Messages:
    def __init__(self) -> None:
        self.items: dict[UUID, Message] = {}
        self.deliveries: dict[tuple[UUID, UUID], MessageDeliveryStatus] = {}

    async def get_existing_idempotent_message(
        self, message_id: UUID, sender_id: UUID
    ) -> Message | None:
        item = self.items.get(message_id)
        return item if item is not None and item.sender_id == sender_id else None

    async def create(self, message: Message) -> Message:
        self.items[message.id] = message
        return message

    async def create_delivery_rows(
        self, deliveries: tuple[MessageDelivery, ...]
    ) -> None:
        for item in deliveries:
            self.deliveries[(item.message_id, item.recipient_id)] = item.status

    async def get_by_id(
        self, message_id: UUID, *, for_update: bool = False
    ) -> Message | None:
        del for_update
        return self.items.get(message_id)

    async def get_for_user(self, message_id: UUID, user_id: UUID) -> Message | None:
        item = self.items.get(message_id)
        if item is None or user_id not in {
            key.recipient_id for key in item.recipient_keys
        }:
            return None
        return item

    async def list_for_conversation(
        self, query: MessagePageQuery
    ) -> CursorPage[Message]:
        conversation_id = query.conversation_id
        return CursorPage(
            tuple(
                item
                for item in self.items.values()
                if item.conversation_id == conversation_id
            ),
            None,
        )

    async def update_encrypted_payload(
        self, message: Message, *, expected_version: int
    ) -> Message:
        assert message.version == expected_version + 1
        self.items[message.id] = message
        return message

    async def soft_delete(
        self, message_id: UUID, deleted_at: datetime, *, expected_version: int
    ) -> bool:
        item = self.items.get(message_id)
        return (
            item is not None
            and item.version == expected_version
            and deleted_at.tzinfo is not None
        )

    async def update_delivery_state(
        self,
        message_id: UUID,
        recipient_id: UUID,
        state: MessageDeliveryStatus,
        at: datetime,
    ) -> bool:
        assert at.tzinfo is not None
        self.deliveries[(message_id, recipient_id)] = state
        return True


class _Conversations:
    def __init__(
        self, conversation: Conversation, members: list[ConversationMember]
    ) -> None:
        self.conversation = conversation
        self.members = members

    async def get_by_id(
        self, conversation_id: UUID, *, for_update: bool = False
    ) -> Conversation | None:
        del for_update
        return self.conversation if conversation_id == self.conversation.id else None

    async def get_active_members(
        self, conversation_id: UUID, *, for_update: bool = False
    ) -> list[ConversationMember]:
        del for_update
        return self.members if conversation_id == self.conversation.id else []

    async def get_active_membership(
        self,
        conversation_id: UUID,
        user_id: UUID,
        *,
        for_update: bool = False,
    ) -> ConversationMember | None:
        del for_update
        return next(
            (
                item
                for item in self.members
                if item.conversation_id == conversation_id and item.user_id == user_id
            ),
            None,
        )

    async def update_last_activity(
        self, conversation_id: UUID, last_activity: datetime, *, expected_version: int
    ) -> bool:
        return (
            conversation_id == self.conversation.id
            and expected_version == self.conversation.version
            and last_activity.tzinfo is not None
        )


class _Outbox:
    def __init__(self) -> None:
        self.events: list[object] = []

    async def add(self, event: object) -> object:
        self.events.append(event)
        return event


class _Uow:
    def __init__(
        self, conversations: _Conversations, messages: _Messages, outbox: _Outbox
    ) -> None:
        self.conversations = conversations
        self.messages = messages
        self.outbox = outbox
        self.audit = object()
        self.commits = 0

    async def __aenter__(self) -> _Uow:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1


class _Factory:
    def __init__(self, uow: _Uow) -> None:
        self.uow = uow

    def __call__(self) -> _Uow:
        return self.uow


class _Permissions:
    def __init__(self) -> None:
        self.denied = False

    async def require_authenticated_permission(
        self, user: object, permission: object
    ) -> None:
        del user, permission
        if self.denied:
            raise AuthorisationError()


class _Audit:
    def __init__(self) -> None:
        self.events: list[str] = []

    async def append(self, repository: object, **values: object) -> None:
        del repository
        self.events.append(str(values["event_type"]))


def _service() -> tuple[MessagingService, _Uow, _Permissions, UUID, UUID, UUID]:
    sender, recipient, conversation_id = uuid4(), uuid4(), uuid4()
    conversation = Conversation(
        id=conversation_id,
        created_at=NOW - timedelta(minutes=1),
        updated_at=NOW - timedelta(minutes=1),
        conversation_type=ConversationType.DIRECT,
        created_by=sender,
        last_activity=NOW - timedelta(minutes=1),
    )
    members = [
        ConversationMember(
            id=uuid4(),
            created_at=NOW - timedelta(minutes=1),
            updated_at=NOW - timedelta(minutes=1),
            conversation_id=conversation_id,
            user_id=user,
            role=GroupRole.MEMBER,
            joined_at=NOW - timedelta(minutes=1),
        )
        for user in (sender, recipient)
    ]
    messages, outbox = _Messages(), _Outbox()
    uow = _Uow(_Conversations(conversation, members), messages, outbox)
    permissions = _Permissions()
    settings = MessagingSettings(maximum_encrypted_request_bytes=4096)
    service = MessagingService(
        _Factory(uow),  # type: ignore[arg-type]
        permissions,  # type: ignore[arg-type]
        _Audit(),  # type: ignore[arg-type]
        EventFactory(),
        MessageEnvelopeValidator(settings, {1}),
        settings,
    )
    return service, uow, permissions, sender, recipient, conversation_id


def _authenticated(user_id: UUID) -> AuthenticatedUser:
    return AuthenticatedUser(user_id, uuid4(), "user", uuid4(), frozenset())


@pytest.mark.asyncio
async def test_send_commits_message_audit_delivery_and_outbox_idempotently() -> None:
    service, uow, _, sender, recipient, conversation_id = _service()
    request = _request(conversation_id, (sender, recipient))
    result = await service.send_message(_authenticated(sender), request)
    assert result.message.id == request.client_message_id
    assert (
        uow.messages.deliveries[(request.client_message_id, recipient)]
        is MessageDeliveryStatus.STORED
    )
    assert len(uow.outbox.events) == 1
    duplicate = await service.send_message(_authenticated(sender), request)
    assert duplicate.duplicate is True
    assert len(uow.messages.items) == 1


@pytest.mark.asyncio
async def test_send_rejects_permission_membership_keys_protocol_and_conflict() -> None:
    service, uow, permissions, sender, recipient, conversation_id = _service()
    permissions.denied = True
    with pytest.raises(AuthorisationError):
        await service.send_message(
            _authenticated(sender), _request(conversation_id, (sender, recipient))
        )
    permissions.denied = False
    with pytest.raises(ValidationError, match="every active"):
        await service.send_message(
            _authenticated(sender), _request(conversation_id, (sender,))
        )
    with pytest.raises(ProtocolError):
        await service.send_message(
            _authenticated(sender),
            _request(conversation_id, (sender, recipient), protocol_version=2),
        )
    message_id = uuid4()
    first = _request(conversation_id, (sender, recipient), message_id=message_id)
    await service.send_message(_authenticated(sender), first)
    changed = first.model_copy(update={"ciphertext": _b64(b"different")})
    with pytest.raises(ConflictError, match="already in use"):
        await service.send_message(_authenticated(sender), changed)
    uow.conversations.members = [
        item for item in uow.conversations.members if item.user_id != sender
    ]
    with pytest.raises(AuthorisationError):
        await service.send_message(
            _authenticated(sender), _request(conversation_id, (recipient,))
        )


@pytest.mark.asyncio
async def test_list_edit_delete_and_delivery_lifecycle() -> None:
    service, uow, _, sender, recipient, conversation_id = _service()
    request = _request(conversation_id, (sender, recipient))
    sent = await service.send_message(_authenticated(sender), request)
    page = await service.list_messages(
        _authenticated(recipient), conversation_id, None, 50
    )
    assert page.messages[0].encrypted_key.recipient_id == recipient
    edit = EditMessageRequest(
        ciphertext=_b64(b"new-ciphertext"),
        nonce=_b64(b"e" * 12),
        signature=_b64(b"t" * 64),
        encrypted_keys=tuple(_key(user) for user in (sender, recipient)),
        expected_version=sent.message.version,
        sender_key_version=1,
    )
    edited = await service.edit_message(_authenticated(sender), sent.message.id, edit)
    assert edited.version == 2
    with pytest.raises(ConflictError, match="changed"):
        await service.edit_message(_authenticated(sender), sent.message.id, edit)
    with pytest.raises(AuthorisationError):
        await service.edit_message(
            _authenticated(recipient),
            sent.message.id,
            edit.model_copy(update={"expected_version": 2}),
        )
    await service.acknowledge_delivery(recipient, sent.message.id, conversation_id, NOW)
    await service.mark_read_by_user_id(
        recipient,
        MarkConversationReadRequest(
            conversation_id=conversation_id, through_message_id=sent.message.id
        ),
    )
    assert (
        uow.messages.deliveries[(sent.message.id, recipient)]
        is MessageDeliveryStatus.READ
    )
    deleted = await service.delete_message(
        _authenticated(sender), sent.message.id, expected_version=2
    )
    assert deleted.is_deleted and deleted.version == 3


@pytest.mark.asyncio
async def test_history_and_acknowledgements_hide_unrelated_resources() -> None:
    service, _, _, sender, recipient, conversation_id = _service()
    outsider = uuid4()
    sent = await service.send_message(
        _authenticated(sender), _request(conversation_id, (sender, recipient))
    )
    with pytest.raises(ResourceNotFoundError):
        await service.list_messages(_authenticated(outsider), conversation_id, None, 50)
    with pytest.raises(ResourceNotFoundError):
        await service.acknowledge_delivery(
            outsider, sent.message.id, conversation_id, NOW
        )


def test_envelope_validator_rejects_size_digest_and_recipient_limit() -> None:
    sender, recipient, conversation_id = uuid4(), uuid4(), uuid4()
    request = _request(conversation_id, (sender, recipient))
    MessageEnvelopeValidator(MessagingSettings(), {1}).validate(request)
    with pytest.raises(ValidationError, match="too large"):
        MessageEnvelopeValidator(
            MessagingSettings(maximum_encrypted_request_bytes=10), {1}
        ).validate(request)
    invalid = request.model_copy(update={"recipient_envelope_digest": _b64(b"x" * 32)})
    with pytest.raises(ValidationError, match="digest"):
        MessageEnvelopeValidator(MessagingSettings(), {1}).validate(invalid)
