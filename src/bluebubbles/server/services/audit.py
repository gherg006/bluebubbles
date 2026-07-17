"""Small transaction-scoped writer for authentication audit-chain events."""

from collections.abc import Mapping
from datetime import datetime
from uuid import UUID, uuid4

from bluebubbles.server.domain.audit import (
    AuditEvent,
    AuditSeverity,
    build_canonical_audit_data,
    calculate_audit_hash,
)
from bluebubbles.server.repositories.interfaces.audit import AuditRepository


class AuthenticationAuditWriter:
    """Append password-free authentication facts to the existing audit chain."""

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
        event_id = uuid4()
        digest = calculate_audit_hash(
            build_canonical_audit_data(
                event_id=event_id,
                event_type=event_type,
                occurred_at=occurred_at,
                actor_id=actor_id,
                source_address=source_ip,
                severity=severity,
                details=details,
                previous_hash=state.last_hash,
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
                details=details,
                previous_hash=state.last_hash,
                event_hash=digest,
            )
        )
