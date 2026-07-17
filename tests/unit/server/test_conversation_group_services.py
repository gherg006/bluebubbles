"""Task 11 direct and group conversation service contracts."""

from collections.abc import Callable, Coroutine
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError as PydanticValidationError

from bluebubbles.server.domain.contacts import Contact
from bluebubbles.server.domain.conversations import Conversation, ConversationMember
from bluebubbles.server.domain.users import Permission, User
from bluebubbles.server.repositories.types import ConversationListQuery, CursorPage
from bluebubbles.server.services.conversations import ConversationService
from bluebubbles.server.services.groups import GroupService
from bluebubbles.shared.errors.exceptions import (
    AuthorisationError,
    ConflictError,
    ResourceNotFoundError,
)
from bluebubbles.shared.models.conversations import (
    ConversationType,
    CreateDirectConversationRequest,
    CreateGroupConversationRequest,
    GroupRole,
    UpdateGroupRequest,
)
from tests.unit.server.test_user_contact_key_services import (
    NOW,
    FakeFactory,
    FakeUnitOfWork,
    _authenticated,
    _user,
)


def _permission() -> AsyncMock:
    service = AsyncMock()
    service.require_authenticated_permission.return_value = None
    return service


def _audit() -> AsyncMock:
    writer = AsyncMock()
    writer.append.return_value = None
    return writer


def _conversation(
    owner: User,
    *others: User,
    direct: bool = False,
    moderator: User | None = None,
) -> Conversation:
    conversation = Conversation(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        conversation_type=(
            ConversationType.DIRECT if direct else ConversationType.GROUP
        ),
        title=None if direct else "Team",
        created_by=owner.id,
        last_activity=NOW,
    )
    for user in (owner, *others):
        role = GroupRole.MEMBER
        if not direct and user.id == owner.id:
            role = GroupRole.OWNER
        elif moderator is not None and user.id == moderator.id:
            role = GroupRole.MODERATOR
        conversation.add_member(
            ConversationMember.create(
                conversation_id=conversation.id,
                user_id=user.id,
                role=role,
                joined_at=NOW,
            ),
            NOW,
        )
    return conversation


def _user_lookup(
    *users: User,
) -> Callable[..., Coroutine[Any, Any, User | None]]:
    values = {user.id: user for user in users}

    async def lookup(user_id: UUID, **kwargs: object) -> User | None:
        del kwargs
        return values.get(user_id)

    return lookup


def _conversation_service(*units: FakeUnitOfWork) -> ConversationService:
    return ConversationService(
        cast(Any, FakeFactory(*units)),
        cast(Any, _permission()),
        cast(Any, _audit()),
        maximum_group_members=4,
    )


@pytest.mark.asyncio
async def test_create_direct_reuses_and_creates_unique_conversation() -> None:
    """A canonical pair is reused or atomically created with both members."""
    actor = _user(name="Actor")
    target = _user(name="Target")
    auth = _authenticated(actor)
    existing = _conversation(actor, target, direct=True)
    reuse_uow = FakeUnitOfWork()
    reuse_uow.conversations.find_direct_pair.return_value = existing
    reuse_uow.users.get_by_id.side_effect = _user_lookup(actor, target)
    reused = await _conversation_service(reuse_uow).create_direct(
        auth, CreateDirectConversationRequest(target_user_id=target.id)
    )
    assert reused.id == existing.id and reused.title == "Target"
    reuse_uow.commit.assert_not_awaited()

    create_uow = FakeUnitOfWork()
    create_uow.conversations.find_direct_pair.return_value = None
    create_uow.users.get_by_id.side_effect = _user_lookup(actor, target)
    create_uow.contacts.get.return_value = None
    create_uow.authentication.permissions_for_role.return_value = frozenset(
        {Permission.SEND_MESSAGE}
    )
    created = await _conversation_service(create_uow).create_direct(
        auth, CreateDirectConversationRequest(target_user_id=target.id)
    )
    assert created.type is ConversationType.DIRECT
    assert {item.id for item in created.participants} == {actor.id, target.id}
    create_uow.conversations.create_direct.assert_awaited_once()
    create_uow.conversations.add_event.assert_awaited_once()
    create_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_direct_rejects_self_missing_and_blocks() -> None:
    """Direct creation fails for self, unknown targets, or either block direction."""
    actor = _user(name="Actor")
    target = _user(name="Target")
    auth = _authenticated(actor)
    with pytest.raises(ConflictError):
        await _conversation_service(FakeUnitOfWork()).create_direct(
            auth, CreateDirectConversationRequest(target_user_id=actor.id)
        )
    missing = FakeUnitOfWork()
    missing.conversations.find_direct_pair.return_value = None
    missing.users.get_by_id.side_effect = _user_lookup(actor)
    with pytest.raises(ResourceNotFoundError):
        await _conversation_service(missing).create_direct(
            auth, CreateDirectConversationRequest(target_user_id=target.id)
        )
    blocked = FakeUnitOfWork()
    blocked.conversations.find_direct_pair.return_value = None
    blocked.users.get_by_id.side_effect = _user_lookup(actor, target)
    blocked.authentication.permissions_for_role.return_value = frozenset(
        {Permission.SEND_MESSAGE}
    )
    blocked.contacts.get.side_effect = [
        Contact.create(owner_id=actor.id, contact_id=target.id, is_blocked=True),
        None,
    ]
    with pytest.raises(ConflictError):
        await _conversation_service(blocked).create_direct(
            auth, CreateDirectConversationRequest(target_user_id=target.id)
        )


@pytest.mark.asyncio
async def test_group_creation_get_list_and_archive() -> None:
    """Group creation validates members and retrieval remains membership scoped."""
    owner = _user(name="Owner")
    member = _user(name="Member")
    auth = _authenticated(owner)
    create_uow = FakeUnitOfWork()
    create_uow.users.get_by_id.side_effect = _user_lookup(owner, member)
    service = _conversation_service(create_uow)
    response = await service.create_group(
        auth,
        CreateGroupConversationRequest(name=" Team ", member_ids=(member.id,)),
    )
    group = cast(Conversation, create_uow.conversations.create_group.await_args.args[0])
    assert response.title == "Team"
    assert group.active_member(owner.id).role is GroupRole.OWNER  # type: ignore[union-attr]
    create_uow.commit.assert_awaited_once()

    get_uow = FakeUnitOfWork()
    get_uow.conversations.get_by_id.return_value = group
    get_uow.users.get_by_id.side_effect = _user_lookup(owner, member)
    fetched = await _conversation_service(get_uow).get_conversation(auth, group.id)
    assert len(fetched.participant_details) == 2

    list_uow = FakeUnitOfWork()
    list_uow.conversations.list_for_user.return_value = CursorPage(
        items=(group,), next_cursor="next"
    )
    list_uow.users.get_by_id.side_effect = _user_lookup(owner, member)
    listed = await _conversation_service(list_uow).list_for_user(
        auth, ConversationListQuery(user_id=owner.id, limit=2)
    )
    assert listed.page.has_more and listed.items[0].id == group.id

    archive_uow = FakeUnitOfWork()
    archive_uow.conversations.get_active_membership.return_value = group.active_member(
        owner.id
    )
    archive_uow.conversations.set_archived.return_value = True
    await _conversation_service(archive_uow).archive_for_user(auth, group.id, True)
    archive_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_group_creation_and_access_fail_closed() -> None:
    """Group size, enabled membership, ownership, and optimistic checks are enforced."""
    owner = _user(name="Owner")
    auth = _authenticated(owner)
    with pytest.raises(PydanticValidationError):
        CreateGroupConversationRequest(name="bad\nname", member_ids=(uuid4(),))
    with pytest.raises(ConflictError):
        await _conversation_service(FakeUnitOfWork()).create_group(
            auth, CreateGroupConversationRequest(name="Team", member_ids=(owner.id,))
        )
    users = tuple(_user(name=f"U{index}") for index in range(4))
    with pytest.raises(ConflictError):
        await _conversation_service(FakeUnitOfWork()).create_group(
            auth,
            CreateGroupConversationRequest(
                name="Team", member_ids=tuple(user.id for user in users)
            ),
        )
    disabled = _user(enabled=False)
    missing = FakeUnitOfWork()
    missing.users.get_by_id.side_effect = _user_lookup(owner, disabled)
    with pytest.raises(ResourceNotFoundError):
        await _conversation_service(missing).create_group(
            auth,
            CreateGroupConversationRequest(name="Team", member_ids=(disabled.id,)),
        )
    concealed = FakeUnitOfWork()
    concealed.conversations.get_by_id.return_value = None
    with pytest.raises(ResourceNotFoundError):
        await _conversation_service(concealed).get_conversation(auth, uuid4())
    bad_query = ConversationListQuery(user_id=uuid4())
    with pytest.raises(ResourceNotFoundError):
        await _conversation_service(FakeUnitOfWork()).list_for_user(auth, bad_query)
    archive = FakeUnitOfWork()
    archive.conversations.get_active_membership.return_value = None
    with pytest.raises(ResourceNotFoundError):
        await _conversation_service(archive).archive_for_user(auth, uuid4(), True)


def _group_service(*units: FakeUnitOfWork) -> GroupService:
    return GroupService(
        cast(Any, FakeFactory(*units)),
        cast(Any, _permission()),
        cast(Any, _audit()),
        maximum_group_members=4,
    )


@pytest.mark.asyncio
async def test_group_membership_role_and_ownership_lifecycle() -> None:
    """Owner/moderator hierarchy governs add, remove, roles, leave, and transfer."""
    owner = _user(name="Owner")
    moderator = _user(name="Moderator")
    member = _user(name="Member")
    target = _user(name="Target")
    group = _conversation(owner, moderator, member, moderator=moderator)

    add = FakeUnitOfWork()
    add.conversations.get_by_id.return_value = group
    add.users.get_by_id.return_value = target
    await _group_service(add).add_member(_authenticated(moderator), group.id, target.id)
    add.conversations.add_member.assert_awaited_once()
    add.commit.assert_awaited_once()

    remove = FakeUnitOfWork()
    remove.conversations.get_by_id.return_value = group
    remove.conversations.remove_member.return_value = True
    await _group_service(remove).remove_member(
        _authenticated(moderator), group.id, member.id
    )
    remove.commit.assert_awaited_once()

    role = FakeUnitOfWork()
    role.conversations.get_by_id.return_value = group
    role.conversations.change_member_role.return_value = True
    await _group_service(role).change_member_role(
        _authenticated(owner), group.id, member.id, GroupRole.MODERATOR
    )
    role.commit.assert_awaited_once()

    leave = FakeUnitOfWork()
    leave.conversations.get_by_id.return_value = group
    leave.conversations.remove_member.return_value = True
    await _group_service(leave).leave_group(_authenticated(member), group.id)
    leave.commit.assert_awaited_once()

    transfer = FakeUnitOfWork()
    transfer.conversations.get_by_id.return_value = group
    transfer.conversations.change_member_role.return_value = True
    await _group_service(transfer).transfer_ownership(
        _authenticated(owner), group.id, member.id
    )
    assert transfer.conversations.change_member_role.await_count == 2
    transfer.commit.assert_awaited_once()

    rename = FakeUnitOfWork()
    rename.conversations.get_by_id.return_value = group
    await _group_service(rename).update_group(
        _authenticated(moderator),
        group.id,
        UpdateGroupRequest(name="Renamed", description="Description"),
    )
    assert group.title == "Renamed" and group.description == "Description"
    rename.conversations.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_group_service_rejects_invalid_hierarchy_and_state() -> None:
    """Missing groups, lower roles, owners, self-removal, and limits fail closed."""
    owner = _user(name="Owner")
    moderator = _user(name="Moderator")
    member = _user(name="Member")
    group = _conversation(owner, moderator, member, moderator=moderator)
    missing = FakeUnitOfWork()
    missing.conversations.get_by_id.return_value = None
    with pytest.raises(ResourceNotFoundError):
        await _group_service(missing).leave_group(_authenticated(member), uuid4())

    lower = FakeUnitOfWork()
    lower.conversations.get_by_id.return_value = group
    with pytest.raises(AuthorisationError):
        await _group_service(lower).remove_member(
            _authenticated(member), group.id, moderator.id
        )
    with pytest.raises(ConflictError):
        await _group_service(lower).remove_member(
            _authenticated(member), group.id, member.id
        )
    with pytest.raises(ConflictError):
        await _group_service(lower).leave_group(_authenticated(owner), group.id)
    with pytest.raises(ConflictError):
        await _group_service(lower).change_member_role(
            _authenticated(owner), group.id, member.id, GroupRole.OWNER
        )
    with pytest.raises(ConflictError):
        await _group_service(lower).transfer_ownership(
            _authenticated(owner), group.id, owner.id
        )

    full_group = _conversation(owner, moderator, member, _user(), moderator=moderator)
    full = FakeUnitOfWork()
    full.conversations.get_by_id.return_value = full_group
    full.users.get_by_id.return_value = _user()
    with pytest.raises(ConflictError):
        await _group_service(full).add_member(
            _authenticated(owner), full_group.id, uuid4()
        )
