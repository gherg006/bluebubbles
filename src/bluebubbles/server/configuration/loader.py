"""Deterministic YAML, environment, and secret-file server settings loader."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from bluebubbles.server.configuration.settings import EnvironmentName, ServerSettings
from bluebubbles.server.configuration.validation import validate_server_settings
from bluebubbles.shared.configuration import (
    ConfigurationError,
    current_environment,
    environment_overrides,
    load_yaml_mapping,
    merge_configuration,
    secret_file_overrides,
)

_ALIASES = {
    "ENVIRONMENT": "application.environment",
    "SERVER_HOST": "network.host",
    "SERVER_PORT": "network.port",
    "DATABASE_URL": "database.url",
    "REDIS_URL": "redis.url",
    "TOKEN_SECRET": "tokens.signing_secret",
    "STORAGE_ROOT": "storage.root_path",
    "TLS_CERTIFICATE": "tls.certificate_path",
    "TLS_PRIVATE_KEY": "tls.private_key_path",
    "LDAP_SERVER": "directory.server",
    "LDAP_BIND_DN": "directory.bind_dn",
    "LDAP_BIND_PASSWORD": "directory.bind_password",
    "LDAP_BASE_DN": "directory.base_dn",
}
_SECRET_FILES = {
    "BLUEBUBBLES_TOKEN_SECRET_FILE": "tokens.signing_secret",
    "BLUEBUBBLES_LDAP_BIND_PASSWORD_FILE": "directory.bind_password",
    "BLUEBUBBLES_DATABASE_URL_FILE": "database.url",
    "BLUEBUBBLES_REDIS_URL_FILE": "redis.url",
}


class ConfigurationLoader:
    """Load and validate server settings using explicit source precedence."""

    def __init__(
        self,
        config_directory: Path | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        """Create a loader with injectable files and environment for tests."""
        project_root = Path(__file__).resolve().parents[4]
        self._config_directory = config_directory or project_root / "config" / "server"
        self._environ = environ if environ is not None else current_environment()

    def load_server_settings(
        self,
        environment: EnvironmentName | None = None,
        *,
        overrides: Mapping[str, Any] | None = None,
        verify_files: bool = False,
    ) -> ServerSettings:
        """Load all server sources and return a fully validated model."""
        selected = environment or self._selected_environment()
        values: dict[str, Any] = {}
        for path in (
            self._config_directory / "base.yaml",
            self._config_directory / f"{selected.value}.yaml",
        ):
            if path.exists():
                values = merge_configuration(values, self.load_yaml_file(path))
        values = merge_configuration(values, self.load_environment_values())
        values = merge_configuration(values, self.load_secret_files())
        if overrides:
            values = merge_configuration(values, overrides)
        values = merge_configuration(
            values, {"application": {"environment": selected.value}}
        )
        try:
            settings = ServerSettings.model_validate(values)
        except ValidationError as error:
            raise ConfigurationError(_safe_validation_message(error)) from error
        validate_server_settings(settings, verify_files=verify_files)
        return settings

    def load_yaml_file(self, path: Path) -> dict[str, Any]:
        """Load a YAML mapping from a named source file."""
        return load_yaml_mapping(path)

    def load_environment_values(self) -> dict[str, Any]:
        """Load documented and delimiter-based server environment variables."""
        return environment_overrides(
            self._environ, prefix="BLUEBUBBLES_", aliases=_ALIASES
        )

    def load_secret_files(self) -> dict[str, Any]:
        """Load only explicitly supported protected secret files."""
        return secret_file_overrides(self._environ, variables=_SECRET_FILES)

    def _selected_environment(self) -> EnvironmentName:
        raw = self._environ.get(
            "BLUEBUBBLES_ENVIRONMENT", EnvironmentName.DEVELOPMENT.value
        )
        try:
            return EnvironmentName(raw)
        except ValueError as error:
            raise ConfigurationError(
                "BLUEBUBBLES_ENVIRONMENT must be development, testing, "
                "demonstration, or production"
            ) from error


def redacted_server_configuration(settings: ServerSettings) -> dict[str, Any]:
    """Return a JSON-compatible settings report with every secret redacted."""
    return settings.model_dump(mode="json")


def _safe_validation_message(error: ValidationError) -> str:
    locations = [
        ".".join(str(part) for part in item["loc"])
        for item in error.errors(include_input=False)
    ]
    return "Invalid configuration at: " + ", ".join(locations)
