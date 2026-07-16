"""Immutable audit records and deterministic hash-chain verification."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from uuid import UUID


class AuditSeverity(StrEnum):
    """Classify audit event importance."""

    INFORMATIONAL = "informational"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Represent one immutable, plaintext-free audit-chain entry."""

    id: UUID
    event_type: str
    occurred_at: datetime
    actor_id: UUID | None
    source_address: str | None
    severity: AuditSeverity
    details: Mapping[str, object]
    previous_hash: str | None
    event_hash: str

    def __post_init__(self) -> None:
        if not self.event_type.strip() or not self.event_hash:
            raise ValueError("Audit type and hash are required")
        if self.occurred_at.tzinfo is None:
            raise ValueError("Audit timestamp must be timezone-aware")
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))


@dataclass(frozen=True, slots=True)
class AuditChainState:
    """Describe the persisted head of one audit chain."""

    last_event_id: UUID | None
    last_hash: str | None
    event_count: int

    def __post_init__(self) -> None:
        if self.event_count < 0:
            raise ValueError("Audit event count cannot be negative")


@dataclass(frozen=True, slots=True)
class AuditVerificationResult:
    """Return audit-chain verification outcome without raising on corruption."""

    valid: bool
    checked_events: int
    first_invalid_event_id: UUID | None = None
    reason: str | None = None


def build_canonical_audit_data(
    *,
    event_id: UUID,
    event_type: str,
    occurred_at: datetime,
    actor_id: UUID | None,
    source_address: str | None,
    severity: AuditSeverity,
    details: Mapping[str, object],
    previous_hash: str | None,
) -> bytes:
    """Serialise audit fields deterministically for hash generation."""
    payload = {
        "actor_id": str(actor_id) if actor_id else None,
        "details": dict(details),
        "event_id": str(event_id),
        "event_type": event_type,
        "occurred_at": occurred_at.isoformat(),
        "previous_hash": previous_hash,
        "severity": severity.value,
        "source_address": source_address,
    }
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def calculate_audit_hash(canonical_data: bytes) -> str:
    """Return the SHA-256 digest for canonical audit data."""
    return hashlib.sha256(canonical_data).hexdigest()


def verify_audit_link(event: AuditEvent, expected_previous_hash: str | None) -> bool:
    """Verify both the previous-link value and current event digest."""
    if event.previous_hash != expected_previous_hash:
        return False
    canonical = build_canonical_audit_data(
        event_id=event.id,
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        actor_id=event.actor_id,
        source_address=event.source_address,
        severity=event.severity,
        details=event.details,
        previous_hash=event.previous_hash,
    )
    return calculate_audit_hash(canonical) == event.event_hash
