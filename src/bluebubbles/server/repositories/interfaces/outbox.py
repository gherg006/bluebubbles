"""Transactional outbox repository protocol."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from bluebubbles.server.domain.outbox import OutboxEvent


class OutboxRepository(Protocol):
    """Define durable event publication-state operations."""

    async def add(self, event: OutboxEvent) -> OutboxEvent: ...

    async def claim_batch(
        self, worker_id: str, limit: int, now: datetime
    ) -> list[OutboxEvent]: ...

    async def mark_published(self, event_id: UUID, published_at: datetime) -> None: ...

    async def mark_failed(
        self,
        event_id: UUID,
        error_code: str,
        next_attempt_at: datetime,
    ) -> None: ...

    async def release_expired_locks(self, before: datetime) -> int: ...

    async def list_repeated_failures(
        self, minimum_attempts: int, *, limit: int
    ) -> list[OutboxEvent]: ...

    async def delete_old_published(self, before: datetime, *, limit: int) -> int: ...
