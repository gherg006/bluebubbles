"""Async SQLAlchemy encrypted-message repository."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.attachments import AttachmentORM
from bluebubbles.server.database.models.messages import (
    MessageDeliveryORM,
    MessageORM,
    MessageRecipientKeyORM,
    MessageVersionORM,
)
from bluebubbles.server.domain.messages import (
    Message,
    MessageDelivery,
    MessageRecipientKey,
)
from bluebubbles.server.repositories.mapping.messages import MessageMapper
from bluebubbles.server.repositories.sqlalchemy._common import (
    flush_changes,
    require_aware,
)
from bluebubbles.server.repositories.types import (
    CursorPage,
    MessagePageQuery,
    decode_cursor,
    encode_cursor,
)
from bluebubbles.shared.errors.exceptions import ConflictError
from bluebubbles.shared.models.messages import MessageDeliveryStatus


class SqlAlchemyMessageRepository:
    """Persist encrypted envelopes without decrypting or authorizing content."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, message: Message) -> Message:
        """Stage a message and its recipient key envelopes, then flush."""
        if message.id != message.client_message_id:
            raise ValueError("Message ID must equal the client idempotency identifier")
        self._session.add(MessageMapper.to_orm(message))
        self._session.add_all(
            [MessageMapper.key_to_orm(key) for key in message.recipient_keys]
        )
        await flush_changes(self._session)
        return message

    async def get_by_id(
        self, message_id: UUID, *, for_update: bool = False
    ) -> Message | None:
        """Return one non-deleted encrypted message with keys and attachments."""
        statement = select(MessageORM).where(
            MessageORM.id == message_id, MessageORM.deleted_at.is_(None)
        )
        if for_update:
            statement = statement.with_for_update()
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return await self._map_record(record) if record is not None else None

    async def get_existing_idempotent_message(
        self, message_id: UUID, sender_id: UUID
    ) -> Message | None:
        """Return an existing sender-owned message for idempotency comparison."""
        statement = select(MessageORM).where(
            MessageORM.id == message_id,
            MessageORM.sender_id == sender_id,
            MessageORM.deleted_at.is_(None),
        )
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return await self._map_record(record) if record is not None else None

    async def get_for_user(self, message_id: UUID, user_id: UUID) -> Message | None:
        """Return a message only when a recipient-key row exists for the user."""
        statement = (
            select(MessageORM)
            .join(
                MessageRecipientKeyORM,
                MessageRecipientKeyORM.message_id == MessageORM.id,
            )
            .where(
                MessageORM.id == message_id,
                MessageORM.deleted_at.is_(None),
                MessageRecipientKeyORM.recipient_user_id == user_id,
            )
        )
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return await self._map_record(record) if record is not None else None

    async def list_for_conversation(
        self, query: MessagePageQuery
    ) -> CursorPage[Message]:
        """Return a stable newest-first encrypted-message page."""
        statement = select(MessageORM).where(
            MessageORM.conversation_id == query.conversation_id
        )
        if not query.include_deleted:
            statement = statement.where(MessageORM.deleted_at.is_(None))
        if query.membership_started_at is not None:
            statement = statement.where(
                MessageORM.server_created_at >= query.membership_started_at
            )
        if query.user_id is not None:
            statement = statement.join(
                MessageRecipientKeyORM,
                and_(
                    MessageRecipientKeyORM.message_id == MessageORM.id,
                    MessageRecipientKeyORM.recipient_user_id == query.user_id,
                ),
            )
        if query.cursor is not None:
            time_value, id_value = decode_cursor(query.cursor, 2)
            if not isinstance(time_value, str) or not isinstance(id_value, str):
                raise ValueError("Invalid message cursor")
            created_at = datetime.fromisoformat(time_value)
            message_id = UUID(id_value)
            statement = statement.where(
                or_(
                    MessageORM.server_created_at < created_at,
                    and_(
                        MessageORM.server_created_at == created_at,
                        MessageORM.id < message_id,
                    ),
                )
            )
        statement = statement.order_by(
            MessageORM.server_created_at.desc(), MessageORM.id.desc()
        ).limit(query.limit + 1)
        records = list((await self._session.scalars(statement)).all())
        has_more = len(records) > query.limit
        selected = records[: query.limit]
        mapped = await self._map_records(selected)
        next_cursor = None
        if has_more and selected:
            last = selected[-1]
            next_cursor = encode_cursor(last.server_created_at, last.id)
        return CursorPage(items=tuple(mapped), next_cursor=next_cursor)

    async def insert_recipient_keys(self, keys: Sequence[MessageRecipientKey]) -> None:
        """Stage unique per-recipient encrypted message key envelopes."""
        await self.add_recipient_keys(keys)

    async def add_recipient_keys(self, keys: Sequence[MessageRecipientKey]) -> None:
        """Stage unique per-recipient encrypted message key envelopes."""
        self._session.add_all([MessageMapper.key_to_orm(key) for key in keys])
        await flush_changes(self._session)

    async def get_recipient_key(
        self, message_id: UUID, recipient_id: UUID
    ) -> MessageRecipientKey | None:
        """Return exactly one recipient-specific encrypted key envelope."""
        statement = select(MessageRecipientKeyORM).where(
            MessageRecipientKeyORM.message_id == message_id,
            MessageRecipientKeyORM.recipient_user_id == recipient_id,
        )
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return MessageMapper.key_to_domain(record) if record is not None else None

    async def update_encrypted_payload(
        self, message: Message, *, expected_version: int
    ) -> Message:
        """Persist an encrypted edit and immutable prior version atomically."""
        return await self.update_payload(message, expected_version)

    async def update_payload(self, message: Message, expected_version: int) -> Message:
        """Stage a version snapshot, encrypted replacement, and new key set."""
        current_statement = (
            select(MessageORM)
            .where(
                MessageORM.id == message.id,
                MessageORM.deleted_at.is_(None),
                MessageORM.version == expected_version,
            )
            .with_for_update()
        )
        current = (await self._session.execute(current_statement)).scalar_one_or_none()
        if current is None:
            raise ConflictError(
                user_message="The message changed before the edit could be saved."
            )
        if any(
            value is None
            for value in (
                current.ciphertext,
                current.nonce,
                current.signature,
                current.signature_key_version,
            )
        ):
            raise ConflictError(user_message="The message cannot be edited.")
        self._session.add(
            MessageVersionORM(
                id=uuid4(),
                message_id=current.id,
                version_number=current.version,
                ciphertext=current.ciphertext,
                nonce=current.nonce,
                authentication_tag=current.authentication_tag or b"",
                signature=current.signature,
                signature_key_version=current.signature_key_version,
                edited_at=message.edited_at or message.updated_at,
                created_at=message.updated_at,
            )
        )
        result = await self._session.execute(
            update(MessageORM)
            .where(MessageORM.id == message.id, MessageORM.version == expected_version)
            .values(
                ciphertext=message.ciphertext,
                nonce=message.nonce,
                signature=message.signature,
                signature_key_version=message.sender_key_version,
                encrypted_payload_size=len(message.ciphertext),
                edited_at=message.edited_at or message.updated_at,
                version=message.version,
            )
        )
        if result.rowcount != 1:
            raise ConflictError(
                user_message="The message changed before the edit could be saved."
            )
        await self._session.execute(
            delete(MessageRecipientKeyORM).where(
                MessageRecipientKeyORM.message_id == message.id
            )
        )
        self._session.add_all(
            [MessageMapper.key_to_orm(key) for key in message.recipient_keys]
        )
        await flush_changes(self._session)
        return message

    async def soft_delete(
        self, message_id: UUID, deleted_at: datetime, *, expected_version: int
    ) -> bool:
        """Soft-delete one encrypted message with optimistic concurrency."""
        require_aware(deleted_at, "deleted_at")
        result = await self._session.execute(
            update(MessageORM)
            .where(
                MessageORM.id == message_id,
                MessageORM.deleted_at.is_(None),
                MessageORM.version == expected_version,
            )
            .values(deleted_at=deleted_at, version=expected_version + 1)
        )
        return result.rowcount == 1

    async def create_delivery_rows(self, deliveries: Sequence[MessageDelivery]) -> None:
        """Stage durable delivery rows for the supplied recipients."""
        self._session.add_all(
            [
                MessageDeliveryORM(
                    message_id=item.message_id,
                    recipient_user_id=item.recipient_id,
                    delivery_state=item.status.value,
                    delivered_at=(
                        item.status_at
                        if item.status
                        in {
                            MessageDeliveryStatus.DELIVERED,
                            MessageDeliveryStatus.READ,
                        }
                        else None
                    ),
                    read_at=(
                        item.status_at
                        if item.status is MessageDeliveryStatus.READ
                        else None
                    ),
                    updated_at=item.status_at,
                )
                for item in deliveries
            ]
        )
        await flush_changes(self._session)

    async def update_delivery_state(
        self,
        message_id: UUID,
        recipient_id: UUID,
        state: MessageDeliveryStatus,
        at: datetime,
    ) -> bool:
        """Advance one delivery row without permitting state regression."""
        require_aware(at, "at")
        allowed_previous_by_target = {
            MessageDeliveryStatus.PENDING: (),
            MessageDeliveryStatus.STORED: (MessageDeliveryStatus.PENDING.value,),
            MessageDeliveryStatus.DELIVERED: (MessageDeliveryStatus.STORED.value,),
            MessageDeliveryStatus.READ: (MessageDeliveryStatus.DELIVERED.value,),
            MessageDeliveryStatus.FAILED: (
                MessageDeliveryStatus.PENDING.value,
                MessageDeliveryStatus.STORED.value,
            ),
        }
        allowed_previous = allowed_previous_by_target[state]
        result = await self._session.execute(
            update(MessageDeliveryORM)
            .where(
                MessageDeliveryORM.message_id == message_id,
                MessageDeliveryORM.recipient_user_id == recipient_id,
                MessageDeliveryORM.delivery_state.in_(allowed_previous),
            )
            .values(
                delivery_state=state.value,
                delivered_at=(
                    at
                    if state
                    in {MessageDeliveryStatus.DELIVERED, MessageDeliveryStatus.READ}
                    else MessageDeliveryORM.delivered_at
                ),
                read_at=(
                    at
                    if state is MessageDeliveryStatus.READ
                    else MessageDeliveryORM.read_at
                ),
                updated_at=at,
            )
        )
        return result.rowcount == 1

    async def _map_record(self, record: MessageORM) -> Message:
        mapped = await self._map_records([record])
        return mapped[0]

    async def _map_records(self, records: list[MessageORM]) -> list[Message]:
        if not records:
            return []
        ids = [record.id for record in records]
        key_records = list(
            (
                await self._session.scalars(
                    select(MessageRecipientKeyORM)
                    .where(MessageRecipientKeyORM.message_id.in_(ids))
                    .order_by(MessageRecipientKeyORM.recipient_user_id)
                )
            ).all()
        )
        attachment_records = list(
            (
                await self._session.scalars(
                    select(AttachmentORM).where(AttachmentORM.message_id.in_(ids))
                )
            ).all()
        )
        keys_by_message: dict[UUID, list[MessageRecipientKeyORM]] = {}
        for key in key_records:
            keys_by_message.setdefault(key.message_id, []).append(key)
        attachments_by_message: dict[UUID, list[UUID]] = {}
        for attachment in attachment_records:
            if attachment.message_id is not None:
                attachments_by_message.setdefault(attachment.message_id, []).append(
                    attachment.id
                )
        return [
            MessageMapper.to_domain(
                record,
                tuple(keys_by_message.get(record.id, ())),
                tuple(attachments_by_message.get(record.id, ())),
            )
            for record in records
        ]
