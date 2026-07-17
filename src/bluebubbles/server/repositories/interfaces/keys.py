"""Public-key repository protocol."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from bluebubbles.server.domain.users import PublicKeyRecord


class PublicKeyRepository(Protocol):
    """Define public-only versioned key persistence."""

    async def add(self, key: PublicKeyRecord, *, key_type: str) -> PublicKeyRecord: ...

    async def get_active(
        self, user_id: UUID, *, key_type: str
    ) -> PublicKeyRecord | None: ...

    async def list_for_user(self, user_id: UUID) -> list[PublicKeyRecord]: ...

    async def revoke(self, key_id: UUID, revoked_at: datetime, reason: str) -> bool: ...
