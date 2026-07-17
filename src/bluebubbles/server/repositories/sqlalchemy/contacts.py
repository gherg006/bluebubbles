"""Async SQLAlchemy contact repository."""

from uuid import UUID, uuid5

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.contacts import ContactRelationshipORM
from bluebubbles.server.domain.contacts import Contact
from bluebubbles.server.repositories.sqlalchemy._common import flush_changes

_CONTACT_NAMESPACE = UUID("f9ace2e0-5dfb-4a99-9266-0d47b29c13d0")


class SqlAlchemyContactRepository:
    """Persist directional contact preferences and interaction weights."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, owner_id: UUID, contact_id: UUID) -> Contact | None:
        """Return one directional contact relationship."""
        record = await self._session.get(ContactRelationshipORM, (owner_id, contact_id))
        return self._to_domain(record) if record is not None else None

    async def list_for_owner(self, owner_id: UUID) -> list[Contact]:
        """Return one owner's contacts by useful descending weight."""
        statement = (
            select(ContactRelationshipORM)
            .where(ContactRelationshipORM.owner_user_id == owner_id)
            .order_by(
                ContactRelationshipORM.is_favourite.desc(),
                ContactRelationshipORM.weight.desc(),
                ContactRelationshipORM.contact_user_id,
            )
        )
        return [
            self._to_domain(record)
            for record in (await self._session.scalars(statement)).all()
        ]

    async def upsert(self, contact: Contact) -> Contact:
        """Insert or replace safe relationship preferences without committing."""
        record = await self._session.get(
            ContactRelationshipORM, (contact.owner_id, contact.contact_id)
        )
        if record is None:
            record = ContactRelationshipORM(
                owner_user_id=contact.owner_id,
                contact_user_id=contact.contact_id,
                nickname=contact.nickname,
                created_at=contact.created_at,
                updated_at=contact.updated_at,
            )
            self._session.add(record)
        record.is_favourite = contact.is_favourite
        record.nickname = contact.nickname
        record.is_blocked = contact.is_blocked
        record.weight = contact.weight_score
        record.last_contacted_at = contact.last_contacted
        record.updated_at = contact.updated_at
        await flush_changes(self._session)
        return contact

    async def delete(self, owner_id: UUID, contact_id: UUID) -> bool:
        """Delete one dependent directional relationship."""
        result = await self._session.execute(
            delete(ContactRelationshipORM).where(
                ContactRelationshipORM.owner_user_id == owner_id,
                ContactRelationshipORM.contact_user_id == contact_id,
            )
        )
        return result.rowcount == 1

    @staticmethod
    def _to_domain(record: ContactRelationshipORM) -> Contact:
        return Contact(
            id=uuid5(
                _CONTACT_NAMESPACE,
                f"{record.owner_user_id}:{record.contact_user_id}",
            ),
            created_at=record.created_at,
            updated_at=record.updated_at,
            owner_id=record.owner_user_id,
            contact_id=record.contact_user_id,
            nickname=record.nickname,
            is_favourite=record.is_favourite,
            is_blocked=record.is_blocked,
            last_contacted=record.last_contacted_at,
            weight_score=record.weight,
        )
