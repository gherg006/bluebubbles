"""FastAPI application factory for the independently deployed LAN server."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import JSONResponse

from bluebubbles.server.bootstrap import build_server_container
from bluebubbles.server.configuration.loader import ConfigurationLoader
from bluebubbles.server.configuration.settings import ServerSettings
from bluebubbles.server.container import ServerContainer
from bluebubbles.server.dependencies import get_server_container
from bluebubbles.server.routes.authentication import router as authentication_router
from bluebubbles.server.routes.contacts import router as contacts_router
from bluebubbles.server.routes.conversations import router as conversations_router
from bluebubbles.server.routes.groups import router as groups_router
from bluebubbles.server.routes.keys import router as keys_router
from bluebubbles.server.routes.users import router as users_router
from bluebubbles.shared.errors.exceptions import BlueBubblesError
from bluebubbles.shared.errors.mappings import get_error_metadata
from bluebubbles.shared.errors.translation import (
    to_api_error_response,
    unexpected_api_error_response,
)
from bluebubbles.shared.models.health import (
    HealthState,
    PublicHealthResponse,
)
from bluebubbles.version import __version__


def create_application(
    settings: ServerSettings | None = None,
    *,
    container: ServerContainer | None = None,
) -> FastAPI:
    """Create a server whose infrastructure is owned by FastAPI lifespan.

    Args:
        settings: Optional prevalidated configuration.
        container: Optional explicit dependency replacement for tests.

    Returns:
        A configured application that opens no connections before lifespan.
    """
    resolved_settings = settings or ConfigurationLoader().load_server_settings()
    resolved_container = container or build_server_container(resolved_settings)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.container = resolved_container
        await resolved_container.start()
        try:
            yield
        finally:
            await resolved_container.stop()

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
    application.state.container = resolved_container
    application.include_router(authentication_router)
    application.include_router(users_router)
    application.include_router(contacts_router)
    application.include_router(keys_router)
    application.include_router(conversations_router)
    application.include_router(groups_router)

    @application.exception_handler(BlueBubblesError)
    async def application_error_handler(
        request: Request, error: BlueBubblesError
    ) -> JSONResponse:
        """Translate expected failures without returning technical exception text."""
        del request
        correlation_id = uuid4()
        payload = to_api_error_response(error, correlation_id)
        return JSONResponse(
            status_code=get_error_metadata(error.code).http_status,
            content=payload.model_dump(mode="json"),
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(
        request: Request, error: Exception
    ) -> JSONResponse:
        """Return a generic envelope and log only the unexpected failure category."""
        resolved_container._logger.error(  # noqa: SLF001 - application boundary owner
            "Unhandled request failure",
            extra={"failure_category": type(error).__name__, "path": request.url.path},
        )
        payload = unexpected_api_error_response(uuid4())
        return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))

    @application.get("/", tags=["foundation"])
    async def application_information() -> dict[str, str]:
        """Return non-sensitive identity and version information."""
        return {
            "name": f"{resolved_settings.application.name} Server",
            "version": __version__,
        }

    @application.get(
        "/health/live",
        response_model=PublicHealthResponse,
        tags=["health"],
    )
    async def liveness() -> PublicHealthResponse:
        """Report only that the running process can serve an HTTP response."""
        return PublicHealthResponse(
            status=HealthState.HEALTHY, timestamp=datetime.now(UTC)
        )

    @application.get(
        "/health/ready",
        response_model=PublicHealthResponse,
        tags=["health"],
    )
    async def readiness(
        response: Response,
        server_container: Annotated[ServerContainer, Depends(get_server_container)],
    ) -> PublicHealthResponse:
        """Report critical dependency readiness with no topology detail."""
        health = await server_container.services.health.public_health()
        if health.status is HealthState.UNHEALTHY:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return health

    return application
