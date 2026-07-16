"""FastAPI application factory for the independently deployed LAN server."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from bluebubbles.server.bootstrap import build_server_container
from bluebubbles.server.configuration.loader import ConfigurationLoader
from bluebubbles.server.configuration.settings import ServerSettings
from bluebubbles.server.container import ServerContainer
from bluebubbles.version import __version__


def create_application(settings: ServerSettings | None = None) -> FastAPI:
    """Create a server whose container starts and stops with FastAPI lifespan."""
    resolved_settings = settings or ConfigurationLoader().load_server_settings()
    container = build_server_container(resolved_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await container.start()
        try:
            yield
        finally:
            await container.stop()

    application = FastAPI(
        title=f"{resolved_settings.application.name} Server",
        description="Encrypted LAN messaging server",
        version=__version__,
        debug=resolved_settings.application.debug,
        docs_url=(
            None
            if resolved_settings.application.environment.value == "production"
            else "/docs"
        ),
        lifespan=lifespan,
    )
    application.state.container = container

    @application.get("/", tags=["foundation"])
    async def application_information() -> dict[str, str]:
        """Return non-sensitive identity and version information."""
        return {
            "name": f"{resolved_settings.application.name} Server",
            "version": __version__,
        }

    return application


def get_server_container(application: FastAPI) -> ServerContainer:
    """Return the lifecycle-owned container for dependency provider functions."""
    container: ServerContainer = application.state.container
    return container
