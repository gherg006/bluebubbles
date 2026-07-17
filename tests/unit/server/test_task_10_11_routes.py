"""Thin route delegation tests for Tasks 10 and 11."""

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from bluebubbles.server.container import ServerContainer
from bluebubbles.server.routes import contacts, conversations, groups, keys, users
from bluebubbles.shared.models.contacts import (
    AddContactRequest,
    BlockContactRequest,
    UpdateContactRequest,
)
from bluebubbles.shared.models.conversations import (
    AddGroupMemberRequest,
    ArchiveConversationRequest,
    ChangeGroupRoleRequest,
    CreateDirectConversationRequest,
    CreateGroupConversationRequest,
    GroupRole,
    TransferOwnershipRequest,
    UpdateGroupRequest,
)
from bluebubbles.shared.models.users import UpdateUserProfileRequest
from bluebubbles.shared.security.key_models import RevokePublicKeyRequest
from tests.unit.server.test_user_contact_key_services import (
    _authenticated,
    _registration,
    _user,
)


def _container(**services: object) -> ServerContainer:
    return cast(
        ServerContainer,
        SimpleNamespace(services=SimpleNamespace(**services)),
    )


@pytest.mark.asyncio
async def test_user_contact_and_key_routes_delegate_without_policy() -> None:
    """Task 10 routes pass authenticated commands to their services."""
    actor = _user()
    current = _authenticated(actor)
    user_service = AsyncMock()
    user_service.search_users.return_value = object()
    user_service.get_user.return_value = object()
    user_service.update_profile.return_value = object()
    key_service = AsyncMock()
    key_service.register.return_value = object()
    key_service.revoke.return_value = None
    key_service.list_for_user.return_value = object()
    user_container = _container(users=user_service, public_keys=key_service)
    assert (
        await users.search_users(current, user_container, "alex", "IT", 10, "cursor")
        is user_service.search_users.return_value
    )
    assert (
        await users.get_user(actor.id, current, user_container)
        is user_service.get_user.return_value
    )
    profile_request = UpdateUserProfileRequest(display_name="Alex")
    assert (
        await users.update_profile(profile_request, current, user_container)
        is user_service.update_profile.return_value
    )
    assert (
        await users.get_user_keys(actor.id, current, user_container)
        is key_service.list_for_user.return_value
    )

    contact_service = AsyncMock()
    for name in (
        "list_contacts",
        "add_contact",
        "update_contact",
        "set_blocked",
    ):
        getattr(contact_service, name).return_value = object()
    contact_service.remove_contact.return_value = None
    contact_container = _container(contacts=contact_service)
    target_id = uuid4()
    assert (
        await contacts.list_contacts(current, contact_container)
        is contact_service.list_contacts.return_value
    )
    assert (
        await contacts.add_contact(
            AddContactRequest(username="target"), current, contact_container
        )
        is contact_service.add_contact.return_value
    )
    update = UpdateContactRequest(nickname="T", is_favourite=True)
    assert (
        await contacts.update_contact(target_id, update, current, contact_container)
        is contact_service.update_contact.return_value
    )
    assert (
        await contacts.favourite_contact(target_id, update, current, contact_container)
        is contact_service.update_contact.return_value
    )
    assert (
        await contacts.block_contact(
            target_id, BlockContactRequest(blocked=True), current, contact_container
        )
        is contact_service.set_blocked.return_value
    )
    response = await contacts.remove_contact(target_id, current, contact_container)
    assert response.status_code == 204

    key_container = _container(public_keys=key_service)
    assert (
        await keys.register_key(_registration(), current, key_container)
        is key_service.register.return_value
    )
    revoked = await keys.revoke_key(
        target_id,
        RevokePublicKeyRequest(reason="Device reset"),
        current,
        key_container,
    )
    assert revoked.status_code == 204


@pytest.mark.asyncio
async def test_conversation_and_group_routes_delegate_without_policy() -> None:
    """Task 11 routes remain transport-only and return documented 204 results."""
    actor = _user()
    current = _authenticated(actor)
    conversation_service = AsyncMock()
    for name in ("list_for_user", "create_direct", "create_group", "get_conversation"):
        getattr(conversation_service, name).return_value = object()
    conversation_container = _container(conversations=conversation_service)
    assert (
        await conversations.list_conversations(
            current, conversation_container, 10, "cursor", True
        )
        is conversation_service.list_for_user.return_value
    )
    target_id = uuid4()
    assert (
        await conversations.create_direct(
            CreateDirectConversationRequest(target_user_id=target_id),
            current,
            conversation_container,
        )
        is conversation_service.create_direct.return_value
    )
    assert (
        await conversations.create_group(
            CreateGroupConversationRequest(name="Team", member_ids=(target_id,)),
            current,
            conversation_container,
        )
        is conversation_service.create_group.return_value
    )
    conversation_id = uuid4()
    assert (
        await conversations.get_conversation(
            conversation_id, current, conversation_container
        )
        is conversation_service.get_conversation.return_value
    )
    archived = await conversations.archive_conversation(
        conversation_id,
        ArchiveConversationRequest(archived=True),
        current,
        conversation_container,
    )
    assert archived.status_code == 204

    group_service = AsyncMock()
    group_container = _container(groups=group_service)
    responses = (
        await groups.update_group(
            conversation_id,
            UpdateGroupRequest(name="Renamed"),
            current,
            group_container,
        ),
        await groups.add_member(
            conversation_id,
            AddGroupMemberRequest(user_id=target_id),
            current,
            group_container,
        ),
        await groups.remove_member(
            conversation_id, target_id, current, group_container
        ),
        await groups.change_role(
            conversation_id,
            ChangeGroupRoleRequest(user_id=target_id, role=GroupRole.MODERATOR),
            current,
            group_container,
        ),
        await groups.leave_group(conversation_id, current, group_container),
        await groups.transfer_ownership(
            conversation_id,
            TransferOwnershipRequest(new_owner_id=target_id),
            current,
            group_container,
        ),
    )
    assert all(response.status_code == 204 for response in responses)


def test_task_route_helpers_fail_when_service_is_not_configured() -> None:
    """A construction error is explicit rather than silently bypassing policy."""
    empty = cast(ServerContainer, SimpleNamespace(services=SimpleNamespace()))
    for helper in (
        users._service,
        users._key_service,
        contacts._service,
        keys._service,
        conversations._service,
        groups._service,
    ):
        with pytest.raises((AttributeError, RuntimeError)):
            cast(Any, helper)(empty)
