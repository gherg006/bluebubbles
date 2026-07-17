"""Contact repository protocol."""

from typing import Protocol
from uuid import UUID

from bluebubbles.server.domain.contacts import Contact


class ContactRepository(Protocol):
    """Define directional contact relationship persistence."""

    async def get(self, owner_id: UUID, contact_id: UUID) -> Contact | None: ...

    async def list_for_owner(self, owner_id: UUID) -> list[Contact]: ...

    async def upsert(self, contact: Contact) -> Contact: ...

    async def delete(self, owner_id: UUID, contact_id: UUID) -> bool: ...
