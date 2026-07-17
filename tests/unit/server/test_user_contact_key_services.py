"""Task 10 user, contact, and public-key service contracts."""

import base64
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from bluebubbles.server.domain.contacts import Contact
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import PublicKeyRecord, User
from bluebubbles.server.repositories.types import CursorPage
from bluebubbles.server.services.contacts import ContactService
from bluebubbles.server.services.keys import PublicKeyService
from bluebubbles.server.services.users import UserService
from bluebubbles.shared.errors.exceptions import ConflictError, ResourceNotFoundError
from bluebubbles.shared.models.contacts import AddContactRequest, UpdateContactRequest
from bluebubbles.shared.models.pagination import OpaqueCursor
from bluebubbles.shared.models.users import UpdateUserProfileRequest, UserSearchRequest
from bluebubbles.shared.security.fingerprints import calculate_public_key_fingerprint
from bluebubbles.shared.security.key_models import (
    KeyFingerprint,
    KeyVersion,
    PublicKeyAlgorithm,
    PublicKeyType,
    RegisterPublicKeyRequest,
    RevokePublicKeyRequest,
)

NOW = datetime(2026, 7, 17, 12, tzinfo=UTC)


class FakeUnitOfWork:
    """Expose configurable repository doubles through the UoW lifecycle shape."""

    def __init__(self) -> None:
        self.users = AsyncMock()
        self.authentication = AsyncMock()
        self.contacts = AsyncMock()
        self.public_keys = AsyncMock()
        self.conversations = AsyncMock()
        self.audit = AsyncMock()
        self.outbox = AsyncMock()
        self.commit = AsyncMock()

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(self, *args: object) -> None:
        del args


class FakeFactory:
    """Return supplied units in deterministic call order."""

    def __init__(self, *units: FakeUnitOfWork) -> None:
        self._units = list(units)

    def __call__(self) -> FakeUnitOfWork:
        return self._units.pop(0) if len(self._units) > 1 else self._units[0]


def _user(
    *, user_id: UUID | None = None, enabled: bool = True, name: str = "Alex"
) -> User:
    return User(
        id=user_id or uuid4(),
        created_at=NOW,
        updated_at=NOW,
        username=name.casefold(),
        display_name=name,
        role_id=uuid4(),
        department="IT",
        is_enabled=enabled,
    )


def _authenticated(user: User) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=user.id,
        session_id=uuid4(),
        username=user.username,
        role_id=user.role_id,
        permissions=frozenset(),
    )


@pytest.mark.asyncio
async def test_user_service_get_search_and_profile_update() -> None:
    """Profiles remain safe, searches are bounded, and own updates commit."""
    user = _user()
    get_uow = FakeUnitOfWork()
    get_uow.users.get_by_id.return_value = user
    get_uow.authentication.role_name.return_value = "Employee"
    service = UserService(cast(Any, FakeFactory(get_uow)))
    profile = await service.get_user(user.id)
    assert profile.display_name == "Alex" and profile.role == "Employee"

    search_uow = FakeUnitOfWork()
    disabled = _user(enabled=False, name="Hidden")
    search_uow.users.search.return_value = CursorPage(
        items=(user, disabled), next_cursor="next"
    )
    result = await UserService(cast(Any, FakeFactory(search_uow))).search_users(
        UserSearchRequest(
            query="al", department="IT", limit=2, after=OpaqueCursor("cursor")
        )
    )
    assert [item.id for item in result.users] == [user.id]
    assert result.page.has_more
    query = search_uow.users.search.await_args.args[0]
    assert query.department == "IT" and query.cursor == "cursor"

    update_uow = FakeUnitOfWork()
    update_uow.users.get_by_id.return_value = user
    update_uow.authentication.role_name.return_value = "Employee"
    updated = await UserService(cast(Any, FakeFactory(update_uow))).update_profile(
        _authenticated(user),
        UpdateUserProfileRequest(
            display_name="Alex M", status_message="Available", avatar="avatar-ref"
        ),
    )
    assert updated.display_name == "Alex M"
    assert updated.status_message == "Available"
    assert updated.avatar_url == "avatar-ref"
    update_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_user_service_conceals_missing_and_disabled_users() -> None:
    """Missing or disabled profiles use the same concealed failure."""
    for value in (None, _user(enabled=False)):
        unit = FakeUnitOfWork()
        unit.users.get_by_id.return_value = value
        with pytest.raises(ResourceNotFoundError):
            await UserService(cast(Any, FakeFactory(unit))).get_user(uuid4())


@pytest.mark.asyncio
async def test_contact_service_full_owner_lifecycle() -> None:
    """Contacts support add, list, nickname, favourite, block, and removal."""
    owner = _user(name="Owner")
    target = _user(name="Target")
    auth = _authenticated(owner)
    add_uow = FakeUnitOfWork()
    add_uow.users.get_by_normalised_username.return_value = target
    add_uow.contacts.get.return_value = None
    service = ContactService(cast(Any, FakeFactory(add_uow)))
    added = await service.add_contact(auth, AddContactRequest(username="TARGET"))
    assert added.id == target.id
    add_uow.contacts.upsert.assert_awaited_once()
    add_uow.commit.assert_awaited_once()

    contact = cast(Contact, add_uow.contacts.upsert.await_args.args[0])
    list_uow = FakeUnitOfWork()
    list_uow.contacts.list_for_owner.return_value = [contact]
    list_uow.users.get_by_id.return_value = target
    listed = await ContactService(cast(Any, FakeFactory(list_uow))).list_contacts(auth)
    assert listed.contacts[0].user.id == target.id

    update_uow = FakeUnitOfWork()
    update_uow.contacts.get.return_value = contact
    update_uow.users.get_by_id.return_value = target
    updated = await ContactService(cast(Any, FakeFactory(update_uow))).update_contact(
        auth,
        target.id,
        UpdateContactRequest(nickname=" T ", is_favourite=True),
    )
    assert updated.nickname == "T" and updated.is_favourite

    block_uow = FakeUnitOfWork()
    block_uow.contacts.get.return_value = contact
    block_uow.users.get_by_id.return_value = target
    blocked = await ContactService(cast(Any, FakeFactory(block_uow))).set_blocked(
        auth, target.id, True
    )
    assert blocked.is_blocked and not blocked.is_favourite

    remove_uow = FakeUnitOfWork()
    remove_uow.contacts.delete.return_value = True
    await ContactService(cast(Any, FakeFactory(remove_uow))).remove_contact(
        auth, target.id
    )
    remove_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_contact_service_rejects_invalid_relationships() -> None:
    """Unknown, self, duplicate, and non-owned relationships are rejected."""
    owner = _user(name="Owner")
    auth = _authenticated(owner)
    for target, existing in (
        (None, None),
        (owner, None),
        (_user(), Contact.create(owner_id=owner.id, contact_id=uuid4())),
    ):
        unit = FakeUnitOfWork()
        unit.users.get_by_normalised_username.return_value = target
        unit.contacts.get.return_value = existing
        with pytest.raises((ResourceNotFoundError, ConflictError)):
            await ContactService(cast(Any, FakeFactory(unit))).add_contact(
                auth, AddContactRequest(username="target")
            )
    missing = FakeUnitOfWork()
    missing.contacts.get.return_value = None
    missing.users.get_by_id.return_value = None
    with pytest.raises(ResourceNotFoundError):
        await ContactService(cast(Any, FakeFactory(missing))).update_contact(
            auth, uuid4(), UpdateContactRequest(is_favourite=True)
        )
    missing.contacts.delete.return_value = False
    with pytest.raises(ResourceNotFoundError):
        await ContactService(cast(Any, FakeFactory(missing))).remove_contact(
            auth, uuid4()
        )


def _registration(
    *,
    key_type: PublicKeyType = PublicKeyType.ENCRYPTION,
    algorithm: PublicKeyAlgorithm = PublicKeyAlgorithm.X25519_V1,
    version: int = 1,
    raw: bytes = b"k" * 32,
) -> RegisterPublicKeyRequest:
    fingerprint = calculate_public_key_fingerprint(
        raw,
        algorithm=algorithm.value,
        key_type=key_type.value,
        key_version=version,
    )
    return RegisterPublicKeyRequest(
        key_type=key_type,
        version=KeyVersion(value=version),
        algorithm=algorithm,
        public_key=base64.b64encode(raw).decode(),
        fingerprint=KeyFingerprint(value=fingerprint),
    )


def _key_service(unit: FakeUnitOfWork) -> PublicKeyService:
    return PublicKeyService(cast(Any, FakeFactory(unit)), cast(Any, AsyncMock()))


@pytest.mark.asyncio
async def test_public_key_registration_rotation_and_history() -> None:
    """Validated keys register independently and retained history is returned."""
    user = _user()
    auth = _authenticated(user)
    first_uow = FakeUnitOfWork()
    first_uow.users.get_by_id.return_value = user
    first_uow.public_keys.get_version.return_value = None
    first_uow.public_keys.get_active.return_value = None
    service = _key_service(first_uow)
    first = await service.register(auth, _registration())
    assert first.version.value == 1 and first.is_primary
    record = cast(PublicKeyRecord, first_uow.public_keys.add.await_args.args[0])

    history_uow = FakeUnitOfWork()
    history_uow.users.get_by_id.return_value = user
    history_uow.public_keys.list_for_user.return_value = [record]
    history = await _key_service(history_uow).list_for_user(user.id)
    assert history.keys == (first,)

    second_uow = FakeUnitOfWork()
    second_uow.users.get_by_id.return_value = user
    second_uow.public_keys.get_version.return_value = None
    second_uow.public_keys.get_active.return_value = record
    second = await _key_service(second_uow).register(
        auth, _registration(version=2, raw=b"n" * 32)
    )
    assert second.version.value == 2


@pytest.mark.asyncio
async def test_public_key_registration_rejects_invalid_or_conflicting_data() -> None:
    """Purpose, fingerprint, version, conflict, and user checks fail closed."""
    user = _user()
    auth = _authenticated(user)
    with pytest.raises(ConflictError):
        await _key_service(FakeUnitOfWork()).register(
            auth,
            _registration(algorithm=PublicKeyAlgorithm.ED25519_V1),
        )
    with pytest.raises(ConflictError):
        await _key_service(FakeUnitOfWork()).register(
            auth, _registration().model_copy(update={"expires_at": NOW})
        )
    bad = _registration().model_copy(
        update={"fingerprint": KeyFingerprint(value="0000-" * 15 + "0000")}
    )
    with pytest.raises(ConflictError):
        await _key_service(FakeUnitOfWork()).register(auth, bad)

    existing = PublicKeyRecord.create(
        user_id=user.id,
        key_version=1,
        algorithm=PublicKeyAlgorithm.X25519_V1.value,
        public_key=b"x" * 32,
        fingerprint=_registration(raw=b"x" * 32).fingerprint.value,
    )
    conflict_uow = FakeUnitOfWork()
    conflict_uow.users.get_by_id.return_value = user
    conflict_uow.public_keys.get_version.return_value = existing
    with pytest.raises(ConflictError):
        await _key_service(conflict_uow).register(auth, _registration())

    version_uow = FakeUnitOfWork()
    version_uow.users.get_by_id.return_value = user
    version_uow.public_keys.get_version.return_value = None
    version_uow.public_keys.get_active.return_value = existing
    with pytest.raises(ConflictError):
        await _key_service(version_uow).register(auth, _registration(version=3))

    missing_uow = FakeUnitOfWork()
    missing_uow.users.get_by_id.return_value = None
    with pytest.raises(ResourceNotFoundError):
        await _key_service(missing_uow).list_for_user(uuid4())


@pytest.mark.asyncio
async def test_public_key_revocation_is_owned_audited_and_published() -> None:
    """Only an owner can revoke, and the change commits with audit/outbox facts."""
    user = _user()
    auth = _authenticated(user)
    record = PublicKeyRecord.create(
        user_id=user.id,
        key_version=1,
        algorithm=PublicKeyAlgorithm.X25519_V1.value,
        public_key=b"k" * 32,
        fingerprint=_registration().fingerprint.value,
    )
    unit = FakeUnitOfWork()
    unit.public_keys.get_by_id.return_value = record
    unit.public_keys.revoke.return_value = True
    await _key_service(unit).revoke(
        auth, record.id, RevokePublicKeyRequest(reason="Device reset")
    )
    unit.public_keys.revoke.assert_awaited_once()
    unit.outbox.add.assert_awaited_once()
    unit.commit.assert_awaited_once()

    missing = FakeUnitOfWork()
    missing.public_keys.get_by_id.return_value = None
    with pytest.raises(ResourceNotFoundError):
        await _key_service(missing).revoke(
            auth, uuid4(), RevokePublicKeyRequest(reason="Unknown")
        )
