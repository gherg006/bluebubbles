"""Foundation-stage import and server workflow integration test."""

from fastapi.testclient import TestClient

import bluebubbles
from bluebubbles.server.main import app


def test_installed_package_and_server_entry_point_work_together() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.json()["version"] == bluebubbles.__version__
