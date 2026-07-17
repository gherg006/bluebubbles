"""Authenticated-owner contact relationship use cases."""

from datetime import UTC, datetime
from uuid import UUID

from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.contacts import Contact
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.services.users import user_summary
from bluebubbles.shared.errors.exceptions import ConflictError, ResourceNotFoundError
from bluebubbles.shared.models.contacts import (
    AddContactRequest,
    ContactListResponse,
    ContactSummary,
    UpdateContactRequest,
)
from bluebubbles.shared.models.users import UserSummary


class ContactService:
    """Manage directional, owner-private contact metadata."""

    def __init__(self, unit_of_work_factory: UnitOfWorkFactory) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    async def list_contacts(self, requester: AuthenticatedUser) -> ContactListResponse:
        """Return contacts sorted by favourite, weight, and stable identity."""
        async with self._unit_of_work_factory() as unit_of_work:
            contacts = await unit_of_work.contacts.list_for_owner(requester.user_id)
            summaries: list[ContactSummary] = []
            for contact in contacts:
                user = await unit_of_work.users.get_by_id(contact.contact_id)
                if user is not None:
                    summaries.append(self._summary(contact, user_summary(user)))
        return ContactListResponse(contacts=tuple(summaries))

    async def add_contact(
        self, requester: AuthenticatedUser, request: AddContactRequest
    ) -> ContactSummary:
        """Add a distinct enabled user by canonical username."""
        async with self._unit_of_work_factory() as unit_of_work:
            target = await unit_of_work.users.get_by_normalised_username(
                request.username
            )
            if target is None or not target.is_enabled:
                raise ResourceNotFoundError()
            if target.id == requester.user_id:
                raise ConflictError(
                    user_message="You cannot add yourself as a contact."
                )
            existing = await unit_of_work.contacts.get(requester.user_id, target.id)
            if existing is not None:
                raise ConflictError(user_message="This contact already exists.")
            contact = Contact.create(owner_id=requester.user_id, contact_id=target.id)
            await unit_of_work.contacts.upsert(contact)
            await unit_of_work.commit()
        return self._summary(contact, user_summary(target))

    async def update_contact(
        self,
        requester: AuthenticatedUser,
        contact_id: UUID,
        request: UpdateContactRequest,
    ) -> ContactSummary:
        """Update an owner-specific nickname or favourite state."""
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as unit_of_work:
            contact = await unit_of_work.contacts.get(requester.user_id, contact_id)
            target = await unit_of_work.users.get_by_id(contact_id)
            if contact is None or target is None:
                raise ResourceNotFoundError()
            if "nickname" in request.model_fields_set:
                contact.set_nickname(request.nickname, now)
            if request.is_favourite is not None:
                contact.set_favourite(request.is_favourite, now)
            await unit_of_work.contacts.upsert(contact)
            await unit_of_work.commit()
        return self._summary(contact, user_summary(target))

    async def set_blocked(
        self, requester: AuthenticatedUser, contact_id: UUID, blocked: bool
    ) -> ContactSummary:
        """Set block state and clear favourite state when blocking."""
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as unit_of_work:
            contact = await unit_of_work.contacts.get(requester.user_id, contact_id)
            target = await unit_of_work.users.get_by_id(contact_id)
            if contact is None or target is None:
                raise ResourceNotFoundError()
            contact.set_blocked(blocked, now)
            await unit_of_work.contacts.upsert(contact)
            await unit_of_work.commit()
        return self._summary(contact, user_summary(target))

    async def remove_contact(
        self, requester: AuthenticatedUser, contact_id: UUID
    ) -> None:
        """Remove only a relationship owned by the authenticated user."""
        async with self._unit_of_work_factory() as unit_of_work:
            if not await unit_of_work.contacts.delete(requester.user_id, contact_id):
                raise ResourceNotFoundError()
            await unit_of_work.commit()

    @staticmethod
    def _summary(contact: Contact, user: UserSummary) -> ContactSummary:
        return ContactSummary(
            id=contact.contact_id,
            user=user,
            nickname=contact.nickname,
            is_favourite=contact.is_favourite,
            is_blocked=contact.is_blocked,
            last_contacted=contact.last_contacted,
        )
