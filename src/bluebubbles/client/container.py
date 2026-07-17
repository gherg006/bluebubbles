"""Explicit ownership boundary for desktop client installation dependencies."""

import asyncio

from bluebubbles.client.configuration.settings import ClientSettings
from bluebubbles.client.storage.service import LocalStorageService


class ClientContainer:
    """Own validated installation-wide client dependencies."""

    def __init__(
        self,
        settings: ClientSettings,
        local_storage: LocalStorageService | None = None,
    ) -> None:
        """Store validated settings independently from authenticated user state."""
        self.settings = settings
        self.local_storage = local_storage
        self._closed = False

    async def start(self) -> None:
        """Initialise authenticated user resources owned by this container."""
        if self.local_storage is not None:
            await self.local_storage.initialise()

    async def stop(self) -> None:
        """Release authenticated resources in reverse ownership order."""
        if self.local_storage is not None:
            await self.local_storage.close()
        self._closed = True

    @property
    def closed(self) -> bool:
        """Report whether installation-scoped resources have been released."""
        return self._closed

    def close(self) -> None:
        """Synchronously close only when no asynchronous event loop owns resources."""
        if self.local_storage is not None and self.local_storage.database.is_open:
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                asyncio.run(self.stop())
                return
            raise RuntimeError("Use 'await container.stop()' for authenticated storage")
        self._closed = True
