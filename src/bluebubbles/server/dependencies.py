"""FastAPI providers for lifecycle-owned server dependencies."""

from fastapi import Request

from bluebubbles.server.container import ServerContainer


def get_server_container(request: Request) -> ServerContainer:
    """Return the application container without constructing dependencies."""
    container: ServerContainer = request.app.state.container
    return container
