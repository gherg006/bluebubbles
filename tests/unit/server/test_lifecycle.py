"""Unit tests for server dependency lifecycle, rollback, and health."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.exc import SQLAlchemyError

from bluebubbles.server.bootstrap import (
    build_server_container,
    run_startup_checks,
    verify_migration_state,
    verify_storage_paths,
)
from bluebubbles.server.configuration.settings import (
    RedisSettings,
    ServerSettings,
    StorageSettings,
)
from bluebubbles.server.container import ServerContainer, ServerServices
from bluebubbles.server.database.engine import DatabaseManager
from bluebubbles.server.database.migrations import SchemaRevisionMismatchError
from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.monitoring.health import HealthAggregator
from bluebubbles.server.monitoring.storage import StorageHealthCheck
from bluebubbles.server.redis import RedisManager
from bluebubbles.shared.errors.exceptions import (
    DatabaseUnavailableError,
    RedisUnavailableError,
    StorageUnavailableError,
)
from bluebubbles.shared.models.health import ComponentHealth, HealthState


class _Component:
    def __init__(
        self,
        name: str,
        events: list[str],
        *,
        start_error: BaseException | None = None,
        stop_error: BaseException | None = None,
        state: HealthState = HealthState.HEALTHY,
    ) -> None:
        self.name = name
        self.events = events
        self.start_error = start_error
        self.stop_error = stop_error
        self.state = state

    async def start(self) -> None:
        self.events.append(f"start:{self.name}")
        if self.start_error is not None:
            raise self.start_error

    async def stop(self) -> None:
        self.events.append(f"stop:{self.name}")
        if self.stop_error is not None:
            raise self.stop_error

    async def check_health(self) -> ComponentHealth:
        return ComponentHealth(name=self.name, state=self.state)


def _container(components: Sequence[_Component], events: list[str]) -> ServerContainer:
    settings = ServerSettings()
    checks = cast(Sequence[Any], components[:3])
    health = HealthAggregator(
        checks,
        timeout_seconds=0.1,
        application_version="test",
        protocol_versions=(1,),
    )
    required = tuple(components) + tuple(
        _Component(f"required-{index}", events)
        for index in range(max(0, 3 - len(components)))
    )
    return ServerContainer(
        settings,
        cast(DatabaseManager, required[0]),
        cast(RedisManager, required[1]),
        cast(StorageHealthCheck, required[2]),
        cast(UnitOfWorkFactory, object()),
        ServerServices(health),
        logging.getLogger("bluebubbles.tests.lifecycle"),
        additional_components=cast(Sequence[Any], required[3:]),
    )


@pytest.mark.asyncio
async def test_container_starts_once_and_stops_in_reverse_order() -> None:
    events: list[str] = []
    components = [_Component(name, events) for name in ("db", "redis", "storage")]
    container = _container(components, events)

    await container.start()
    await container.start()
    assert container.started
    await container.stop()
    await container.stop()

    assert events == [
        "start:db",
        "start:redis",
        "start:storage",
        "stop:storage",
        "stop:redis",
        "stop:db",
    ]
    assert not container.started


@pytest.mark.asyncio
async def test_container_rolls_back_failing_stage_and_continues_cleanup() -> None:
    events: list[str] = []
    components = [
        _Component("db", events, stop_error=RuntimeError("hidden cleanup")),
        _Component("redis", events),
        _Component("storage", events, start_error=RuntimeError("startup")),
    ]
    container = _container(components, events)

    with pytest.raises(RuntimeError, match="startup"):
        await container.start()

    assert events == [
        "start:db",
        "start:redis",
        "start:storage",
        "stop:storage",
        "stop:redis",
        "stop:db",
    ]
    assert not container.started


class _SlowHealth:
    async def check_health(self) -> ComponentHealth:
        await asyncio.sleep(1)
        return ComponentHealth(name="slow", state=HealthState.HEALTHY)


@pytest.mark.asyncio
async def test_health_aggregator_bounds_checks_and_separates_detail() -> None:
    aggregator = HealthAggregator(
        (
            _Component("database", [], state=HealthState.HEALTHY),
            _Component("redis", [], state=HealthState.DEGRADED),
        ),
        timeout_seconds=0.1,
        application_version="1.2.3",
        protocol_versions=(1, 2),
    )
    assert (await aggregator.public_health()).status is HealthState.DEGRADED
    detailed = await aggregator.detailed_health()
    assert [item.name for item in detailed.components] == ["database", "redis"]
    assert detailed.application_version == "1.2.3"

    timed_out = HealthAggregator(
        (_SlowHealth(),),
        timeout_seconds=0.01,
        application_version="test",
        protocol_versions=(1,),
    )
    result = await timed_out.detailed_health()
    assert result.status is HealthState.UNHEALTHY
    assert result.components[0].message is None

    latency = HealthAggregator(
        (_LatencyHealth(),),
        timeout_seconds=0.1,
        application_version="test",
        protocol_versions=(1,),
        latency_warning_ms={"database": 50},
    )
    assert (await latency.public_health()).status is HealthState.DEGRADED


class _LatencyHealth:
    async def check_health(self) -> ComponentHealth:
        return ComponentHealth(
            name="database", state=HealthState.HEALTHY, latency_ms=50
        )


@pytest.mark.asyncio
async def test_storage_check_creates_and_verifies_configured_paths(
    tmp_path: Path,
) -> None:
    settings = StorageSettings(
        root_path=tmp_path / "root",
        temporary_path=tmp_path / "temporary",
        export_path=tmp_path / "exports",
        reserved_free_bytes=0,
        reserved_free_percentage=0,
    )
    check = StorageHealthCheck(settings, logging.getLogger("test"))
    await check.start()
    assert check.started
    assert (await check.check_health()).state is HealthState.HEALTHY
    await check.stop()
    assert (await check.check_health()).state is HealthState.UNHEALTHY


@pytest.mark.asyncio
async def test_storage_failure_is_safe_and_contains_no_path(tmp_path: Path) -> None:
    settings = StorageSettings(
        root_path=tmp_path / "missing-root",
        temporary_path=tmp_path / "missing-temporary",
        export_path=tmp_path / "missing-exports",
        create_missing_directories=False,
        reserved_free_bytes=0,
        reserved_free_percentage=0,
    )
    check = StorageHealthCheck(settings, logging.getLogger("test"))
    with pytest.raises(StorageUnavailableError) as captured:
        await check.start()
    assert str(tmp_path) not in str(captured.value)

    relative = StorageHealthCheck(
        StorageSettings(
            root_path=Path("relative-root"),
            temporary_path=Path("relative-temporary"),
            export_path=Path("relative-exports"),
            reserved_free_bytes=0,
            reserved_free_percentage=0,
        ),
        logging.getLogger("test"),
    )
    with pytest.raises(StorageUnavailableError):
        await relative.start()


class _RedisClient:
    def __init__(self, error: BaseException | None = None) -> None:
        self.error = error
        self.closed = False

    async def ping(self) -> bool:
        if self.error is not None:
            raise self.error
        return True

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_redis_degraded_and_required_startup_behaviour() -> None:
    failing = _RedisClient(RedisConnectionError("redis://secret@host"))
    fallback = RedisManager(
        RedisSettings(fallback_enabled=True),
        logging.getLogger("test"),
        redis_client=cast(Redis, failing),
    )
    await fallback.start()
    assert fallback.degraded
    assert (await fallback.check_health()).state is HealthState.DEGRADED
    assert fallback.namespaced_key("presence", "user") == ("bluebubbles:presence:user")
    with pytest.raises(ValueError):
        fallback.namespaced_key("unsafe:value")
    await fallback.stop()
    assert failing.closed

    required = RedisManager(
        RedisSettings(fallback_enabled=False),
        logging.getLogger("test"),
        redis_client=cast(Redis, _RedisClient(RedisConnectionError("secret"))),
    )
    with pytest.raises(RedisUnavailableError) as captured:
        await required.start()
    assert "secret" not in str(captured.value)

    failing.error = None
    assert (await fallback.check_health()).state is HealthState.HEALTHY
    assert fallback.started


class _ConnectionContext:
    def __init__(self, connection: AsyncMock) -> None:
        self.connection = connection

    async def __aenter__(self) -> AsyncMock:
        return self.connection

    async def __aexit__(self, *_: object) -> None:
        return None


class _Engine:
    def __init__(self, execute_error: BaseException | None = None) -> None:
        self.connection = AsyncMock()
        if execute_error is not None:
            self.connection.execute.side_effect = execute_error
        self.disposals: int = 0

    def connect(self) -> _ConnectionContext:
        return _ConnectionContext(self.connection)

    async def dispose(self) -> None:
        self.disposals += 1


def _database_manager(engine: _Engine) -> DatabaseManager:
    manager = DatabaseManager(
        ServerSettings().database,
        logging.getLogger("test"),
        engine=cast(Any, engine),
    )
    return manager


def test_database_session_is_rejected_before_verified_startup() -> None:
    manager = _database_manager(_Engine())
    with pytest.raises(DatabaseUnavailableError):
        manager.create_session()


@pytest.mark.asyncio
async def test_database_manager_starts_checks_health_and_disposes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verify = AsyncMock()
    monkeypatch.setattr("bluebubbles.server.database.engine.verify_revision", verify)
    engine = _Engine()
    manager = _database_manager(engine)

    await manager.start()
    await manager.start()
    assert manager.started
    health = await manager.check_health()
    assert health.state is HealthState.HEALTHY
    assert health.latency_ms is not None
    verify.assert_awaited_once()

    await manager.stop()
    assert (await manager.check_health()).state is HealthState.UNHEALTHY
    assert (manager.started, engine.disposals) == (False, 1)


@pytest.mark.asyncio
async def test_database_manager_translates_adapter_failure_without_detail() -> None:
    engine = _Engine(SQLAlchemyError("postgresql://user:secret@host/database"))
    manager = _database_manager(engine)
    with pytest.raises(DatabaseUnavailableError) as captured:
        await manager.start()
    assert "secret" not in str(captured.value)
    assert engine.disposals == 1


@pytest.mark.asyncio
async def test_database_manager_disposes_after_migration_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _Engine()
    manager = _database_manager(engine)
    monkeypatch.setattr(
        "bluebubbles.server.database.engine.verify_revision",
        AsyncMock(side_effect=SchemaRevisionMismatchError("old", "head")),
    )
    with pytest.raises(SchemaRevisionMismatchError):
        await manager.start()
    assert engine.disposals == 1


@pytest.mark.asyncio
async def test_redis_success_runtime_failure_and_client_access() -> None:
    client = _RedisClient()
    manager = RedisManager(
        RedisSettings(),
        logging.getLogger("test"),
        redis_client=cast(Redis, client),
    )
    with pytest.raises(RedisUnavailableError):
        manager.client()
    await manager.start()
    assert manager.client() is cast(Any, client)
    assert await manager.ping() >= 0
    assert (await manager.check_health()).state is HealthState.HEALTHY

    client.error = RedisConnectionError("hidden")
    with pytest.raises(RedisUnavailableError):
        await manager.ping()
    assert manager.degraded


def test_bootstrap_constructs_singletons_without_opening_connections(
    tmp_path: Path,
) -> None:
    settings = ServerSettings.model_validate(
        {
            "storage": {
                "root_path": tmp_path / "root",
                "temporary_path": tmp_path / "temporary",
                "export_path": tmp_path / "exports",
                "reserved_free_bytes": 0,
                "reserved_free_percentage": 0,
            }
        }
    )
    container = build_server_container(settings)
    assert not container.started
    assert not container.database_manager.started
    assert not container.redis_manager.started
    assert container.services.health is container.services.health


@pytest.mark.asyncio
async def test_named_bootstrap_checks_delegate_to_real_lifecycle_methods(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = _database_manager(_Engine())
    monkeypatch.setattr(
        "bluebubbles.server.database.engine.verify_revision", AsyncMock()
    )
    storage = StorageHealthCheck(
        StorageSettings(
            root_path=tmp_path / "root",
            temporary_path=tmp_path / "temporary",
            export_path=tmp_path / "exports",
            reserved_free_bytes=0,
            reserved_free_percentage=0,
        ),
        logging.getLogger("test"),
    )
    await verify_migration_state(database)
    await verify_storage_paths(storage)
    assert database.started and storage.started
    await database.stop()

    events: list[str] = []
    container = _container(
        [_Component(name, events) for name in ("db", "redis", "storage")],
        events,
    )
    await run_startup_checks(container)
    assert container.started
    await container.stop()
