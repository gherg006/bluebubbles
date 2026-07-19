"""Cross-setting and production-safety validation for server configuration."""

import os
import stat
from urllib.parse import urlsplit

from bluebubbles.server.configuration.settings import (
    AuthenticationProviderName,
    DirectoryProviderName,
    EnvironmentName,
    ServerSettings,
)
from bluebubbles.shared.configuration import ConfigurationError

_UNSAFE_TOKEN_SECRETS = frozenset(
    {
        "development-only-token-secret-replace-before-production",
        "replace-me-with-at-least-32-random-bytes",
    }
)


def validate_setting_relationships(settings: ServerSettings) -> None:
    """Validate relationships not owned by a single nested model."""
    if (
        settings.authentication.directory_sync_interval_seconds
        != settings.workers.directory_sync_interval_seconds
    ):
        raise ConfigurationError(
            "authentication.directory_sync_interval_seconds must equal "
            "workers.directory_sync_interval_seconds"
        )
    if (
        settings.authentication.provider is AuthenticationProviderName.DIRECTORY
        and settings.directory.provider is DirectoryProviderName.DISABLED
    ):
        raise ConfigurationError(
            "authentication.provider directory requires an enabled directory provider"
        )
    if (
        settings.authentication.provider is AuthenticationProviderName.LOCAL
        and not settings.authentication.allow_local_accounts
    ):
        raise ConfigurationError(
            "authentication.provider local requires allow_local_accounts"
        )


def validate_production_safety(settings: ServerSettings) -> None:
    """Reject defaults and unsafe options in the production profile."""
    if settings.application.environment is not EnvironmentName.PRODUCTION:
        return
    failures: list[str] = []
    if settings.application.debug:
        failures.append("application.debug must be false")
    if not settings.directory.use_tls:
        failures.append("directory.use_tls must be true")
    if not settings.tls.enabled:
        if settings.network.host not in {"127.0.0.1", "::1", "localhost"}:
            failures.append(
                "network.host must be loopback when TLS terminates at a reverse proxy"
            )
        if settings.network.trusted_proxy_count != 1:
            failures.append(
                "network.trusted_proxy_count must be 1 when TLS terminates at Nginx"
            )
    if settings.authentication.provider in {
        AuthenticationProviderName.LOCAL,
        AuthenticationProviderName.MOCK,
    }:
        failures.append(
            "authentication.provider must use the production directory provider"
        )
    if settings.database.echo_sql:
        failures.append("database.echo_sql must be false")
    database_url = settings.database.url.get_secret_value()
    if "development-only" in database_url or "replace" in database_url:
        failures.append("database.url must not contain development credentials")
    redis_url = settings.redis.url.get_secret_value()
    if urlsplit(redis_url).password is None or "replace" in redis_url:
        failures.append("redis.url must use non-example authentication credentials")
    if settings.tokens.signing_secret.get_secret_value() in _UNSAFE_TOKEN_SECRETS:
        failures.append("tokens.signing_secret must be a unique production secret")
    if not settings.logging.redact_sensitive_values:
        failures.append("logging.redact_sensitive_values must be true")
    if failures:
        raise ConfigurationError(
            "Unsafe production configuration: " + "; ".join(failures)
        )


def validate_tls_files(settings: ServerSettings) -> None:
    """Verify referenced certificate files and private-key permissions."""
    if not settings.tls.enabled:
        return
    assert settings.tls.certificate_path is not None
    assert settings.tls.private_key_path is not None
    for label, path in (
        ("tls.certificate_path", settings.tls.certificate_path),
        ("tls.private_key_path", settings.tls.private_key_path),
    ):
        if not path.is_absolute() or not path.is_file():
            raise ConfigurationError(
                f"{label} must reference an existing absolute file"
            )
    if (
        os.name != "nt"
        and stat.S_IMODE(settings.tls.private_key_path.stat().st_mode) & 0o077
    ):
        raise ConfigurationError(
            "tls.private_key_path must not be accessible by group or others"
        )


def validate_path_permissions(
    settings: ServerSettings, *, create: bool = False
) -> None:
    """Verify absolute, distinct, non-world-writable server storage paths."""
    paths = (
        settings.storage.root_path,
        settings.storage.temporary_path,
        settings.storage.export_path,
    )
    normalised = tuple(path.resolve() for path in paths)
    if len(set(normalised)) != len(normalised):
        raise ConfigurationError("storage paths must be distinct")
    for path in paths:
        if not path.is_absolute() or ".." in path.parts:
            raise ConfigurationError(
                "storage paths must be absolute and contain no parent traversal"
            )
        if not path.exists() and create and settings.storage.create_missing_directories:
            path.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if not path.is_dir():
                raise ConfigurationError("configured storage path must be a directory")
            if os.name != "nt" and stat.S_IMODE(path.stat().st_mode) & stat.S_IWOTH:
                raise ConfigurationError(
                    "configured storage path must not be world-writable"
                )


def validate_no_test_defaults(settings: ServerSettings) -> None:
    """Reject testing and demonstration identity from production."""
    if (
        settings.application.environment is EnvironmentName.PRODUCTION
        and settings.redis.namespace.startswith(("test", "demo"))
    ):
        raise ConfigurationError(
            "redis.namespace must not use a test or demonstration namespace"
        )


def validate_server_settings(
    settings: ServerSettings, *, verify_files: bool = False, create_paths: bool = False
) -> None:
    """Run all configuration checks in a stable order."""
    validate_setting_relationships(settings)
    validate_production_safety(settings)
    validate_no_test_defaults(settings)
    if verify_files:
        validate_tls_files(settings)
        validate_path_permissions(settings, create=create_paths)
