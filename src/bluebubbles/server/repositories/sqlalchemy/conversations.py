"""Async SQLAlchemy conversation repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.conversations import (
    ConversationMemberORM,
    ConversationORM,
    DirectConversationPairORM,
)
from bluebubbles.server.domain.conversations import (
    Conversation,
    ConversationMember,
    DirectConversationPair,
)
from bluebubbles.server.repositories.mapping.conversations import ConversationMapper
from bluebubbles.server.repositories.sqlalchemy._common import (
    flush_changes,
    require_aware,
)
from bluebubbles.server.repositories.types import (
    ConversationListQuery,
    CursorPage,
    decode_cursor,
    encode_cursor,
)
from bluebubbles.shared.models.conversations import ConversationType, GroupRole


class SqlAlchemyConversationRepository:
    """Persist conversations and membership periods without policy decisions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, conversation_id: UUID, *, for_update: bool = False
    ) -> Conversation | None:
        """Return one active conversation and its active memberships."""
        statement = select(ConversationORM).where(
            ConversationORM.id == conversation_id,
            ConversationORM.deleted_at.is_(None),
        )
        if for_update:
            statement = statement.with_for_update()
        record = (await self._session.execute(statement)).scalar_one_or_none()
        if record is None:
            return None
        members = await self._load_active_members((conversation_id,), for_update)
        return ConversationMapper.to_domain(record, tuple(members))

    async def find_direct_pair(
        self, first_user_id: UUID, second_user_id: UUID
    ) -> Conversation | None:
        """Return the active direct conversation for an order-independent pair."""
        pair = DirectConversationPair.create(first_user_id, second_user_id)
        statement = (
            select(ConversationORM)
            .join(
                DirectConversationPairORM,
                DirectConversationPairORM.conversation_id == ConversationORM.id,
            )
            .where(
                DirectConversationPairORM.lower_user_id == pair.first_user_id,
                DirectConversationPairORM.higher_user_id == pair.second_user_id,
                ConversationORM.deleted_at.is_(None),
            )
        )
        record = (await self._session.execute(statement)).scalar_one_or_none()
        if record is None:
            return None
        members = await self._load_active_members((record.id,), False)
        return ConversationMapper.to_domain(record, tuple(members))

    async def create(self, conversation: Conversation) -> Conversation:
        """Create a direct or group conversation according to its domain type."""
        if conversation.conversation_type is ConversationType.DIRECT:
            return await self.create_direct(conversation)
        return await self.create_group(conversation)

    async def create_direct(self, conversation: Conversation) -> Conversation:
        """Stage a direct conversation, canonical pair, and membership rows."""
        if conversation.conversation_type is not ConversationType.DIRECT:
            raise ValueError("Direct creation requires a direct conversation")
        active_members = tuple(
            member for member in conversation.members.values() if member.active
        )
        if len(active_members) != 2:
            raise ValueError("A direct conversation requires exactly two members")
        pair = DirectConversationPair.create(
            active_members[0].user_id, active_members[1].user_id
        )
        self._session.add(ConversationMapper.to_orm(conversation))
        self._session.add(
            DirectConversationPairORM(
                conversation_id=conversation.id,
                lower_user_id=pair.first_user_id,
                higher_user_id=pair.second_user_id,
            )
        )
        self._session.add_all(
            [ConversationMapper.member_to_orm(member) for member in active_members]
        )
        await flush_changes(self._session)
        return conversation

    async def create_group(self, conversation: Conversation) -> Conversation:
        """Stage a group and all supplied membership rows atomically."""
        if conversation.conversation_type is not ConversationType.GROUP:
            raise ValueError("Group creation requires a group conversation")
        active_members = tuple(
            member for member in conversation.members.values() if member.active
        )
        owners = [member for member in active_members if member.role is GroupRole.OWNER]
        if len(owners) != 1:
            raise ValueError("A group requires exactly one active owner")
        self._session.add(ConversationMapper.to_orm(conversation))
        self._session.add_all(
            [ConversationMapper.member_to_orm(member) for member in active_members]
        )
        await flush_changes(self._session)
        return conversation

    async def list_for_user(
        self, query: ConversationListQuery
    ) -> CursorPage[Conversation]:
        """List active memberships by stable descending activity/UUID order."""
        statement = (
            select(ConversationORM)
            .join(
                ConversationMemberORM,
                ConversationMemberORM.conversation_id == ConversationORM.id,
            )
            .where(
                ConversationMemberORM.user_id == query.user_id,
                ConversationMemberORM.removed_at.is_(None),
                ConversationORM.deleted_at.is_(None),
            )
        )
        if not query.include_archived:
            statement = statement.where(
                ConversationMemberORM.is_archived.is_(False),
                ConversationORM.is_archived_systemwide.is_(False),
            )
        if query.cursor is not None:
            activity_value, id_value = decode_cursor(query.cursor, 2)
            if not isinstance(activity_value, str) or not isinstance(id_value, str):
                raise ValueError("Invalid conversation cursor")
            activity = datetime.fromisoformat(activity_value)
            conversation_id = UUID(id_value)
            statement = statement.where(
                or_(
                    ConversationORM.last_activity_at < activity,
                    and_(
                        ConversationORM.last_activity_at == activity,
                        ConversationORM.id < conversation_id,
                    ),
                )
            )
        statement = statement.order_by(
            ConversationORM.last_activity_at.desc(), ConversationORM.id.desc()
        ).limit(query.limit + 1)
        records = list((await self._session.scalars(statement)).all())
        has_more = len(records) > query.limit
        selected = records[: query.limit]
        members = await self._load_active_members(
            tuple(record.id for record in selected), False
        )
        grouped: dict[UUID, list[ConversationMemberORM]] = {}
        for member in members:
            grouped.setdefault(member.conversation_id, []).append(member)
        next_cursor = None
        if has_more and selected:
            last = selected[-1]
            next_cursor = encode_cursor(
                last.last_activity_at or last.created_at, last.id
            )
        return CursorPage(
            items=tuple(
                ConversationMapper.to_domain(record, tuple(grouped.get(record.id, ())))
                for record in selected
            ),
            next_cursor=next_cursor,
        )

    async def get_active_members(
        self, conversation_id: UUID, *, for_update: bool = False
    ) -> list[ConversationMember]:
        """Return active members, optionally locked in deterministic ID order."""
        return await self.list_active_members(conversation_id, for_update=for_update)

    async def list_active_members(
        self, conversation_id: UUID, *, for_update: bool = False
    ) -> list[ConversationMember]:
        """Return active members, optionally locked in deterministic ID order."""
        records = await self._load_active_members((conversation_id,), for_update)
        return [ConversationMapper.member_to_domain(record) for record in records]

    async def get_membership(
        self,
        conversation_id: UUID,
        user_id: UUID,
        *,
        for_update: bool = False,
    ) -> ConversationMember | None:
        """Return the active membership for one conversation/user pair."""
        return await self.get_active_membership(
            conversation_id, user_id, for_update=for_update
        )

    async def get_active_membership(
        self,
        conversation_id: UUID,
        user_id: UUID,
        *,
        for_update: bool = False,
    ) -> ConversationMember | None:
        """Return one current membership, optionally row-locked."""
        statement = select(ConversationMemberORM).where(
            ConversationMemberORM.conversation_id == conversation_id,
            ConversationMemberORM.user_id == user_id,
            ConversationMemberORM.removed_at.is_(None),
        )
        if for_update:
            statement = statement.with_for_update()
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return (
            ConversationMapper.member_to_domain(record) if record is not None else None
        )

    async def add_member(self, member: ConversationMember) -> ConversationMember:
        """Stage and flush one new membership period."""
        self._session.add(ConversationMapper.member_to_orm(member))
        await flush_changes(self._session)
        return member

    async def remove_member(
        self, membership_id: UUID, removed_at: datetime, *, expected_version: int
    ) -> bool:
        """Close one active membership using optimistic concurrency."""
        require_aware(removed_at, "removed_at")
        result = await self._session.execute(
            update(ConversationMemberORM)
            .where(
                ConversationMemberORM.id == membership_id,
                ConversationMemberORM.removed_at.is_(None),
                ConversationMemberORM.membership_version == expected_version,
                ConversationMemberORM.member_role != GroupRole.OWNER.value,
            )
            .values(removed_at=removed_at, membership_version=expected_version + 1)
        )
        return result.rowcount == 1

    async def change_member_role(
        self, membership_id: UUID, role: GroupRole, *, expected_version: int
    ) -> bool:
        """Change one active membership role after service authorization."""
        result = await self._session.execute(
            update(ConversationMemberORM)
            .where(
                ConversationMemberORM.id == membership_id,
                ConversationMemberORM.removed_at.is_(None),
                ConversationMemberORM.membership_version == expected_version,
            )
            .values(member_role=role.value, membership_version=expected_version + 1)
        )
        return result.rowcount == 1

    async def update_last_activity(
        self,
        conversation_id: UUID,
        last_activity: datetime,
        *,
        expected_version: int,
    ) -> bool:
        """Advance conversation ordering metadata using optimistic concurrency."""
        require_aware(last_activity, "last_activity")
        result = await self._session.execute(
            update(ConversationORM)
            .where(
                ConversationORM.id == conversation_id,
                ConversationORM.deleted_at.is_(None),
                ConversationORM.version == expected_version,
                ConversationORM.last_activity_at <= last_activity,
            )
            .values(
                last_activity_at=last_activity,
                updated_at=last_activity,
                version=expected_version + 1,
            )
        )
        return result.rowcount == 1

    async def _load_active_members(
        self, conversation_ids: tuple[UUID, ...], for_update: bool
    ) -> list[ConversationMemberORM]:
        if not conversation_ids:
            return []
        statement = (
            select(ConversationMemberORM)
            .where(
                ConversationMemberORM.conversation_id.in_(conversation_ids),
                ConversationMemberORM.removed_at.is_(None),
            )
            .order_by(ConversationMemberORM.id)
        )
        if for_update:
            statement = statement.with_for_update()
        return list((await self._session.scalars(statement)).all())
