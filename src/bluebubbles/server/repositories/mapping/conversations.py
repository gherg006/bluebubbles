"""Pure conversation ORM/domain conversions."""

from bluebubbles.server.database.models.conversations import (
    ConversationMemberORM,
    ConversationORM,
)
from bluebubbles.server.domain.conversations import Conversation, ConversationMember
from bluebubbles.shared.models.conversations import ConversationType, GroupRole


class ConversationMapper:
    """Convert conversation rows and already-loaded membership rows."""

    @staticmethod
    def member_to_domain(record: ConversationMemberORM) -> ConversationMember:
        """Convert one membership period to a domain member."""
        return ConversationMember(
            id=record.id,
            created_at=record.joined_at,
            updated_at=record.removed_at or record.joined_at,
            version=record.membership_version,
            conversation_id=record.conversation_id,
            user_id=record.user_id,
            role=GroupRole(record.member_role),
            joined_at=record.joined_at,
            left_at=record.removed_at,
            is_muted=record.is_muted,
            is_pinned=record.is_pinned,
            is_archived=record.is_archived,
        )

    @staticmethod
    def member_to_orm(member: ConversationMember) -> ConversationMemberORM:
        """Convert one domain membership to a new ORM row."""
        return ConversationMemberORM(
            id=member.id,
            conversation_id=member.conversation_id,
            user_id=member.user_id,
            member_role=member.role.value,
            joined_at=member.joined_at,
            removed_at=member.left_at,
            last_read_message_id=None,
            last_read_at=None,
            is_muted=member.is_muted,
            muted_until=None,
            is_pinned=member.is_pinned,
            is_archived=member.is_archived,
            notification_level="all",
            membership_version=member.version,
        )

    @staticmethod
    def to_domain(
        record: ConversationORM,
        members: tuple[ConversationMemberORM, ...] = (),
    ) -> Conversation:
        """Convert a conversation with an explicitly supplied membership set."""
        mapped = tuple(ConversationMapper.member_to_domain(item) for item in members)
        return Conversation(
            id=record.id,
            created_at=record.created_at,
            updated_at=record.updated_at,
            deleted_at=record.deleted_at,
            version=record.version,
            conversation_type=ConversationType(record.conversation_type),
            created_by=record.created_by,
            last_activity=record.last_activity_at or record.created_at,
            title=record.title,
            description=record.description,
            archived=record.is_archived_systemwide,
            members={member.user_id: member for member in mapped},
        )

    @staticmethod
    def to_orm(conversation: Conversation) -> ConversationORM:
        """Convert one domain conversation to a new ORM row."""
        return ConversationORM(
            id=conversation.id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            deleted_at=conversation.deleted_at,
            version=conversation.version,
            conversation_type=conversation.conversation_type.value,
            title=conversation.title,
            description=conversation.description,
            created_by=conversation.created_by,
            last_activity_at=conversation.last_activity,
            is_archived_systemwide=conversation.archived,
        )
