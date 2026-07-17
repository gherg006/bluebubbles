"""Package import and lifecycle-managed server workflow integration test."""

from typing import cast

from fastapi.testclient import TestClient

import bluebubbles
from bluebubbles.server.application import create_application
from bluebubbles.server.configuration.settings import ServerSettings
from bluebubbles.server.container import ServerContainer


class _Container:
    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None


def test_installed_package_and_server_entry_point_work_together() -> None:
    app = create_application(
        ServerSettings(), container=cast(ServerContainer, _Container())
    )
    with TestClient(app) as client:
        response = client.get("/")

    assert response.json()["version"] == bluebubbles.__version__
