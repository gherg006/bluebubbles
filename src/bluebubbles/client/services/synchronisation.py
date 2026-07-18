"""Ordered authoritative synchronisation, checkpointing and conflict policy."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from bluebubbles.client.domain.synchronisation import (
    CancellationToken,
    ConflictCategory,
    ConflictResolution,
    ConnectivityState,
    ScopeSynchronisationResult,
    SynchronisationConflict,
    SynchronisationResult,
    SynchronisationScope,
)
from bluebubbles.client.repositories.interfaces import ConflictRepository
from bluebubbles.client.services.connectivity import ConnectivityController
from bluebubbles.client.storage.models import SynchronisationState


class EventCursorExpiredError(Exception):
    """Report that retained incremental events cannot cover the local cursor."""


class ReauthenticationRequiredError(Exception):
    """Report that protected synchronisation cannot continue with this session."""


class SynchronisationGateway(Protocol):
    """Fetch and atomically apply one validated authoritative scope page."""

    async def synchronise(
        self,
        scope: SynchronisationScope,
        *,
        scope_id: UUID | None,
        cursor: str | None,
        last_event_id: UUID | None,
        full: bool,
    ) -> ScopeSynchronisationResult: ...


class SynchronisationStateStore(Protocol):
    """Persist opaque checkpoints after an adapter commits its records."""

    async def save(self, state: SynchronisationState) -> bool: ...
    async def get(
        self, scope: str, scope_identifier: str | None = None
    ) -> SynchronisationState | None: ...


class QueueSynchronisationCoordinator(Protocol):
    """Expose only queue operations needed after authoritative refresh."""

    async def unblock_after_sync(self, scope: SynchronisationScope) -> int: ...
    async def process_pending(self) -> object: ...


class SynchronisationService:
    """Run security-first initial, reconnect, targeted and full reconciliation."""

    _SECURITY_ORDER = (
        SynchronisationScope.PROTOCOL,
        SynchronisationScope.CURRENT_USER,
        SynchronisationScope.POLICIES,
        SynchronisationScope.CONVERSATIONS,
        SynchronisationScope.CONVERSATION_MEMBERSHIP,
        SynchronisationScope.PUBLIC_KEYS,
    )
    _GENERAL_ORDER = (
        SynchronisationScope.MESSAGES,
        SynchronisationScope.ANNOUNCEMENTS,
        SynchronisationScope.SESSIONS,
        SynchronisationScope.ADMIN_CAPABILITIES,
        SynchronisationScope.TRANSFERS,
    )

    def __init__(
        self,
        gateway: SynchronisationGateway,
        state_repository: SynchronisationStateStore,
        queue: QueueSynchronisationCoordinator,
        connectivity: ConnectivityController,
    ) -> None:
        self._gateway = gateway
        self._state_repository = state_repository
        self._queue = queue
        self._connectivity = connectivity

    async def initial_sync(
        self, cancellation_token: CancellationToken
    ) -> SynchronisationResult:
        """Load essential security state before messages and queued writes."""
        return await self._run(
            self._SECURITY_ORDER + self._GENERAL_ORDER,
            cancellation_token=cancellation_token,
            full=False,
        )

    async def reconnect_sync(self, last_event_id: UUID | None) -> SynchronisationResult:
        """Prefer incremental missed-event recovery, falling back on expiry."""
        try:
            return await self._run(
                self._SECURITY_ORDER + self._GENERAL_ORDER,
                last_event_id=last_event_id,
                full=False,
            )
        except EventCursorExpiredError:
            return await self.full_resync(CancellationToken())

    async def synchronise_conversation(
        self, conversation_id: UUID
    ) -> SynchronisationResult:
        """Refresh membership, keys and messages for one affected conversation."""
        return await self._run(
            (
                SynchronisationScope.CONVERSATION_MEMBERSHIP,
                SynchronisationScope.PUBLIC_KEYS,
                SynchronisationScope.MESSAGES,
            ),
            scope_id=conversation_id,
            full=False,
        )

    async def full_resync(
        self, cancellation_token: CancellationToken
    ) -> SynchronisationResult:
        """Rebuild server-derived scopes while adapters preserve local work."""
        return await self._run(
            self._SECURITY_ORDER + self._GENERAL_ORDER,
            cancellation_token=cancellation_token,
            full=True,
        )

    async def _run(
        self,
        scopes: tuple[SynchronisationScope, ...],
        *,
        cancellation_token: CancellationToken | None = None,
        scope_id: UUID | None = None,
        last_event_id: UUID | None = None,
        full: bool,
    ) -> SynchronisationResult:
        started = datetime.now(UTC)
        succeeded: list[str] = []
        failed: list[str] = []
        conversations = messages_added = messages_updated = tombstones = 0
        unblocked = 0
        requires_reauthentication = False
        self._prepare_to_synchronise()
        for scope in scopes:
            if cancellation_token is not None and cancellation_token.cancelled:
                break
            identifier = str(scope_id) if scope_id else None
            checkpoint = await self._state_repository.get(scope.value, identifier)
            try:
                page = await self._gateway.synchronise(
                    scope,
                    scope_id=scope_id,
                    cursor=checkpoint.cursor if checkpoint else None,
                    last_event_id=last_event_id,
                    full=full,
                )
                # The gateway returns only after its page commit. A crash before this
                # checkpoint causes a safe replay; it can never skip server records.
                await self._state_repository.save(
                    SynchronisationState(
                        scope.value,
                        identifier,
                        page.cursor,
                        page.version,
                        datetime.now(UTC),
                    )
                )
            except ReauthenticationRequiredError:
                failed.append(scope.value)
                requires_reauthentication = True
                break
            except EventCursorExpiredError:
                raise
            except Exception:
                failed.append(scope.value)
                continue
            succeeded.append(scope.value)
            conversations += page.conversations_updated
            messages_added += page.messages_added
            messages_updated += page.messages_updated
            tombstones += page.tombstones_applied
            unblocked += await self._queue.unblock_after_sync(scope)
        critical = {
            SynchronisationScope.PROTOCOL.value,
            SynchronisationScope.CURRENT_USER.value,
            SynchronisationScope.POLICIES.value,
            SynchronisationScope.CONVERSATION_MEMBERSHIP.value,
            SynchronisationScope.PUBLIC_KEYS.value,
        }
        requested_critical = critical.intersection(scope.value for scope in scopes)
        security_ready = requested_critical.issubset(succeeded)
        if security_ready and not requires_reauthentication:
            await self._queue.process_pending()
        degraded = bool(failed)
        if requires_reauthentication:
            final_state = ConnectivityState.REAUTHENTICATION_REQUIRED
        elif degraded:
            final_state = ConnectivityState.DEGRADED
        else:
            final_state = ConnectivityState.CONNECTED
        self._connectivity.transition(final_state)
        return SynchronisationResult(
            started,
            datetime.now(UTC),
            tuple(succeeded),
            tuple(failed),
            conversations,
            messages_added,
            messages_updated,
            tombstones,
            unblocked,
            requires_reauthentication,
            degraded,
        )

    def _prepare_to_synchronise(self) -> None:
        if self._connectivity.state in {
            ConnectivityState.STARTING,
            ConnectivityState.OFFLINE,
        }:
            self._connectivity.transition(ConnectivityState.CONNECTING)
            self._connectivity.transition(ConnectivityState.CONNECTED)
        self._connectivity.transition(ConnectivityState.SYNCHRONISING)


SynchronizationService = SynchronisationService


class ConflictResolver:
    """Automatically resolve only equivalence cases that cannot lose user intent."""

    _EQUIVALENT_CODES = frozenset(
        {
            "duplicate_identical",
            "read_position_already_advanced",
            "preference_already_applied",
            "announcement_already_acknowledged",
            "message_already_deleted",
        }
    )

    def __init__(self, repository: ConflictRepository) -> None:
        self._repository = repository

    async def resolve(self, conflict: SynchronisationConflict) -> ConflictResolution:
        """Persist and return a deterministic resolution classification."""
        if conflict.failure_code in self._EQUIVALENT_CODES:
            resolution = ConflictResolution.EQUIVALENT_SUCCESS
        elif conflict.category in {
            ConflictCategory.MEMBERSHIP_CONFLICT,
            ConflictCategory.PERMISSION_CONFLICT,
            ConflictCategory.DELETION_CONFLICT,
            ConflictCategory.POLICY_CONFLICT,
        }:
            resolution = ConflictResolution.ACTION_BLOCKED
        elif conflict.category in {
            ConflictCategory.KEY_CONFLICT,
            ConflictCategory.PROTOCOL_CONFLICT,
        }:
            resolution = ConflictResolution.REBUILD_REQUIRED
        else:
            resolution = ConflictResolution.USER_INPUT_REQUIRED
        await self._repository.save(
            replace(
                conflict,
                resolved_at=(
                    datetime.now(UTC)
                    if resolution is not ConflictResolution.USER_INPUT_REQUIRED
                    else None
                ),
                resolution=resolution,
            )
        )
        return resolution
