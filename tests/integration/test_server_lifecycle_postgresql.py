"""Opt-in real PostgreSQL evidence for the Task 08 server lifecycle."""

import os
from pathlib import Path

import pytest

from bluebubbles.server.bootstrap import build_server_container
from bluebubbles.server.configuration.settings import ServerSettings
from bluebubbles.shared.models.health import HealthState

_DATABASE_URL = os.environ.get("BLUEBUBBLES_TEST_DATABASE_URL")
_REQUIRES_DATABASE = pytest.mark.skipif(
    _DATABASE_URL is None,
    reason="BLUEBUBBLES_TEST_DATABASE_URL does not name a migrated PostgreSQL test DB",
)


@_REQUIRES_DATABASE
@pytest.mark.asyncio
async def test_real_container_verifies_schema_and_cleans_up(tmp_path: Path) -> None:
    """Start the real database manager, create a session, and stop every resource."""
    assert _DATABASE_URL is not None
    settings = ServerSettings.model_validate(
        {
            "database": {"url": _DATABASE_URL},
            "redis": {
                "url": "redis://127.0.0.1:1/0",
                "connection_timeout_seconds": 1,
                "operation_timeout_seconds": 1,
                "fallback_enabled": True,
            },
            "storage": {
                "root_path": tmp_path / "attachments",
                "temporary_path": tmp_path / "temporary",
                "export_path": tmp_path / "exports",
                "reserved_free_bytes": 0,
                "reserved_free_percentage": 0,
            },
        }
    )
    container = build_server_container(settings)
    try:
        await container.start()
        session = container.database_manager.create_session()
        await session.close()
        health = await container.get_health()
        assert health.status is HealthState.DEGRADED
        assert {component.name for component in health.components} == {
            "database",
            "redis",
            "storage",
        }
    finally:
        await container.stop()
    assert not container.started
