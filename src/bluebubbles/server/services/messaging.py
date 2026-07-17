"""Transactional encrypted-message use cases; plaintext is structurally absent."""

from __future__ import annotations

import base64
import binascii
import hmac
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from bluebubbles.server.configuration.settings import MessagingSettings
from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.audit import AuditSeverity
from bluebubbles.server.domain.messages import (
    Message,
    MessageDelivery,
    MessageRecipientKey,
)
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission
from bluebubbles.server.repositories.types import MessagePageQuery
from bluebubbles.server.services.audit import AuthenticationAuditWriter
from bluebubbles.server.services.events import EventFactory
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.shared.errors.exceptions import (
    AuthorisationError,
    ConflictError,
    ProtocolError,
    ResourceNotFoundError,
    ValidationError,
)
from bluebubbles.shared.models.messages import (
    DeletedMessageResponse,
    EditMessageRequest,
    EncryptedMessageResponse,
    MarkConversationReadRequest,
    MessageDeliveryStatus,
    MessagePageResponse,
    MessageType,
    RecipientKeyEnvelopeRequest,
    SendMessageRequest,
    SendMessageResponse,
    recipient_envelope_digest,
)
from bluebubbles.shared.models.pagination import CursorPageMetadata, OpaqueCursor


class MessageEnvelopeValidator:
    """Validate encrypted structure, protocol, and size without decryption."""

    def __init__(
        self, settings: MessagingSettings, supported_versions: set[int]
    ) -> None:
        self._settings = settings
        self._supported_versions = supported_versions

    def validate(self, request: SendMessageRequest) -> None:
        if request.protocol_version not in self._supported_versions:
            raise ProtocolError()
        if (
            len(request.model_dump_json().encode("utf-8"))
            > self._settings.maximum_encrypted_request_bytes
        ):
            raise ValidationError(
                user_message="The encrypted message request is too large."
            )
        if len(request.encrypted_keys) > self._settings.maximum_group_members:
            raise ValidationError(user_message="The recipient list is too large.")
        if request.recipient_envelope_digest != recipient_envelope_digest(
            request.encrypted_keys
        ):
            raise ValidationError(
                user_message="The recipient envelope digest is invalid."
            )


class MessagingService:
    """Store, retrieve, edit, delete, and acknowledge encrypted messages."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        audit_writer: AuthenticationAuditWriter,
        event_factory: EventFactory,
        validator: MessageEnvelopeValidator,
        settings: MessagingSettings,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._permission_service = permission_service
        self._audit_writer = audit_writer
        self._event_factory = event_factory
        self._validator = validator
        self._settings = settings

    async def send_message(
        self, sender: AuthenticatedUser, request: SendMessageRequest
    ) -> SendMessageResponse:
        self._validator.validate(request)
        await self._permission_service.require_authenticated_permission(
            sender, Permission.SEND_MESSAGE
        )
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as uow:
            existing = await uow.messages.get_existing_idempotent_message(
                request.client_message_id, sender.user_id
            )
            if existing is not None:
                if not self._same_payload(existing, request):
                    raise ConflictError(
                        user_message="The message identifier is already in use."
                    )
                return SendMessageResponse(
                    message=self._response(existing, sender.user_id), duplicate=True
                )
            conversation = await uow.conversations.get_by_id(
                request.conversation_id, for_update=True
            )
            if conversation is None or conversation.is_deleted:
                raise ResourceNotFoundError()
            members = await uow.conversations.get_active_members(
                request.conversation_id, for_update=True
            )
            required = {member.user_id for member in members if member.active}
            if sender.user_id not in required:
                raise AuthorisationError()
            supplied = {item.recipient_id for item in request.encrypted_keys}
            if supplied != required:
                raise ValidationError(
                    user_message="Encrypted keys must cover every active participant."
                )
            if request.reply_to_id is not None:
                reply = await uow.messages.get_by_id(request.reply_to_id)
                if reply is None or reply.conversation_id != request.conversation_id:
                    raise ValidationError(user_message="The reply target is invalid.")
            message = self._build_message(sender.user_id, request, now)
            for attachment_id in request.attachment_ids:
                attachment = await uow.attachments.get_by_id(attachment_id)
                if (
                    attachment is None
                    or attachment.uploaded_by != sender.user_id
                    or attachment.conversation_id != request.conversation_id
                    or not attachment.can_be_linked()
                ):
                    raise ValidationError(
                        user_message="One or more attachments cannot be linked."
                    )
            await uow.messages.create(message)
            if request.attachment_ids:
                await uow.attachments.link_to_message(
                    request.attachment_ids, message.id
                )
            await uow.messages.create_delivery_rows(
                tuple(
                    MessageDelivery(
                        id=uuid4(),
                        created_at=now,
                        updated_at=now,
                        message_id=message.id,
                        recipient_id=recipient_id,
                        status=MessageDeliveryStatus.STORED,
                        status_at=now,
                    )
                    for recipient_id in required
                )
            )
            if not await uow.conversations.update_last_activity(
                conversation.id, now, expected_version=conversation.version
            ):
                raise ConflictError(
                    user_message="The conversation changed during send."
                )
            await self._audit_writer.append(
                uow.audit,
                event_type="message_stored",
                occurred_at=now,
                actor_id=sender.user_id,
                source_ip=None,
                severity=AuditSeverity.INFORMATIONAL,
                details={
                    "message_id": str(message.id),
                    "conversation_id": str(message.conversation_id),
                    "recipient_count": len(required),
                },
            )
            await uow.outbox.add(self._event_factory.message_stored(message))
            await uow.commit()
            return SendMessageResponse(message=self._response(message, sender.user_id))

    async def list_messages(
        self,
        requester: AuthenticatedUser,
        conversation_id: UUID,
        cursor: str | None,
        limit: int,
    ) -> MessagePageResponse:
        async with self._unit_of_work_factory() as uow:
            membership = await uow.conversations.get_active_membership(
                conversation_id, requester.user_id
            )
            if membership is None:
                raise ResourceNotFoundError()
            page = await uow.messages.list_for_conversation(
                MessagePageQuery(
                    conversation_id=conversation_id,
                    user_id=requester.user_id,
                    cursor=cursor,
                    limit=min(limit, self._settings.maximum_page_size),
                    membership_started_at=membership.joined_at,
                )
            )
        return MessagePageResponse(
            messages=tuple(
                self._response(item, requester.user_id) for item in page.items
            ),
            page=CursorPageMetadata(
                next_cursor=(
                    OpaqueCursor(page.next_cursor) if page.next_cursor else None
                ),
                has_more=page.next_cursor is not None,
            ),
        )

    async def edit_message(
        self,
        requester: AuthenticatedUser,
        message_id: UUID,
        request: EditMessageRequest,
    ) -> EncryptedMessageResponse:
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as uow:
            message = await uow.messages.get_by_id(message_id, for_update=True)
            if message is None:
                raise ResourceNotFoundError()
            membership = await uow.conversations.get_active_membership(
                message.conversation_id, requester.user_id
            )
            if membership is None or requester.user_id != message.sender_id:
                raise AuthorisationError()
            if message.message_type not in {
                MessageType.TEXT,
                MessageType.TEXT_WITH_ATTACHMENT,
            }:
                raise ValidationError(
                    user_message="This message type cannot be edited."
                )
            if request.expected_version != message.version:
                raise ConflictError(user_message="The message has changed.")
            if not message.can_edit(
                requester.user_id,
                now,
                timedelta(seconds=self._settings.edit_window_seconds),
            ):
                raise ConflictError(user_message="The message edit window has expired.")
            members = await uow.conversations.get_active_members(
                message.conversation_id
            )
            if {item.recipient_id for item in request.encrypted_keys} != {
                item.user_id for item in members
            }:
                raise ValidationError(user_message="The recipient key set is invalid.")
            expected_version = message.version
            message.sender_key_version = request.sender_key_version
            message.replace_envelope(
                ciphertext=self._decode(request.ciphertext),
                nonce=self._decode(request.nonce),
                signature=self._decode(request.signature),
                recipient_keys=self._build_keys(
                    message.id, request.encrypted_keys, now
                ),
                at=now,
            )
            await uow.messages.update_encrypted_payload(
                message, expected_version=expected_version
            )
            await self._audit_writer.append(
                uow.audit,
                event_type="message_edited",
                occurred_at=now,
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.INFORMATIONAL,
                details={"message_id": str(message.id)},
            )
            await uow.outbox.add(self._event_factory.message_updated(message))
            await uow.commit()
            return self._response(message, requester.user_id)

    async def delete_message(
        self, requester: AuthenticatedUser, message_id: UUID, expected_version: int
    ) -> DeletedMessageResponse:
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as uow:
            message = await uow.messages.get_by_id(message_id, for_update=True)
            if message is None:
                raise ResourceNotFoundError()
            if requester.user_id != message.sender_id:
                await self._permission_service.require_authenticated_permission(
                    requester, Permission.DELETE_MESSAGE
                )
            if expected_version != message.version:
                raise ConflictError(user_message="The message has changed.")
            if not await uow.messages.soft_delete(
                message.id, now, expected_version=expected_version
            ):
                raise ConflictError(user_message="The message has changed.")
            message.mark_deleted(now)
            await self._audit_writer.append(
                uow.audit,
                event_type="message_deleted",
                occurred_at=now,
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.INFORMATIONAL,
                details={"message_id": str(message.id)},
            )
            await uow.outbox.add(self._event_factory.message_deleted(message, now))
            await uow.commit()
        return DeletedMessageResponse(
            message_id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            created_at=message.created_at,
            deleted_at=now,
            version=message.version,
        )

    async def mark_read(
        self, requester: AuthenticatedUser, request: MarkConversationReadRequest
    ) -> None:
        await self.mark_read_by_user_id(requester.user_id, request)

    async def mark_read_by_user_id(
        self, requester_id: UUID, request: MarkConversationReadRequest
    ) -> None:
        """Advance read state for a WebSocket-authenticated user identity."""
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as uow:
            membership = await uow.conversations.get_active_membership(
                request.conversation_id, requester_id, for_update=True
            )
            message = await uow.messages.get_for_user(
                request.through_message_id, requester_id
            )
            if (
                membership is None
                or message is None
                or message.conversation_id != request.conversation_id
            ):
                raise ResourceNotFoundError()
            await uow.messages.update_delivery_state(
                message.id, requester_id, MessageDeliveryStatus.READ, now
            )
            await uow.commit()

    async def acknowledge_delivery(
        self,
        requester_id: UUID,
        message_id: UUID,
        conversation_id: UUID,
        occurred_at: datetime,
    ) -> None:
        """Accept an acknowledgement only from an intended message recipient."""
        if occurred_at.tzinfo is None:
            raise ValidationError(user_message="Delivery timestamp is invalid.")
        async with self._unit_of_work_factory() as uow:
            message = await uow.messages.get_for_user(message_id, requester_id)
            if message is None or message.conversation_id != conversation_id:
                raise ResourceNotFoundError()
            await uow.messages.update_delivery_state(
                message_id,
                requester_id,
                MessageDeliveryStatus.DELIVERED,
                occurred_at,
            )
            await uow.commit()

    def _build_message(
        self, sender_id: UUID, request: SendMessageRequest, now: datetime
    ) -> Message:
        return Message(
            id=request.client_message_id,
            created_at=now,
            updated_at=now,
            client_message_id=request.client_message_id,
            conversation_id=request.conversation_id,
            sender_id=sender_id,
            message_type=request.message_type,
            content_algorithm=request.content_algorithm,
            ciphertext=self._decode(request.ciphertext),
            nonce=self._decode(request.nonce),
            signature_algorithm=request.signature_algorithm,
            signature=self._decode(request.signature),
            sender_key_version=request.sender_key_version,
            sent_at=request.client_created_at,
            recipient_keys=self._build_keys(
                request.client_message_id, request.encrypted_keys, now
            ),
            reply_to_id=request.reply_to_id,
            attachment_ids=request.attachment_ids,
        )

    @staticmethod
    def _build_keys(
        message_id: UUID,
        requests: tuple[RecipientKeyEnvelopeRequest, ...],
        now: datetime,
    ) -> tuple[MessageRecipientKey, ...]:
        return tuple(
            MessageRecipientKey(
                id=uuid4(),
                created_at=now,
                updated_at=now,
                message_id=message_id,
                recipient_id=item.recipient_id,
                key_version=item.key_version,
                algorithm=item.algorithm,
                ephemeral_public_key=MessagingService._decode(
                    item.ephemeral_public_key
                ),
                nonce=MessagingService._decode(item.nonce),
                encrypted_key=MessagingService._decode(item.encrypted_key),
            )
            for item in requests
        )

    @staticmethod
    def _response(message: Message, recipient_id: UUID) -> EncryptedMessageResponse:
        key = next(
            (
                item
                for item in message.recipient_keys
                if item.recipient_id == recipient_id
            ),
            None,
        )
        if key is None:
            raise AuthorisationError()
        key_requests = tuple(
            RecipientKeyEnvelopeRequest(
                recipient_id=item.recipient_id,
                key_version=item.key_version,
                algorithm=item.algorithm,
                ephemeral_public_key=MessagingService._encode(
                    item.ephemeral_public_key
                ),
                nonce=MessagingService._encode(item.nonce),
                encrypted_key=MessagingService._encode(item.encrypted_key),
            )
            for item in message.recipient_keys
        )
        selected = next(
            item for item in key_requests if item.recipient_id == recipient_id
        )
        return EncryptedMessageResponse(
            id=message.id,
            client_message_id=message.client_message_id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            message_type=message.message_type,
            content_algorithm=message.content_algorithm,
            ciphertext=MessagingService._encode(message.ciphertext),
            nonce=MessagingService._encode(message.nonce),
            signature_algorithm=message.signature_algorithm,
            signature=MessagingService._encode(message.signature),
            sender_key_version=message.sender_key_version,
            encrypted_key=selected,
            recipient_envelope_digest=recipient_envelope_digest(key_requests),
            sent_at=message.sent_at,
            edited_at=message.edited_at,
            reply_to_id=message.reply_to_id,
            attachment_ids=message.attachment_ids,
            version=message.version,
        )

    @staticmethod
    def _same_payload(message: Message, request: SendMessageRequest) -> bool:
        return all(
            (
                message.conversation_id == request.conversation_id,
                message.message_type is request.message_type,
                hmac.compare_digest(
                    message.ciphertext, MessagingService._decode(request.ciphertext)
                ),
                hmac.compare_digest(
                    message.nonce, MessagingService._decode(request.nonce)
                ),
                hmac.compare_digest(
                    message.signature, MessagingService._decode(request.signature)
                ),
                {key.recipient_id for key in message.recipient_keys}
                == {key.recipient_id for key in request.encrypted_keys},
            )
        )

    @staticmethod
    def _decode(value: str) -> bytes:
        try:
            return base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValidationError(
                user_message="Encrypted message encoding is invalid."
            ) from error

    @staticmethod
    def _encode(value: bytes) -> str:
        return base64.b64encode(value).decode("ascii")
