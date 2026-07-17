"""Encrypted-message repository protocol."""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from bluebubbles.server.domain.messages import (
    Message,
    MessageDelivery,
    MessageRecipientKey,
)
from bluebubbles.server.repositories.types import CursorPage, MessagePageQuery
from bluebubbles.shared.models.messages import MessageDeliveryStatus


class MessageRepository(Protocol):
    """Define encrypted envelope persistence without permission decisions."""

    async def create(self, message: Message) -> Message: ...

    async def get_by_id(
        self, message_id: UUID, *, for_update: bool = False
    ) -> Message | None: ...

    async def get_existing_idempotent_message(
        self, message_id: UUID, sender_id: UUID
    ) -> Message | None: ...

    async def get_for_user(self, message_id: UUID, user_id: UUID) -> Message | None: ...

    async def list_for_conversation(
        self, query: MessagePageQuery
    ) -> CursorPage[Message]: ...

    async def insert_recipient_keys(
        self, keys: Sequence[MessageRecipientKey]
    ) -> None: ...

    async def add_recipient_keys(self, keys: Sequence[MessageRecipientKey]) -> None: ...

    async def get_recipient_key(
        self, message_id: UUID, recipient_id: UUID
    ) -> MessageRecipientKey | None: ...

    async def update_encrypted_payload(
        self, message: Message, *, expected_version: int
    ) -> Message: ...

    async def update_payload(
        self, message: Message, expected_version: int
    ) -> Message: ...

    async def soft_delete(
        self, message_id: UUID, deleted_at: datetime, *, expected_version: int
    ) -> bool: ...

    async def create_delivery_rows(
        self, deliveries: Sequence[MessageDelivery]
    ) -> None: ...

    async def update_delivery_state(
        self,
        message_id: UUID,
        recipient_id: UUID,
        state: MessageDeliveryStatus,
        at: datetime,
    ) -> bool: ...
