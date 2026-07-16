"""FastAPI application factory for the BlueBubbles server."""

from fastapi import FastAPI

from bluebubbles.version import __version__


def create_application() -> FastAPI:
    """Create an isolated minimal server application for this foundation stage."""
    application = FastAPI(
        title="BlueBubbles Server",
        description="Encrypted LAN messaging server",
        version=__version__,
    )

    @application.get("/", tags=["foundation"])
    async def application_information() -> dict[str, str]:
        """Return non-sensitive identity and version information."""
        return {"name": "BlueBubbles Server", "version": __version__}

    return application
