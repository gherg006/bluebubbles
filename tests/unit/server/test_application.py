"""Tests for the server application factory and public health boundary."""

from datetime import UTC, datetime
from typing import cast

from fastapi.testclient import TestClient

from bluebubbles.server.application import create_application
from bluebubbles.server.configuration.settings import ServerSettings
from bluebubbles.server.container import ServerContainer
from bluebubbles.shared.models.health import HealthState, PublicHealthResponse
from bluebubbles.version import __version__


class _HealthService:
    def __init__(self, state: HealthState) -> None:
        self._state = state

    async def public_health(self) -> PublicHealthResponse:
        return PublicHealthResponse(status=self._state, timestamp=datetime.now(UTC))


class _Services:
    def __init__(self, state: HealthState) -> None:
        self.health = _HealthService(state)


class _Container:
    def __init__(self, state: HealthState = HealthState.HEALTHY) -> None:
        self.services = _Services(state)
        self.started = False
        self.stopped = False

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True


def _application(
    state: HealthState = HealthState.HEALTHY,
) -> tuple[_Container, TestClient]:
    container = _Container(state)
    application = create_application(
        ServerSettings(), container=cast(ServerContainer, container)
    )
    return container, TestClient(application)


def test_application_factory_returns_working_server_and_closes_lifecycle() -> None:
    container, client = _application()

    with client:
        response = client.get("/")
        assert container.started

    assert container.stopped
    assert response.status_code == 200
    assert response.json() == {
        "name": "BlueBubbles Server",
        "version": __version__,
    }


def test_liveness_is_lightweight_and_readiness_reflects_dependencies() -> None:
    _, client = _application(HealthState.UNHEALTHY)

    with client:
        live = client.get("/health/live")
        ready = client.get("/health/ready")

    assert live.status_code == 200
    assert live.json()["status"] == "healthy"
    assert ready.status_code == 503
    assert ready.json()["status"] == "unhealthy"
    assert set(ready.json()) == {"status", "timestamp"}


def test_degraded_readiness_remains_available() -> None:
    _, client = _application(HealthState.DEGRADED)
    with client:
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"


def test_unknown_route_returns_not_found() -> None:
    _, client = _application()
    with client:
        response = client.get("/not-defined")
    assert response.status_code == 404
