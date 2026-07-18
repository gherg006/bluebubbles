"""Task 17 synchronisation order, fallback, conflict and tombstone evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from bluebubbles.client.domain.synchronisation import (
    CancellationToken,
    ConflictCategory,
    ConflictResolution,
    LocalTombstone,
    ScopeSynchronisationResult,
    SynchronisationConflict,
    SynchronisationScope,
)
from bluebubbles.client.repositories.sqlite.synchronisation_metadata import (
    SQLiteConflictRepository,
    SQLiteTombstoneRepository,
)
from bluebubbles.client.services.connectivity import ConnectivityController
from bluebubbles.client.services.synchronisation import (
    ConflictResolver,
    EventCursorExpiredError,
    ReauthenticationRequiredError,
    SynchronisationService,
)
from bluebubbles.client.storage.database import LocalDatabaseManager
from bluebubbles.client.storage.migrations import ClientMigrationManager
from bluebubbles.client.storage.models import SynchronisationState


class QueueSpy:
    """Record security-scope unblocking and queue replay calls."""

    def __init__(self) -> None:
        self.unblocked: list[SynchronisationScope] = []
        self.processed = 0

    async def unblock_after_sync(self, scope: SynchronisationScope) -> int:
        self.unblocked.append(scope)
        return 1

    async def process_pending(self) -> object:
        self.processed += 1
        return object()


class StateStore:
    """Store checkpoints in memory for ordering tests."""

    def __init__(self) -> None:
        self.items: dict[tuple[str, str | None], SynchronisationState] = {}

    async def save(self, state: SynchronisationState) -> bool:
        self.items[(state.scope, state.scope_identifier)] = state
        return True

    async def get(
        self, scope: str, scope_identifier: str | None = None
    ) -> SynchronisationState | None:
        return self.items.get((scope, scope_identifier))


class Gateway:
    """Return synthetic committed scope pages and optionally expire once."""

    def __init__(
        self, *, expire_once: bool = False, fail_scope: str | None = None
    ) -> None:
        self.calls: list[tuple[SynchronisationScope, bool]] = []
        self.expire_once = expire_once
        self.fail_scope = fail_scope

    async def synchronise(
        self,
        scope: SynchronisationScope,
        *,
        scope_id: UUID | None,
        cursor: str | None,
        last_event_id: UUID | None,
        full: bool,
    ) -> ScopeSynchronisationResult:
        del cursor, last_event_id
        self.calls.append((scope, full))
        if self.expire_once:
            self.expire_once = False
            raise EventCursorExpiredError
        if scope.value == self.fail_scope:
            raise RuntimeError("synthetic scope failure")
        return ScopeSynchronisationResult(scope, scope_id, f"cursor-{scope.value}", 1)


@pytest.mark.asyncio
async def test_initial_sync_is_security_first_and_then_processes_queue() -> None:
    gateway, store, queue = Gateway(), StateStore(), QueueSpy()
    service = SynchronisationService(gateway, store, queue, ConnectivityController())

    result = await service.initial_sync(CancellationToken())

    assert [scope for scope, _full in gateway.calls[:6]] == list(
        SynchronisationService._SECURITY_ORDER
    )
    assert not result.degraded
    assert queue.processed == 1
    assert len(store.items) == len(gateway.calls)


@pytest.mark.asyncio
async def test_expired_reconnect_cursor_falls_back_to_full_resync() -> None:
    gateway, store, queue = Gateway(expire_once=True), StateStore(), QueueSpy()
    service = SynchronisationService(gateway, store, queue, ConnectivityController())

    result = await service.reconnect_sync(uuid4())

    assert result.scopes_failed == ()
    assert gateway.calls[0][1] is False
    assert gateway.calls[1][1] is True


@pytest.mark.asyncio
async def test_critical_scope_failure_blocks_queue_and_reports_degraded() -> None:
    gateway = Gateway(fail_scope=SynchronisationScope.POLICIES.value)
    queue = QueueSpy()
    service = SynchronisationService(
        gateway, StateStore(), queue, ConnectivityController()
    )

    result = await service.initial_sync(CancellationToken())

    assert result.degraded
    assert SynchronisationScope.POLICIES.value in result.scopes_failed
    assert queue.processed == 0


@pytest.mark.asyncio
async def test_conflicts_and_tombstones_persist_without_content(tmp_path: Path) -> None:
    path = tmp_path / "client_cache.db"
    database = LocalDatabaseManager(path, ClientMigrationManager(path, tmp_path / "r"))
    await database.open(b"s" * 32)
    conflicts = SQLiteConflictRepository(database)
    resolver = ConflictResolver(conflicts)
    conflict = SynchronisationConflict(
        uuid4(),
        ConflictCategory.DUPLICATE_ID_CONFLICT,
        SynchronisationScope.MESSAGES,
        uuid4(),
        uuid4(),
        datetime.now(UTC),
        "duplicate_identical",
    )
    assert await resolver.resolve(conflict) is ConflictResolution.EQUIVALENT_SUCCESS
    assert await conflicts.list_unresolved() == []

    tombstones = SQLiteTombstoneRepository(database)
    tombstone = LocalTombstone(
        SynchronisationScope.CONVERSATIONS,
        uuid4(),
        4,
        datetime.now(UTC),
        "conversation_deleted",
    )
    await tombstones.save(tombstone)
    assert await tombstones.get(tombstone.scope, tombstone.resource_id) == tombstone
    await database.close()
    assert b"message plaintext" not in path.read_bytes()


def test_connectivity_rejects_invalid_state_transition() -> None:
    from bluebubbles.client.domain.synchronisation import ConnectivityState

    controller = ConnectivityController()
    with pytest.raises(ValueError, match="Invalid connectivity transition"):
        controller.transition(ConnectivityState.CONNECTED)


@pytest.mark.asyncio
async def test_targeted_sync_cancellation_and_reauthentication() -> None:
    queue = QueueSpy()
    gateway = Gateway()
    service = SynchronisationService(
        gateway, StateStore(), queue, ConnectivityController()
    )
    result = await service.synchronise_conversation(uuid4())
    assert result.scopes_succeeded == (
        SynchronisationScope.CONVERSATION_MEMBERSHIP.value,
        SynchronisationScope.PUBLIC_KEYS.value,
        SynchronisationScope.MESSAGES.value,
    )

    token = CancellationToken()
    token.cancel()
    cancelled = await SynchronisationService(
        Gateway(), StateStore(), QueueSpy(), ConnectivityController()
    ).initial_sync(token)
    assert cancelled.scopes_succeeded == ()

    class ReauthenticationGateway(Gateway):
        async def synchronise(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            del args, kwargs
            raise ReauthenticationRequiredError

    reauthentication = await SynchronisationService(
        ReauthenticationGateway(),
        StateStore(),
        QueueSpy(),
        ConnectivityController(),
    ).initial_sync(CancellationToken())
    assert reauthentication.requires_reauthentication


@pytest.mark.asyncio
async def test_conflict_resolver_requires_user_or_rebuilds_by_category(
    tmp_path: Path,
) -> None:
    path = tmp_path / "client_cache.db"
    database = LocalDatabaseManager(path, ClientMigrationManager(path, tmp_path / "r"))
    await database.open(b"t" * 32)
    repository = SQLiteConflictRepository(database)
    resolver = ConflictResolver(repository)

    def conflict(
        category: ConflictCategory, failure_code: str
    ) -> SynchronisationConflict:
        return SynchronisationConflict(
            uuid4(),
            category,
            SynchronisationScope.MESSAGES,
            uuid4(),
            uuid4(),
            datetime.now(UTC),
            failure_code,
            attempted_content_preserved=True,
        )

    user = conflict(ConflictCategory.VERSION_CONFLICT, "message_changed")
    assert await resolver.resolve(user) is ConflictResolution.USER_INPUT_REQUIRED
    assert len(await repository.list_unresolved()) == 1
    rebuild = conflict(ConflictCategory.KEY_CONFLICT, "key_changed")
    assert await resolver.resolve(rebuild) is ConflictResolution.REBUILD_REQUIRED
    blocked = conflict(ConflictCategory.MEMBERSHIP_CONFLICT, "member_removed")
    assert await resolver.resolve(blocked) is ConflictResolution.ACTION_BLOCKED
    await database.close()


def test_connectivity_subscriber_and_normalised_repeated_state() -> None:
    from bluebubbles.client.domain.synchronisation import ConnectivityState

    states: list[ConnectivityState] = []
    controller = ConnectivityController()
    controller.subscribe(states.append)
    controller.transition(ConnectivityState.CONNECTING)
    controller.transition(ConnectivityState.CONNECTING)
    assert states == [ConnectivityState.STARTING, ConnectivityState.CONNECTING]
