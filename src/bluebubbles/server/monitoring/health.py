"""Timeout-bounded aggregation of safe component health results."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

from bluebubbles.shared.models.health import (
    CapabilityState,
    ComponentHealth,
    DetailedHealthResponse,
    HealthState,
    PublicHealthResponse,
)


class HealthCheck(Protocol):
    """Expose one safe asynchronous component health result."""

    async def check_health(self) -> ComponentHealth:
        """Return component state without secrets or topology details."""
        ...


class HealthAggregator:
    """Combine dependency checks into public and detailed health contracts."""

    def __init__(
        self,
        checks: Sequence[HealthCheck],
        *,
        timeout_seconds: float,
        application_version: str,
        protocol_versions: Sequence[int],
        latency_warning_ms: dict[str, float] | None = None,
    ) -> None:
        """Store immutable checks and safe application metadata."""
        if timeout_seconds <= 0:
            raise ValueError("Health-check timeout must be positive")
        self._checks = tuple(checks)
        self._timeout_seconds = timeout_seconds
        self._application_version = application_version
        self._protocol_versions = tuple(protocol_versions)
        self._latency_warning_ms = dict(latency_warning_ms or {})

    async def public_health(self) -> PublicHealthResponse:
        """Return minimal aggregate readiness for unauthenticated callers."""
        components = await self._collect()
        return PublicHealthResponse(
            status=self._aggregate_state(components), timestamp=datetime.now(UTC)
        )

    async def detailed_health(self) -> DetailedHealthResponse:
        """Return safe component detail for a future authorised API boundary."""
        components = await self._collect()
        return DetailedHealthResponse(
            status=self._aggregate_state(components),
            timestamp=datetime.now(UTC),
            application_version=self._application_version,
            protocol_versions=self._protocol_versions,
            components=components,
            capabilities=self._capability_states(components),
        )

    async def _collect(self) -> tuple[ComponentHealth, ...]:
        return tuple(
            await asyncio.gather(
                *(self._bounded_check(check) for check in self._checks)
            )
        )

    async def _bounded_check(self, check: HealthCheck) -> ComponentHealth:
        try:
            result = await asyncio.wait_for(
                check.check_health(), timeout=self._timeout_seconds
            )
            threshold = self._latency_warning_ms.get(result.name)
            if (
                threshold is not None
                and result.state is HealthState.HEALTHY
                and result.latency_ms is not None
                and result.latency_ms >= threshold
            ):
                return result.model_copy(update={"state": HealthState.DEGRADED})
            return result
        except Exception:
            # Component implementations must return safe names. An unexpected
            # failure cannot be exposed, so even its type is omitted here.
            return ComponentHealth(name="dependency", state=HealthState.UNHEALTHY)

    @staticmethod
    def _aggregate_state(components: Sequence[ComponentHealth]) -> HealthState:
        states = {component.state for component in components}
        if HealthState.UNHEALTHY in states:
            return HealthState.UNHEALTHY
        if HealthState.DEGRADED in states:
            return HealthState.DEGRADED
        return HealthState.HEALTHY

    @staticmethod
    def _capability_states(
        components: Sequence[ComponentHealth],
    ) -> dict[str, CapabilityState]:
        """Derive coarse feature availability from dependency health."""
        states = {component.name: component.state for component in components}

        def capability(*dependencies: str) -> CapabilityState:
            required = [states[name] for name in dependencies if name in states]
            if any(state is HealthState.UNHEALTHY for state in required):
                return CapabilityState.UNAVAILABLE
            if any(state is HealthState.DEGRADED for state in required):
                return CapabilityState.DEGRADED
            return CapabilityState.AVAILABLE

        return {
            "authentication": capability("database", "directory"),
            "messaging": capability("database", "outbox", "websocket"),
            "presence": capability("redis", "websocket"),
            "attachments": capability("database", "storage"),
            "administration": capability("database"),
        }
