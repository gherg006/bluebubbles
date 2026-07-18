"""Transaction-scoped audit writing, visibility, querying, and verification."""

from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Final
from uuid import UUID, uuid4

from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.audit import (
    AuditEvent,
    AuditSeverity,
    build_canonical_audit_data,
    calculate_audit_hash,
)
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission
from bluebubbles.server.repositories.interfaces.audit import AuditRepository
from bluebubbles.server.repositories.types import AuditQuery
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.shared.models.administration import (
    AuditEventResponse,
    AuditPageResponse,
    AuditVerificationResponse,
)
from bluebubbles.shared.models.pagination import CursorPageMetadata, OpaqueCursor

_SENSITIVE_MARKERS: Final = (
    "password",
    "token",
    "secret",
    "private",
    "plaintext",
    "ciphertext",
    "content",
    "database_url",
)


def sanitise_audit_details(details: Mapping[str, object]) -> dict[str, object]:
    """Return a recursively redacted, JSON-safe audit detail mapping."""

    def clean(key: str, value: object) -> object:
        if any(marker in key.casefold() for marker in _SENSITIVE_MARKERS):
            return "[redacted]"
        if isinstance(value, Mapping):
            return {str(k): clean(str(k), v) for k, v in value.items()}
        if isinstance(value, list | tuple):
            return [clean(key, item) for item in value]
        if isinstance(value, str | int | float | bool) or value is None:
            return value
        return str(value)

    return {str(key): clean(str(key), value) for key, value in details.items()}


class AuditWriter:
    """Append one redacted hash-linked event in the caller's transaction."""

    async def append(
        self,
        repository: AuditRepository,
        *,
        event_type: str,
        occurred_at: datetime,
        actor_id: UUID | None,
        source_ip: str | None,
        severity: AuditSeverity,
        details: Mapping[str, object],
    ) -> AuditEvent:
        """Build and stage one deterministic event in the caller transaction."""
        state = await repository.lock_chain_state()
        sequence_number = state.event_count + 1
        safe_details = sanitise_audit_details(details)
        event_id = uuid4()
        digest = calculate_audit_hash(
            build_canonical_audit_data(
                event_id=event_id,
                event_type=event_type,
                occurred_at=occurred_at,
                actor_id=actor_id,
                source_address=source_ip,
                severity=severity,
                details=safe_details,
                previous_hash=state.last_hash,
                sequence_number=sequence_number,
            )
        )
        return await repository.append(
            AuditEvent(
                id=event_id,
                event_type=event_type,
                occurred_at=occurred_at,
                actor_id=actor_id,
                source_address=source_ip,
                severity=severity,
                details=safe_details,
                previous_hash=state.last_hash,
                event_hash=digest,
                sequence_number=sequence_number,
            )
        )


class AuthenticationAuditWriter(AuditWriter):
    """Retain the established authentication-specific writer name."""


class AuditVisibilityFilter:
    """Apply least-privilege detail filtering to audit response metadata."""

    def filter(self, event: AuditEvent, *, limited: bool) -> AuditEventResponse:
        """Convert an event while hiding reason and source detail when limited."""
        details = dict(event.details)
        if limited:
            details = {
                key: value
                for key, value in details.items()
                if key not in {"reason", "source_ip", "target_email"}
            }
        return AuditEventResponse(
            id=event.id,
            event_type=event.event_type,
            actor_id=event.actor_id,
            occurred_at=event.occurred_at,
            severity=event.severity.value,
            details=details,
            chain_hash=event.event_hash,
            sequence_number=event.sequence_number,
        )


class AuditService:
    """Provide permission-filtered cursor queries over immutable audit events."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        visibility_filter: AuditVisibilityFilter | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._permissions = permission_service
        self._visibility = visibility_filter or AuditVisibilityFilter()

    async def query(
        self,
        requester: AuthenticatedUser,
        *,
        limit: int = 50,
        cursor: str | None = None,
        category: str | None = None,
        actor_id: UUID | None = None,
    ) -> AuditPageResponse:
        """Return one authorised audit page without sensitive detail fields."""
        limited = Permission.AUDIT_VIEW.value not in requester.permissions
        required = Permission.AUDIT_VIEW_LIMITED if limited else Permission.AUDIT_VIEW
        await self._permissions.require_authenticated_permission(requester, required)
        async with self._unit_of_work_factory() as unit_of_work:
            page = await unit_of_work.audit.list_events(
                AuditQuery(
                    limit=limit,
                    cursor=cursor,
                    category=category,
                    actor_user_id=actor_id,
                )
            )
        return AuditPageResponse(
            events=tuple(
                self._visibility.filter(event, limited=limited) for event in page.items
            ),
            page=CursorPageMetadata(
                next_cursor=(
                    OpaqueCursor(page.next_cursor) if page.next_cursor else None
                ),
                has_more=page.next_cursor is not None,
            ),
        )


class AuditIntegrityService:
    """Verify sequence continuity, hashes, links, and persisted chain-head state."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService | None = None,
        *,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._permissions = permission_service
        self._clock = clock

    async def verify(
        self,
        requester: AuthenticatedUser | None = None,
        *,
        full: bool = False,
        recent_count: int = 1000,
    ) -> AuditVerificationResponse:
        """Verify the full chain or a bounded suffix and return safe failure codes."""
        if requester is not None and self._permissions is not None:
            await self._permissions.require_authenticated_permission(
                requester, Permission.AUDIT_VERIFY
            )
        async with self._unit_of_work_factory() as unit_of_work:
            state = await unit_of_work.audit.get_latest_chain_state()
            first = 1 if full else max(1, state.event_count - recent_count + 1)
            events = (
                await unit_of_work.audit.verify_range_data(first, state.event_count)
                if state.event_count
                else []
            )
        expected_previous: str | None = None
        if first > 1:
            async with self._unit_of_work_factory() as unit_of_work:
                previous = await unit_of_work.audit.get_by_sequence(first - 1)
            if previous is None:
                return self._result(False, full, len(events), first, "missing_sequence")
            expected_previous = previous.event_hash
        expected_sequence = first
        for event in events:
            if event.sequence_number != expected_sequence:
                return self._result(
                    False,
                    full,
                    expected_sequence - first,
                    expected_sequence,
                    "missing_sequence",
                )
            canonical = build_canonical_audit_data(
                event_id=event.id,
                event_type=event.event_type,
                occurred_at=event.occurred_at,
                actor_id=event.actor_id,
                source_address=event.source_address,
                severity=event.severity,
                details=event.details,
                previous_hash=event.previous_hash,
                sequence_number=event.sequence_number,
            )
            if (
                event.previous_hash != expected_previous
                or calculate_audit_hash(canonical) != event.event_hash
            ):
                return self._result(
                    False,
                    full,
                    expected_sequence - first,
                    expected_sequence,
                    "hash_mismatch",
                )
            expected_previous = event.event_hash
            expected_sequence += 1
        if len(events) != max(0, state.event_count - first + 1):
            return self._result(
                False, full, len(events), expected_sequence, "missing_sequence"
            )
        if state.last_hash != expected_previous:
            return self._result(False, full, len(events), None, "chain_state_mismatch")
        return self._result(True, full, len(events), None, None)

    def _result(
        self,
        valid: bool,
        full: bool,
        checked: int,
        sequence: int | None,
        reason: str | None,
    ) -> AuditVerificationResponse:
        now = self._clock()
        if now.tzinfo is None:
            from datetime import UTC

            now = now.replace(tzinfo=UTC)
        return AuditVerificationResponse(
            valid=valid,
            mode="full" if full else "recent",
            checked_events=checked,
            first_invalid_sequence=sequence,
            reason_code=reason,
            verified_at=now,
        )
