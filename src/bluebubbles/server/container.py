"""Explicit ownership boundary for server-wide configuration and lifecycle."""

from bluebubbles.server.configuration.settings import ServerSettings


class ServerContainer:
    """Own application-wide server dependencies for the current stage."""

    def __init__(self, settings: ServerSettings) -> None:
        """Store validated settings without constructing later-stage services."""
        self.settings = settings
        self._started = False

    @property
    def started(self) -> bool:
        """Report whether this container currently owns started resources."""
        return self._started

    async def start(self) -> None:
        """Start resources idempotently; configuration owns no I/O resources yet."""
        self._started = True

    async def stop(self) -> None:
        """Stop owned resources idempotently in reverse construction order."""
        self._started = False
