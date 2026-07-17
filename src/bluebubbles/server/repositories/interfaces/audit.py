"""Append-only audit repository protocol."""

from typing import Protocol

from bluebubbles.server.domain.audit import AuditChainState, AuditEvent
from bluebubbles.server.repositories.types import AuditQuery, CursorPage


class AuditRepository(Protocol):
    """Define immutable audit-chain persistence operations."""

    async def lock_chain_state(self) -> AuditChainState: ...

    async def get_latest_chain_state(self) -> AuditChainState: ...

    async def append(self, event: AuditEvent) -> AuditEvent: ...

    async def update_chain_state(self, state: AuditChainState) -> None: ...

    async def list_events(self, query: AuditQuery) -> CursorPage[AuditEvent]: ...

    async def get_by_sequence(self, sequence: int) -> AuditEvent | None: ...

    async def list_range(
        self, first_sequence: int, last_sequence: int
    ) -> list[AuditEvent]: ...

    async def verify_range_data(
        self, first_sequence: int, last_sequence: int
    ) -> list[AuditEvent]: ...
