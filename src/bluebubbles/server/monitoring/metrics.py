"""Low-overhead in-process operational metrics without user-content labels."""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass
from pathlib import Path
from time import monotonic

from bluebubbles.server.websocket.manager import WebSocketConnectionManager


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    """Represent aggregate process and storage measurements."""

    uptime_seconds: float
    connected_users: int
    active_connections: int
    cpu_percent: float
    memory_percent: float
    disk_percent: float


class MetricsService:
    """Collect cheap aggregate metrics without retaining per-user history."""

    def __init__(
        self, connections: WebSocketConnectionManager, storage_root: Path
    ) -> None:
        self._connections = connections
        self._storage_root = storage_root
        self._started_at = monotonic()

    async def snapshot(self) -> MetricsSnapshot:
        """Return current aggregate metrics; unavailable values remain zero."""
        connections = await self._connections.list_connections()
        usage = await asyncio.to_thread(shutil.disk_usage, self._storage_root)
        disk_percent = 0.0 if usage.total == 0 else usage.used / usage.total * 100
        return MetricsSnapshot(
            uptime_seconds=max(0.0, monotonic() - self._started_at),
            connected_users=len({connection.user_id for connection in connections}),
            active_connections=len(connections),
            cpu_percent=0.0,
            memory_percent=0.0,
            disk_percent=disk_percent,
        )
