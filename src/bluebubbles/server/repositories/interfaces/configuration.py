"""Configuration-version repository protocol."""

from collections.abc import Mapping
from typing import Protocol

from bluebubbles.server.domain.configuration import ConfigurationRevision


class ConfigurationRepository(Protocol):
    """Define append-only, secret-free configuration revision persistence."""

    async def append(
        self, revision: ConfigurationRevision, *, reason: str, restart_required: bool
    ) -> ConfigurationRevision: ...

    async def get_latest(self) -> ConfigurationRevision | None: ...

    async def get_public_values(self) -> Mapping[str, object] | None: ...
