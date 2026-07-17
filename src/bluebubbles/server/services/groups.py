"""Group metadata, membership, role, and ownership use cases."""

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
from bluebubbles.server.services.audit import AuthenticationAuditWriter
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.shared.errors.exceptions import (
    AuthorisationError,
    ConflictError,
    ResourceNotFoundError,
)
from bluebubbles.shared.models.conversations import GroupRole, UpdateGroupRequest

_ROLE_RANK = {
    GroupRole.MEMBER: 10,
    GroupRole.MODERATOR: 20,
    GroupRole.OWNER: 30,
}


class GroupService:
    """Enforce group role hierarchy inside explicit database transactions."""

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

    async def add_member(
        self, requester: AuthenticatedUser, group_id: UUID, target_user_id: UUID
    ) -> None:
        """Allow an owner or moderator to add one enabled non-member."""
        await self._permission_service.require_authenticated_permission(
            requester, Permission.CREATE_GROUP
        )
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as unit_of_work:
            group = await self._locked_group(unit_of_work, group_id)
            actor = self._require_role(group, requester.user_id, GroupRole.MODERATOR)
            target = await unit_of_work.users.get_by_id(target_user_id)
            if target is None or not target.is_enabled:
                raise ResourceNotFoundError()
            if group.active_member(target_user_id) is not None:
                raise ConflictError(user_message="The user is already a group member.")
            if len(group.members) >= self._maximum_group_members:
                raise ConflictError(user_message="The group member limit was reached.")
            member = ConversationMember.create(
                conversation_id=group.id,
                user_id=target_user_id,
                role=GroupRole.MEMBER,
                joined_at=now,
            )
            await unit_of_work.conversations.add_member(member)
            await self._record(
                unit_of_work,
                group,
                actor.user_id,
                target_user_id,
                ConversationEventType.MEMBER_ADDED,
                "group_member_added",
                now,
            )
            await unit_of_work.commit()

    async def remove_member(
        self, requester: AuthenticatedUser, group_id: UUID, target_user_id: UUID
    ) -> None:
        """Require a strictly higher role and prohibit owner removal."""
        await self._permission_service.require_authenticated_permission(
            requester, Permission.CREATE_GROUP
        )
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as unit_of_work:
            group = await self._locked_group(unit_of_work, group_id)
            actor = self._active_member(group, requester.user_id)
            target = self._active_member(group, target_user_id)
            if requester.user_id == target_user_id:
                raise ConflictError(user_message="Use the leave-group operation.")
            if not self._can_manage_target(actor.role, target.role):
                raise AuthorisationError()
            if not await unit_of_work.conversations.remove_member(
                target.id, now, expected_version=target.version
            ):
                raise ConflictError()
            await self._record(
                unit_of_work,
                group,
                actor.user_id,
                target.user_id,
                ConversationEventType.MEMBER_REMOVED,
                "group_member_removed",
                now,
            )
            await unit_of_work.commit()

    async def leave_group(self, requester: AuthenticatedUser, group_id: UUID) -> None:
        """Allow a non-owner to end only their own membership."""
        await self._permission_service.require_authenticated_permission(
            requester, Permission.SEND_MESSAGE
        )
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as unit_of_work:
            group = await self._locked_group(unit_of_work, group_id)
            member = self._active_member(group, requester.user_id)
            if member.role is GroupRole.OWNER:
                raise ConflictError(
                    user_message="Transfer ownership before leaving the group."
                )
            if not await unit_of_work.conversations.remove_member(
                member.id, now, expected_version=member.version
            ):
                raise ConflictError()
            await self._record(
                unit_of_work,
                group,
                requester.user_id,
                requester.user_id,
                ConversationEventType.MEMBER_LEFT,
                "group_member_left",
                now,
            )
            await unit_of_work.commit()

    async def change_member_role(
        self,
        requester: AuthenticatedUser,
        group_id: UUID,
        target_user_id: UUID,
        role: GroupRole,
    ) -> None:
        """Allow only the owner to promote or demote a non-owner."""
        await self._permission_service.require_authenticated_permission(
            requester, Permission.CREATE_GROUP
        )
        if role not in {GroupRole.MEMBER, GroupRole.MODERATOR}:
            raise ConflictError(
                user_message="Use ownership transfer for the owner role."
            )
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as unit_of_work:
            group = await self._locked_group(unit_of_work, group_id)
            actor = self._require_role(group, requester.user_id, GroupRole.OWNER)
            target = self._active_member(group, target_user_id)
            if target.role is GroupRole.OWNER or target.user_id == actor.user_id:
                raise ConflictError(
                    user_message="The owner role cannot be changed here."
                )
            if target.role is role:
                return
            if not await unit_of_work.conversations.change_member_role(
                target.id, role, expected_version=target.version
            ):
                raise ConflictError()
            await self._record(
                unit_of_work,
                group,
                actor.user_id,
                target.user_id,
                ConversationEventType.ROLE_CHANGED,
                "group_role_changed",
                now,
            )
            await unit_of_work.commit()

    async def transfer_ownership(
        self, requester: AuthenticatedUser, group_id: UUID, target_user_id: UUID
    ) -> None:
        """Atomically demote the current owner and promote an active target."""
        await self._permission_service.require_authenticated_permission(
            requester, Permission.CREATE_GROUP
        )
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as unit_of_work:
            group = await self._locked_group(unit_of_work, group_id)
            owner = self._require_role(group, requester.user_id, GroupRole.OWNER)
            target = self._active_member(group, target_user_id)
            if target.user_id == owner.user_id:
                raise ConflictError(user_message="Choose another active member.")
            if not await unit_of_work.conversations.change_member_role(
                owner.id, GroupRole.MODERATOR, expected_version=owner.version
            ):
                raise ConflictError()
            if not await unit_of_work.conversations.change_member_role(
                target.id, GroupRole.OWNER, expected_version=target.version
            ):
                raise ConflictError()
            await self._record(
                unit_of_work,
                group,
                owner.user_id,
                target.user_id,
                ConversationEventType.OWNERSHIP_TRANSFERRED,
                "group_ownership_transferred",
                now,
            )
            await unit_of_work.commit()

    async def update_group(
        self,
        requester: AuthenticatedUser,
        group_id: UUID,
        request: UpdateGroupRequest,
    ) -> None:
        """Allow owner/moderator metadata updates with domain validation."""
        await self._permission_service.require_authenticated_permission(
            requester, Permission.CREATE_GROUP
        )
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as unit_of_work:
            group = await self._locked_group(unit_of_work, group_id)
            actor = self._require_role(group, requester.user_id, GroupRole.MODERATOR)
            expected = group.version
            if request.name is not None:
                group.rename(request.name, now)
            if "description" in request.model_fields_set:
                group.description = request.description
                if group.version == expected:
                    group.touch(now)
            await unit_of_work.conversations.update(group, expected_version=expected)
            await self._record(
                unit_of_work,
                group,
                actor.user_id,
                None,
                ConversationEventType.RENAMED,
                "group_updated",
                now,
            )
            await unit_of_work.commit()

    async def _locked_group(
        self, unit_of_work: UnitOfWork, group_id: UUID
    ) -> Conversation:
        group = await unit_of_work.conversations.get_by_id(group_id, for_update=True)
        if group is None or group.conversation_type.value != "group":
            raise ResourceNotFoundError()
        return group

    @staticmethod
    def _active_member(group: Conversation, user_id: UUID) -> ConversationMember:
        member = group.active_member(user_id)
        if member is None:
            raise ResourceNotFoundError()
        return member

    def _require_role(
        self, group: Conversation, user_id: UUID, minimum: GroupRole
    ) -> ConversationMember:
        member = self._active_member(group, user_id)
        if _ROLE_RANK[member.role] < _ROLE_RANK[minimum]:
            raise AuthorisationError()
        return member

    @staticmethod
    def _can_manage_target(actor: GroupRole, target: GroupRole) -> bool:
        """Require strict hierarchy; moderators can remove members only."""
        return _ROLE_RANK[actor] > _ROLE_RANK[target]

    async def _record(
        self,
        unit_of_work: UnitOfWork,
        group: Conversation,
        actor_id: UUID,
        subject_id: UUID | None,
        event_type: ConversationEventType,
        audit_type: str,
        occurred_at: datetime,
    ) -> None:
        await unit_of_work.conversations.add_event(
            ConversationEvent.create(
                conversation_id=group.id,
                event_type=event_type,
                actor_id=actor_id,
                subject_id=subject_id,
                occurred_at=occurred_at,
            )
        )
        if event_type is ConversationEventType.MEMBER_ADDED:
            outbox_type = "GROUP_MEMBER_ADDED"
        elif event_type in {
            ConversationEventType.MEMBER_REMOVED,
            ConversationEventType.MEMBER_LEFT,
        }:
            outbox_type = "GROUP_MEMBER_REMOVED"
        elif event_type in {
            ConversationEventType.ROLE_CHANGED,
            ConversationEventType.OWNERSHIP_TRANSFERRED,
        }:
            outbox_type = "GROUP_ROLE_UPDATED"
        else:
            outbox_type = "GROUP_UPDATED"
        await unit_of_work.outbox.add(
            OutboxEvent(
                id=uuid4(),
                created_at=occurred_at,
                updated_at=occurred_at,
                event_type=outbox_type,
                aggregate_type="conversation",
                aggregate_id=group.id,
                protocol_version=1,
                payload={
                    "conversation_id": str(group.id),
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
                "conversation_id": str(group.id),
                "subject_id": str(subject_id) if subject_id else None,
            },
        )
