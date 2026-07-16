"""Explicit ownership boundary for desktop client installation dependencies."""

from bluebubbles.client.configuration.settings import ClientSettings


class ClientContainer:
    """Own validated installation-wide client dependencies."""

    def __init__(self, settings: ClientSettings) -> None:
        """Store validated settings independently from authenticated user state."""
        self.settings = settings
        self._closed = False

    @property
    def closed(self) -> bool:
        """Report whether installation-scoped resources have been released."""
        return self._closed

    def close(self) -> None:
        """Release installation resources; none exist before later client stages."""
        self._closed = True
