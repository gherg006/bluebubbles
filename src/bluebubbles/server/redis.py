"""Application-owned Redis lifecycle with explicit degraded fallback."""

from __future__ import annotations

import logging
from time import perf_counter

from redis.asyncio import Redis
from redis.exceptions import RedisError

from bluebubbles.server.configuration.settings import RedisSettings
from bluebubbles.shared.errors.exceptions import RedisUnavailableError
from bluebubbles.shared.models.health import ComponentHealth, HealthState


class RedisManager:
    """Own Redis connectivity and namespace transient-state keys."""

    def __init__(
        self,
        settings: RedisSettings,
        logger: logging.Logger,
        *,
        redis_client: Redis | None = None,
    ) -> None:
        """Construct a lazy Redis client without performing network I/O."""
        self._settings = settings
        self._logger = logger
        self._client = redis_client or Redis.from_url(
            settings.url.get_secret_value(),
            socket_connect_timeout=settings.connection_timeout_seconds,
            socket_timeout=settings.operation_timeout_seconds,
            max_connections=settings.maximum_connections,
            decode_responses=False,
        )
        self._started = False
        self._degraded = False

    @property
    def started(self) -> bool:
        """Return whether Redis passed its startup ping."""
        return self._started

    @property
    def degraded(self) -> bool:
        """Return whether configured fallback is serving without Redis."""
        return self._degraded

    async def start(self) -> None:
        """Test Redis or enter the configured degraded mode.

        Raises:
            RedisUnavailableError: If Redis fails and fallback is disabled.
        """
        if self._started:
            return
        try:
            await self._client.ping()
        except RedisError as error:
            if not self._settings.fallback_enabled:
                raise RedisUnavailableError(
                    user_message="The transient-state service is unavailable.",
                    technical_message="Redis startup verification failed.",
                    retryable=True,
                ) from error
            self._degraded = True
            self._logger.warning(
                "Redis unavailable; durable operations remain available",
                extra={"fallback_enabled": True},
            )
            return
        self._started = True
        self._degraded = False

    async def stop(self) -> None:
        """Close Redis connections; repeated and degraded calls are safe."""
        try:
            await self._client.aclose()
        except RedisError as error:
            self._logger.error(
                "Redis connection cleanup failed",
                extra={"failure_category": type(error).__name__},
            )
        finally:
            self._started = False
            self._degraded = False

    async def ping(self) -> float:
        """Return Redis round-trip latency in milliseconds.

        Raises:
            RedisUnavailableError: If Redis is not operational.
        """
        if not self._started:
            raise RedisUnavailableError(
                user_message="The transient-state service is unavailable.",
                technical_message="Redis was used while unavailable.",
                retryable=True,
            )
        started_at = perf_counter()
        try:
            await self._client.ping()
        except RedisError as error:
            self._started = False
            self._degraded = self._settings.fallback_enabled
            raise RedisUnavailableError(
                user_message="The transient-state service is unavailable.",
                technical_message="Redis health verification failed.",
                retryable=True,
            ) from error
        return (perf_counter() - started_at) * 1000

    async def check_health(self) -> ComponentHealth:
        """Return Redis health without addresses or library error text."""
        if not self._started:
            started_at = perf_counter()
            try:
                await self._client.ping()
            except RedisError:
                return ComponentHealth(
                    name="redis",
                    state=(
                        HealthState.DEGRADED
                        if self._settings.fallback_enabled
                        else HealthState.UNHEALTHY
                    ),
                )
            self._started = True
            self._degraded = False
            return ComponentHealth(
                name="redis",
                state=HealthState.HEALTHY,
                latency_ms=(perf_counter() - started_at) * 1000,
            )
        try:
            latency = await self.ping()
        except RedisUnavailableError:
            return ComponentHealth(
                name="redis",
                state=(
                    HealthState.DEGRADED
                    if self._settings.fallback_enabled
                    else HealthState.UNHEALTHY
                ),
            )
        return ComponentHealth(
            name="redis", state=HealthState.HEALTHY, latency_ms=latency
        )

    def client(self) -> Redis:
        """Return the live client for explicit transient adapters.

        Raises:
            RedisUnavailableError: If Redis is unavailable or degraded.
        """
        if not self._started:
            raise RedisUnavailableError(
                user_message="The transient-state service is unavailable.",
                technical_message="A Redis client was requested while unavailable.",
                retryable=True,
            )
        return self._client

    def namespaced_key(self, *parts: str) -> str:
        """Build a safe key rooted in the configured application namespace."""
        if not parts or any(not part or ":" in part for part in parts):
            raise ValueError("Redis key parts must be non-empty and contain no colons")
        return ":".join((self._settings.namespace, *parts))
