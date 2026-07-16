"""Server dependency construction and startup validation boundary."""

from bluebubbles.server.configuration.settings import ServerSettings
from bluebubbles.server.configuration.validation import validate_server_settings
from bluebubbles.server.container import ServerContainer


def build_server_container(settings: ServerSettings) -> ServerContainer:
    """Validate settings and construct an explicit server container."""
    validate_server_settings(settings)
    return ServerContainer(settings)
