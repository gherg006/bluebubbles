"""FastAPI providers for lifecycle-owned server dependencies."""

from starlette.requests import HTTPConnection

from bluebubbles.server.container import ServerContainer


def get_server_container(request: HTTPConnection) -> ServerContainer:
    """Return the application container without constructing dependencies."""
    container: ServerContainer = request.app.state.container
    return container
