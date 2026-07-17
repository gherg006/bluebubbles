"""Append-only audit-chain and security-alert persistence mappings."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Uuid,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from bluebubbles.server.database.base import (
    JSON_VALUE_TYPE,
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

IP_ADDRESS_TYPE = String(45).with_variant(INET(), "postgresql")


class AuditEventORM(Base):
    """Map one immutable, tamper-evident audit-chain entry."""

    __tablename__ = "audit_events"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('informational', 'warning', 'error', 'critical')",
            name="severity_valid",
        ),
        CheckConstraint(
            "result IN ('success', 'failure', 'denied')", name="result_valid"
        ),
        CheckConstraint("length(entry_hash) = 64", name="entry_hash_length"),
        CheckConstraint(
            "previous_hash IS NULL OR length(previous_hash) = 64",
            name="previous_hash_length",
        ),
        Index("ix_audit_timestamp", "timestamp"),
        Index("ix_audit_category_time", "category", "timestamp"),
        Index("ix_audit_actor_time", "actor_user_id", "timestamp"),
        Index("ix_audit_target", "target_type", "target_id"),
        Index("ix_audit_correlation", "correlation_id"),
        Index("ix_audit_severity_time", "severity", "timestamp"),
    )

    sequence_number: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    target_type: Mapped[str | None] = mapped_column(String(100))
    target_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    session_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL")
    )
    source_ip: Mapped[str | None] = mapped_column(IP_ADDRESS_TYPE)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    details: Mapped[dict[str, object]] = mapped_column(
        JSON_VALUE_TYPE, nullable=False, default=dict
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    previous_hash: Mapped[str | None] = mapped_column(String(64))
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)


class AuditChainStateORM(Base):
    """Map the single lockable head row used to serialize audit appends."""

    __tablename__ = "audit_chain_state"
    __table_args__ = (
        CheckConstraint("id = 1", name="singleton_id"),
        CheckConstraint("latest_sequence_number >= 0", name="sequence_non_negative"),
        CheckConstraint(
            "latest_hash IS NULL OR length(latest_hash) = 64", name="hash_length"
        ),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    latest_sequence_number: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    latest_hash: Mapped[str | None] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class SecurityAlertORM(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Map safe diagnostic alert metadata and administrator review state."""

    __tablename__ = "security_alerts"
    __table_args__ = (
        CheckConstraint("occurrence_count >= 1", name="occurrence_count_positive"),
        CheckConstraint(
            "severity IN ('informational', 'warning', 'error', 'critical')",
            name="severity_valid",
        ),
        CheckConstraint(
            "status IN ('open', 'acknowledged', 'resolved')", name="status_valid"
        ),
        CheckConstraint(
            "status <> 'acknowledged' OR acknowledged_at IS NOT NULL",
            name="acknowledged_has_timestamp",
        ),
        CheckConstraint(
            "status <> 'resolved' OR resolved_at IS NOT NULL",
            name="resolved_has_timestamp",
        ),
        Index("ix_security_alerts_status", "status", "severity", "created_at"),
    )

    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_component: Mapped[str] = mapped_column(String(100), nullable=False)
    related_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    related_session_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL")
    )
    related_audit_sequence: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("audit_events.sequence_number", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    occurrence_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    resolution_notes: Mapped[str | None] = mapped_column(String(2000))
