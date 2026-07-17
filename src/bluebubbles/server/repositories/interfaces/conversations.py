"""Conversation repository protocol."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from bluebubbles.server.domain.conversations import Conversation, ConversationMember
from bluebubbles.server.repositories.types import ConversationListQuery, CursorPage
from bluebubbles.shared.models.conversations import GroupRole


class ConversationRepository(Protocol):
    """Define conversation and membership persistence operations."""

    async def get_by_id(
        self, conversation_id: UUID, *, for_update: bool = False
    ) -> Conversation | None: ...

    async def find_direct_pair(
        self, first_user_id: UUID, second_user_id: UUID
    ) -> Conversation | None: ...

    async def create(self, conversation: Conversation) -> Conversation: ...

    async def create_direct(self, conversation: Conversation) -> Conversation: ...

    async def create_group(self, conversation: Conversation) -> Conversation: ...

    async def list_for_user(
        self, query: ConversationListQuery
    ) -> CursorPage[Conversation]: ...

    async def get_active_members(
        self, conversation_id: UUID, *, for_update: bool = False
    ) -> list[ConversationMember]: ...

    async def list_active_members(
        self, conversation_id: UUID, *, for_update: bool = False
    ) -> list[ConversationMember]: ...

    async def get_membership(
        self,
        conversation_id: UUID,
        user_id: UUID,
        *,
        for_update: bool = False,
    ) -> ConversationMember | None: ...

    async def get_active_membership(
        self,
        conversation_id: UUID,
        user_id: UUID,
        *,
        for_update: bool = False,
    ) -> ConversationMember | None: ...

    async def add_member(self, member: ConversationMember) -> ConversationMember: ...

    async def remove_member(
        self, membership_id: UUID, removed_at: datetime, *, expected_version: int
    ) -> bool: ...

    async def change_member_role(
        self, membership_id: UUID, role: GroupRole, *, expected_version: int
    ) -> bool: ...

    async def update_last_activity(
        self,
        conversation_id: UUID,
        last_activity: datetime,
        *,
        expected_version: int,
    ) -> bool: ...
