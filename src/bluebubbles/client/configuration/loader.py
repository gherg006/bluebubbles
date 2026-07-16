"""Deterministic installation settings loader for Windows clients."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from bluebubbles.client.configuration.settings import ClientSettings
from bluebubbles.shared.configuration import (
    ConfigurationError,
    current_environment,
    environment_overrides,
    load_yaml_mapping,
    merge_configuration,
)

_ALIASES = {
    "SERVER_URL": "server.base_url",
    "WEBSOCKET_URL": "server.websocket_url",
    "TRUSTED_CA": "tls.trusted_ca_path",
    "PROFILE_ROOT": "storage.profile_root",
}


class ClientConfigurationLoader:
    """Load client YAML and client-only environment overrides."""

    def __init__(
        self,
        config_file: Path | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        """Create a loader with injectable sources for deterministic tests."""
        project_root = Path(__file__).resolve().parents[4]
        self._config_file = (
            config_file or project_root / "config" / "client" / "default.yaml"
        )
        self._environ = environ if environ is not None else current_environment()

    def load_client_settings(
        self, *, overrides: Mapping[str, Any] | None = None
    ) -> ClientSettings:
        """Load and validate client settings without reading server variables."""
        values: dict[str, Any] = {}
        if self._config_file.exists():
            values = load_yaml_mapping(self._config_file)
        values = merge_configuration(values, self.load_environment_values())
        if overrides:
            values = merge_configuration(values, overrides)
        try:
            return ClientSettings.model_validate(values)
        except ValidationError as error:
            locations = [
                ".".join(str(part) for part in item["loc"])
                for item in error.errors(include_input=False)
            ]
            raise ConfigurationError(
                "Invalid client configuration at: " + ", ".join(locations)
            ) from error

    def load_environment_values(self) -> dict[str, Any]:
        """Load only variables in the client-specific namespace."""
        return environment_overrides(
            self._environ, prefix="BLUEBUBBLES_CLIENT_", aliases=_ALIASES
        )
