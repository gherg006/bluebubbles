"""Operating-system-protected master-key lifecycle for one client profile."""

from __future__ import annotations

import asyncio
import secrets
from uuid import UUID

from bluebubbles.client.security.secure_store import SecureStore
from bluebubbles.shared.errors.exceptions import LocalStorageError


class ProfileLocalKeyProvider:
    """Retrieve or create one random 256-bit local profile master key."""

    def __init__(self, secure_store: SecureStore, profile_id: UUID) -> None:
        self._secure_store = secure_store
        self._profile_id = profile_id
        self._key: bytearray | None = None
        self._lock = asyncio.Lock()

    async def get_master_key(self) -> bytes:
        """Return the in-memory key, creating it in the secure store if absent."""
        async with self._lock:
            if self._key is None:
                name = self._name
                stored = await self._secure_store.get_secret(name)
                if stored is None:
                    stored = secrets.token_bytes(32)
                    await self._secure_store.set_secret(name, stored)
                if len(stored) != 32:
                    raise LocalStorageError(
                        user_message="The local profile protection key is invalid."
                    )
                self._key = bytearray(stored)
            return bytes(self._key)

    async def lock(self) -> None:
        """Overwrite and discard the in-memory key copy where Python permits."""
        async with self._lock:
            if self._key is not None:
                self._key[:] = b"\x00" * len(self._key)
                self._key = None

    async def destroy(self) -> None:
        """Remove the protected key and discard its in-memory copy."""
        await self.lock()
        await self._secure_store.delete_secret(self._name)

    @property
    def _name(self) -> str:
        return f"profile:{self._profile_id}:local_master_key"

