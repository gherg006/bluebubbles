"""Exclusive process lock for one authenticated client profile."""

from __future__ import annotations

import os
from contextlib import suppress
from pathlib import Path

from bluebubbles.shared.errors.exceptions import LocalStorageError


class ProfileLock:
    """Prevent two processes from mutating one local profile concurrently."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._descriptor: int | None = None

    @property
    def acquired(self) -> bool:
        """Report whether this object currently owns the lock file."""
        return self._descriptor is not None

    def acquire(self) -> None:
        """Create the exclusive lock, failing safely when already held."""
        if self.acquired:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = self._create_lock_file()
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        self._descriptor = descriptor

    def _create_lock_file(self) -> int:
        try:
            return os.open(
                self._path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError as error:
            if self._existing_owner_is_alive():
                raise LocalStorageError(
                    user_message="This BlueBubbles profile is already open."
                ) from error
            with suppress(FileNotFoundError):
                self._path.unlink()
            try:
                return os.open(
                    self._path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o600,
                )
            except FileExistsError as retry_error:
                raise LocalStorageError(
                    user_message="This BlueBubbles profile is already open."
                ) from retry_error

    def _existing_owner_is_alive(self) -> bool:
        try:
            owner = int(self._path.read_text(encoding="ascii"))
            if owner <= 0:
                return False
            os.kill(owner, 0)
        except (OSError, ValueError):
            return False
        return True

    def release(self) -> None:
        """Release the owned lock idempotently."""
        if self._descriptor is None:
            return
        os.close(self._descriptor)
        self._descriptor = None
        with suppress(FileNotFoundError):
            self._path.unlink()

    def __enter__(self) -> ProfileLock:
        self.acquire()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()
