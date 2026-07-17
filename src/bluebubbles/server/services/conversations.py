"""Direct and group conversation creation, retrieval, and listing."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from bluebubbles.server.database.unit_of_work import UnitOfWork, UnitOfWorkFactory
from bluebubbles.server.domain.audit import AuditSeverity
from bluebubbles.server.domain.conversations import (
    Conversation,
    ConversationEvent,
    ConversationEventType,
    ConversationMember,
)
from bluebubbles.server.domain.outbox import OutboxEvent
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission
from bluebubbles.server.repositories.types import ConversationListQuery
from bluebubbles.server.services.audit import AuthenticationAuditWriter
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.server.services.users import user_summary
from bluebubbles.shared.errors.exceptions import (
    ConflictError,
    ResourceNotFoundError,
)
from bluebubbles.shared.models.conversations import (
    ConversationParticipantResponse,
    ConversationResponse,
    ConversationSummaryResponse,
    ConversationType,
    CreateDirectConversationRequest,
    CreateGroupConversationRequest,
    GroupRole,
)
from bluebubbles.shared.models.pagination import (
    CursorPage,
    CursorPageMetadata,
    OpaqueCursor,
)


class ConversationService:
    """Coordinate transaction-safe direct and group conversation use cases."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        audit_writer: AuthenticationAuditWriter,
        *,
        maximum_group_members: int,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._permission_service = permission_service
        self._audit_writer = audit_writer
        self._maximum_group_members = maximum_group_members

    async def create_direct(
        self,
        requester: AuthenticatedUser,
        request: CreateDirectConversationRequest,
    ) -> ConversationResponse:
        """Create or return the unique direct conversation for two users."""
        if requester.user_id == request.target_user_id:
            raise ConflictError(
                user_message="A direct conversation requires another user."
            )
        await self._permission_service.require_authenticated_permission(
            requester, Permission.SEND_MESSAGE
        )
        try:
            async with self._unit_of_work_factory() as unit_of_work:
                existing = await unit_of_work.conversations.find_direct_pair(
                    requester.user_id, request.target_user_id
                )
                if existing is not None:
                    return await self._response(
                        unit_of_work, existing, requester.user_id
                    )
                target = await unit_of_work.users.get_by_id(request.target_user_id)
                actor = await unit_of_work.users.get_by_id(requester.user_id)
                if target is None or actor is None or not target.is_enabled:
                    raise ResourceNotFoundError()
                target_permissions = (
                    await unit_of_work.authentication.permissions_for_role(
                        target.role_id
                    )
                )
                if Permission.SEND_MESSAGE not in target_permissions:
                    raise ResourceNotFoundError()
                actor_block = await unit_of_work.contacts.get(
                    requester.user_id, target.id
                )
                target_block = await unit_of_work.contacts.get(
                    target.id, requester.user_id
                )
                if (actor_block and actor_block.is_blocked) or (
                    target_block and target_block.is_blocked
                ):
                    raise ConflictError(
                        user_message=(
                            "A direct conversation is blocked by contact policy."
                        )
                    )
                now = datetime.now(UTC)
                conversation = Conversation(
                    id=uuid4(),
                    created_at=now,
                    updated_at=now,
                    conversation_type=ConversationType.DIRECT,
                    created_by=requester.user_id,
                    last_activity=now,
                )
                for user_id in (requester.user_id, target.id):
                    conversation.add_member(
                        ConversationMember.create(
                            conversation_id=conversation.id,
                            user_id=user_id,
                            role=GroupRole.MEMBER,
                            joined_at=now,
                        ),
                        now,
                    )
                await unit_of_work.conversations.create_direct(conversation)
                await self._record_event(
                    unit_of_work,
                    conversation,
                    requester.user_id,
                    None,
                    ConversationEventType.CONVERSATION_CREATED,
                    "direct_conversation_created",
                    now,
                )
                response = await self._response(
                    unit_of_work, conversation, requester.user_id
                )
                await unit_of_work.commit()
                return response
        except ConflictError:
            async with self._unit_of_work_factory() as retry_unit_of_work:
                winner = await retry_unit_of_work.conversations.find_direct_pair(
                    requester.user_id, request.target_user_id
                )
                if winner is not None:
                    return await self._response(
                        retry_unit_of_work, winner, requester.user_id
                    )
            raise

    async def create_group(
        self,
        requester: AuthenticatedUser,
        request: CreateGroupConversationRequest,
    ) -> ConversationResponse:
        """Create a group with one owner and validated enabled members."""
        await self._permission_service.require_authenticated_permission(
            requester, Permission.CREATE_GROUP
        )
        member_ids = tuple(dict.fromkeys(request.member_ids))
        all_ids = tuple(dict.fromkeys((requester.user_id, *member_ids)))
        if len(all_ids) < 2:
            raise ConflictError(user_message="A group requires at least two members.")
        if len(all_ids) > self._maximum_group_members:
            raise ConflictError(user_message="The group member limit was reached.")
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as unit_of_work:
            for user_id in all_ids:
                user = await unit_of_work.users.get_by_id(user_id)
                if user is None or not user.is_enabled:
                    raise ResourceNotFoundError()
            conversation = Conversation(
                id=uuid4(),
                created_at=now,
                updated_at=now,
                conversation_type=ConversationType.GROUP,
                title=request.name,
                description=request.description,
                created_by=requester.user_id,
                last_activity=now,
            )
            for user_id in all_ids:
                conversation.add_member(
                    ConversationMember.create(
                        conversation_id=conversation.id,
                        user_id=user_id,
                        role=(
                            GroupRole.OWNER
                            if user_id == requester.user_id
                            else GroupRole.MEMBER
                        ),
                        joined_at=now,
                    ),
                    now,
                )
            await unit_of_work.conversations.create_group(conversation)
            await self._record_event(
                unit_of_work,
                conversation,
                requester.user_id,
                None,
                ConversationEventType.GROUP_CREATED,
                "group_created",
                now,
            )
            response = await self._response(
                unit_of_work, conversation, requester.user_id
            )
            await unit_of_work.commit()
        return response

    async def get_conversation(
        self, requester: AuthenticatedUser, conversation_id: UUID
    ) -> ConversationResponse:
        """Return a conversation only to an active member."""
        async with self._unit_of_work_factory() as unit_of_work:
            conversation = await unit_of_work.conversations.get_by_id(conversation_id)
            if (
                conversation is None
                or conversation.active_member(requester.user_id) is None
            ):
                raise ResourceNotFoundError()
            return await self._response(unit_of_work, conversation, requester.user_id)

    async def list_for_user(
        self, requester: AuthenticatedUser, query: ConversationListQuery
    ) -> CursorPage[ConversationSummaryResponse]:
        """Return a bounded page without loading message history or plaintext."""
        if query.user_id != requester.user_id:
            raise ResourceNotFoundError()
        async with self._unit_of_work_factory() as unit_of_work:
            page = await unit_of_work.conversations.list_for_user(query)
            summaries: list[ConversationSummaryResponse] = []
            for item in page.items:
                summaries.append(
                    await self._summary(unit_of_work, item, requester.user_id)
                )
            items = tuple(summaries)
        return CursorPage(
            items=items,
            page=CursorPageMetadata(
                next_cursor=(
                    OpaqueCursor(page.next_cursor) if page.next_cursor else None
                ),
                has_more=page.next_cursor is not None,
            ),
        )

    async def archive_for_user(
        self, requester: AuthenticatedUser, conversation_id: UUID, archived: bool
    ) -> None:
        """Set an archive preference that affects no other participant."""
        async with self._unit_of_work_factory() as unit_of_work:
            member = await unit_of_work.conversations.get_active_membership(
                conversation_id, requester.user_id, for_update=True
            )
            if member is None:
                raise ResourceNotFoundError()
            if not await unit_of_work.conversations.set_archived(
                member.id, archived, expected_version=member.version
            ):
                raise ConflictError()
            await unit_of_work.commit()

    async def _summary(
        self, unit_of_work: UnitOfWork, conversation: Conversation, requester_id: UUID
    ) -> ConversationSummaryResponse:
        users = []
        for member in conversation.members.values():
            user = await unit_of_work.users.get_by_id(member.user_id)
            if user is not None:
                users.append(user_summary(user))
        requester = conversation.active_member(requester_id)
        title = conversation.title
        if conversation.conversation_type is ConversationType.DIRECT:
            title = next(
                (user.display_name for user in users if user.id != requester_id),
                "Direct conversation",
            )
        return ConversationSummaryResponse(
            id=conversation.id,
            type=conversation.conversation_type,
            title=title,
            participants=tuple(users),
            last_activity=conversation.last_activity,
            archived=requester.is_archived if requester else False,
        )

    async def _response(
        self, unit_of_work: UnitOfWork, conversation: Conversation, requester_id: UUID
    ) -> ConversationResponse:
        summary = await self._summary(unit_of_work, conversation, requester_id)
        details = []
        for member in conversation.members.values():
            user = await unit_of_work.users.get_by_id(member.user_id)
            if user is not None:
                details.append(
                    ConversationParticipantResponse(
                        user=user_summary(user),
                        role=member.role,
                        joined_at=member.joined_at,
                    )
                )
        return ConversationResponse(
            **summary.model_dump(),
            created_by=conversation.created_by,
            created_at=conversation.created_at,
            participant_details=tuple(details),
            description=conversation.description,
        )

    async def _record_event(
        self,
        unit_of_work: UnitOfWork,
        conversation: Conversation,
        actor_id: UUID,
        subject_id: UUID | None,
        event_type: ConversationEventType,
        audit_type: str,
        occurred_at: datetime,
    ) -> None:
        await unit_of_work.conversations.add_event(
            ConversationEvent.create(
                conversation_id=conversation.id,
                event_type=event_type,
                actor_id=actor_id,
                subject_id=subject_id,
                occurred_at=occurred_at,
            )
        )
        await unit_of_work.outbox.add(
            OutboxEvent(
                id=uuid4(),
                created_at=occurred_at,
                updated_at=occurred_at,
                event_type="CONVERSATION_CREATED",
                aggregate_type="conversation",
                aggregate_id=conversation.id,
                protocol_version=1,
                payload={
                    "conversation_id": str(conversation.id),
                    "actor_id": str(actor_id),
                    "user_id": str(subject_id) if subject_id else None,
                    "changed_at": occurred_at.isoformat(),
                },
                available_at=occurred_at,
            )
        )
        await self._audit_writer.append(
            unit_of_work.audit,
            event_type=audit_type,
            occurred_at=occurred_at,
            actor_id=actor_id,
            source_ip=None,
            severity=AuditSeverity.INFORMATIONAL,
            details={
                "conversation_id": str(conversation.id),
                "subject_id": str(subject_id) if subject_id else None,
            },
        )
