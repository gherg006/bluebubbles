"""Source-independent helpers for strict nested configuration loading."""

import json
import os
import stat
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from bluebubbles.shared.errors.exceptions import ConfigurationError

__all__ = [
    "ConfigurationError",
    "current_environment",
    "environment_overrides",
    "load_yaml_mapping",
    "merge_configuration",
    "secret_file_overrides",
]


def merge_configuration(
    base: Mapping[str, Any], override: Mapping[str, Any]
) -> dict[str, Any]:
    """Recursively merge mappings while replacing scalar and collection values."""
    merged = deepcopy(dict(base))
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, Mapping) and isinstance(value, Mapping):
            merged[key] = merge_configuration(existing, value)
        else:
            merged[key] = deepcopy(value)
    return merged


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    """Load one UTF-8 YAML mapping, rejecting malformed or non-mapping documents."""
    try:
        with path.open(encoding="utf-8") as stream:
            document = yaml.safe_load(stream)
    except (OSError, yaml.YAMLError) as error:
        raise ConfigurationError(
            f"Cannot load configuration file {path.name}: {error}"
        ) from error
    if document is None:
        return {}
    if not isinstance(document, dict) or not all(
        isinstance(key, str) for key in document
    ):
        raise ConfigurationError(
            f"Configuration file {path.name} must contain a mapping"
        )
    return document


def environment_overrides(
    environ: Mapping[str, str], *, prefix: str, aliases: Mapping[str, str] | None = None
) -> dict[str, Any]:
    """Convert prefixed variables into nested dictionaries using ``__`` separators."""
    values: dict[str, Any] = {}
    for variable, raw_value in environ.items():
        if not variable.startswith(prefix) or variable.endswith("_FILE"):
            continue
        suffix = variable[len(prefix) :]
        dotted = (
            aliases.get(suffix, suffix.lower().replace("__", "."))
            if aliases
            else suffix.lower().replace("__", ".")
        )
        target = values
        parts = dotted.split(".")
        for part in parts[:-1]:
            child = target.setdefault(part, {})
            if not isinstance(child, dict):
                raise ConfigurationError(
                    f"Environment variable {variable} conflicts with another override"
                )
            target = child
        target[parts[-1]] = _parse_environment_value(raw_value)
    return values


def secret_file_overrides(
    environ: Mapping[str, str], *, variables: Mapping[str, str]
) -> dict[str, Any]:
    """Read explicitly supported secret files and map them to setting paths."""
    values: dict[str, Any] = {}
    for variable, dotted_path in variables.items():
        raw_path = environ.get(variable)
        if raw_path is None:
            continue
        path = Path(raw_path).expanduser()
        _validate_secret_file(path, variable)
        try:
            secret = (
                path.read_text(encoding="utf-8").removesuffix("\r\n").removesuffix("\n")
            )
        except OSError as error:
            raise ConfigurationError(
                f"Cannot read secret file for {variable}: {error}"
            ) from error
        if not secret:
            raise ConfigurationError(f"Secret file for {variable} is empty")
        target = values
        parts = dotted_path.split(".")
        for part in parts[:-1]:
            child = target.setdefault(part, {})
            if not isinstance(child, dict):
                raise ConfigurationError(
                    f"Secret file mapping for {variable} is invalid"
                )
            target = child
        target[parts[-1]] = secret
    return values


def current_environment() -> Mapping[str, str]:
    """Return the process environment at the configuration boundary."""
    return os.environ


def _parse_environment_value(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _validate_secret_file(path: Path, variable: str) -> None:
    if not path.is_file():
        raise ConfigurationError(
            f"Secret file for {variable} does not exist or is not a file"
        )
    if os.name != "nt" and secret_permissions_are_unsafe(
        stat.S_IMODE(path.stat().st_mode)
    ):
        raise ConfigurationError(
            f"Secret file for {variable} must be owner-only or group-readable"
        )


def secret_permissions_are_unsafe(mode: int) -> bool:
    """Allow owner access and optional group read, but no other permission bits."""
    return bool(mode & 0o037)
