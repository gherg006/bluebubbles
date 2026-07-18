"""Pure audit ORM/domain conversions."""

from bluebubbles.server.database.models.audit import AuditEventORM
from bluebubbles.server.domain.audit import AuditEvent, AuditSeverity


class AuditMapper:
    """Convert immutable audit records without changing their hash data."""

    @staticmethod
    def to_domain(record: AuditEventORM) -> AuditEvent:
        """Convert one immutable audit database row."""
        return AuditEvent(
            id=record.id,
            event_type=record.action,
            occurred_at=record.timestamp,
            actor_id=record.actor_user_id,
            source_address=record.source_ip,
            severity=AuditSeverity(record.severity),
            details=record.details,
            previous_hash=record.previous_hash,
            event_hash=record.entry_hash,
            sequence_number=record.sequence_number,
        )
