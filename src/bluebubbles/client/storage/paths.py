"""Constrained per-profile paths for client-owned local data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from bluebubbles.shared.errors.exceptions import LocalStorageError


@dataclass(frozen=True, slots=True)
class ProfilePaths:
    """Resolve paths that cannot escape the configured profile root."""

    root: Path
    profile_id: UUID

    @property
    def profile_root(self) -> Path:
        """Return the canonical directory for this BlueBubbles identity."""
        return self._inside(self.root.expanduser().resolve() / str(self.profile_id))

    @property
    def database(self) -> Path:
        """Return the local SQLite database path."""
        return self.profile_root / "client_cache.db"

    @property
    def cache(self) -> Path:
        """Return the managed cache directory."""
        return self.profile_root / "cache"

    @property
    def recovery(self) -> Path:
        """Return the migration and diagnostic recovery directory."""
        return self.profile_root / "recovery"

    @property
    def lock_file(self) -> Path:
        """Return the exclusive profile lock path."""
        return self.profile_root / ".profile.lock"

    def initialise(self) -> None:
        """Create the profile-owned directories required by storage services."""
        for path in (self.profile_root, self.cache, self.recovery):
            path.mkdir(parents=True, exist_ok=True)

    def managed_path(self, relative: str) -> Path:
        """Resolve a caller-supplied managed path below the profile directory."""
        if not relative or Path(relative).is_absolute():
            raise LocalStorageError(user_message="The local cache path is invalid.")
        return self._inside(self.profile_root / relative)

    def _inside(self, candidate: Path) -> Path:
        root = self.root.expanduser().resolve()
        selected = candidate.resolve()
        if selected != root and root not in selected.parents:
            raise LocalStorageError(user_message="The local cache path is invalid.")
        return selected
