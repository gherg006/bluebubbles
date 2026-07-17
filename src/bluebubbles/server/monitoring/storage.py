"""Encrypted-file storage readiness and capacity health checks."""

from __future__ import annotations

import logging
import os
import shutil
import stat
from pathlib import Path
from uuid import uuid4

from bluebubbles.server.configuration.settings import StorageSettings
from bluebubbles.shared.errors.exceptions import StorageUnavailableError
from bluebubbles.shared.models.health import ComponentHealth, HealthState


class StorageHealthCheck:
    """Validate configured storage paths without exposing them in health DTOs."""

    def __init__(self, settings: StorageSettings, logger: logging.Logger) -> None:
        """Store validated settings; filesystem changes occur only at startup."""
        self._settings = settings
        self._logger = logger
        self._started = False

    @property
    def started(self) -> bool:
        """Return whether every configured path passed readiness checks."""
        return self._started

    async def start(self) -> None:
        """Create allowed directories and verify containment, writes, and capacity.

        Raises:
            StorageUnavailableError: If any critical storage check fails.
        """
        if self._started:
            return
        try:
            self._verify_path_configuration()
            for path in self._paths:
                if not path.exists() and self._settings.create_missing_directories:
                    path.mkdir(parents=True, exist_ok=True)
                if not path.is_dir():
                    raise OSError("storage path is not a directory")
                self._verify_write(path)
            state = self._capacity_state()
            if state is HealthState.UNHEALTHY:
                raise OSError("storage reserve is exhausted")
        except OSError as error:
            raise StorageUnavailableError(
                user_message="Encrypted file storage is unavailable.",
                technical_message="Storage readiness verification failed.",
                retryable=True,
            ) from error
        self._started = True

    async def stop(self) -> None:
        """Clear readiness state; storage directories remain durable."""
        self._started = False

    async def check_health(self) -> ComponentHealth:
        """Return capacity and writability health without filesystem paths."""
        if not self._started:
            return ComponentHealth(name="storage", state=HealthState.UNHEALTHY)
        try:
            for path in self._paths:
                if not path.is_dir():
                    raise OSError("storage path is unavailable")
                self._verify_write(path)
            state = self._capacity_state()
        except OSError:
            state = HealthState.UNHEALTHY
        return ComponentHealth(name="storage", state=state)

    @property
    def _paths(self) -> tuple[Path, ...]:
        return (
            self._settings.root_path.resolve(),
            self._settings.temporary_path.resolve(),
            self._settings.export_path.resolve(),
        )

    def _verify_write(self, directory: Path) -> None:
        probe = directory / f".bluebubbles-health-{uuid4().hex}"
        try:
            with probe.open("xb") as stream:
                stream.write(b"health")
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            probe.unlink(missing_ok=True)

    def _verify_path_configuration(self) -> None:
        configured = (
            self._settings.root_path,
            self._settings.temporary_path,
            self._settings.export_path,
        )
        if any(not path.is_absolute() or ".." in path.parts for path in configured):
            raise OSError("storage paths must be absolute")
        if len(set(self._paths)) != len(self._paths):
            raise OSError("storage paths must be distinct")
        if not self._settings.allow_network_filesystem and any(
            str(path).startswith(("\\\\", "//")) for path in configured
        ):
            raise OSError("network storage is disabled")
        if os.name != "nt" and any(
            path.exists() and stat.S_IMODE(path.stat().st_mode) & stat.S_IWOTH
            for path in configured
        ):
            raise OSError("storage path is world-writable")

    def _capacity_state(self) -> HealthState:
        usage = shutil.disk_usage(self._settings.root_path)
        free_percentage = usage.free / usage.total * 100 if usage.total else 0
        if (
            usage.free < self._settings.reserved_free_bytes
            or free_percentage < self._settings.reserved_free_percentage
        ):
            return HealthState.UNHEALTHY
        return HealthState.HEALTHY
