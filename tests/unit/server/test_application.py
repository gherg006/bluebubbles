"""Tests for the server application factory."""

from fastapi.testclient import TestClient

from bluebubbles.server.application import create_application
from bluebubbles.version import __version__


def test_application_factory_returns_working_server() -> None:
    application = create_application()

    with TestClient(application) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "BlueBubbles Server",
        "version": __version__,
    }


def test_unknown_route_returns_not_found() -> None:
    with TestClient(create_application()) as client:
        response = client.get("/not-defined")

    assert response.status_code == 404
