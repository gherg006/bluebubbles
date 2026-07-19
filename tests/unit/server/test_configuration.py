"""Tests for strict server configuration loading and safety checks."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from bluebubbles.server.configuration.capabilities import build_server_capabilities
from bluebubbles.server.configuration.loader import (
    ConfigurationLoader,
    redacted_server_configuration,
)
from bluebubbles.server.configuration.settings import (
    AttachmentSettings,
    DirectorySettings,
    EnvironmentName,
    MessagingSettings,
    MonitoringSettings,
    ProtocolSettings,
    RetentionSettings,
    ServerSettings,
    TLSSettings,
    TokenSettings,
)
from bluebubbles.server.configuration.validation import (
    validate_no_test_defaults,
    validate_path_permissions,
    validate_production_safety,
    validate_server_settings,
    validate_setting_relationships,
    validate_tls_files,
)
from bluebubbles.shared.configuration import (
    ConfigurationError,
    secret_permissions_are_unsafe,
)


def _write(path: Path, value: str) -> Path:
    path.write_text(value, encoding="utf-8")
    return path


def test_loader_applies_yaml_environment_secret_and_override_precedence(
    tmp_path: Path,
) -> None:
    config = tmp_path / "config"
    config.mkdir()
    _write(config / "base.yaml", "network:\n  port: 8000\n")
    _write(config / "development.yaml", "network:\n  port: 8001\n")
    secret = _write(tmp_path / "token", "a" * 40 + "\n")
    loader = ConfigurationLoader(
        config,
        {
            "BLUEBUBBLES_NETWORK__PORT": "8002",
            "BLUEBUBBLES_TOKEN_SECRET_FILE": str(secret),
        },
    )

    settings = loader.load_server_settings(overrides={"network": {"port": 8003}})

    assert settings.network.port == 8003
    assert settings.tokens.signing_secret.get_secret_value() == "a" * 40


def test_loader_rejects_unknown_environment_and_unknown_setting(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="BLUEBUBBLES_ENVIRONMENT"):
        ConfigurationLoader(
            tmp_path, {"BLUEBUBBLES_ENVIRONMENT": "staging"}
        ).load_server_settings()
    with pytest.raises(ConfigurationError, match="not_real"):
        ConfigurationLoader(
            tmp_path, {"BLUEBUBBLES_NOT_REAL": "true"}
        ).load_server_settings()


def test_loader_rejects_invalid_yaml_and_redacts_secrets(tmp_path: Path) -> None:
    config = tmp_path / "config"
    config.mkdir()
    _write(config / "base.yaml", "- not-a-mapping\n")
    loader = ConfigurationLoader(config, {})
    with pytest.raises(ConfigurationError, match="must contain a mapping"):
        loader.load_server_settings()

    report = redacted_server_configuration(ServerSettings())
    assert report["tokens"]["signing_secret"] == "**********"
    assert "development-only" not in str(report)


def test_secret_file_must_exist_and_not_be_empty(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(ConfigurationError, match="does not exist"):
        ConfigurationLoader(
            tmp_path, {"BLUEBUBBLES_TOKEN_SECRET_FILE": str(missing)}
        ).load_server_settings()
    empty = _write(tmp_path / "empty", "")
    with pytest.raises(ConfigurationError, match="empty"):
        ConfigurationLoader(
            tmp_path, {"BLUEBUBBLES_TOKEN_SECRET_FILE": str(empty)}
        ).load_server_settings()


@pytest.mark.parametrize("mode", [0o600, 0o640])
def test_secret_permissions_accept_owner_and_optional_group_read(mode: int) -> None:
    assert not secret_permissions_are_unsafe(mode)


@pytest.mark.parametrize("mode", [0o604, 0o644, 0o660, 0o666, 0o750])
def test_secret_permissions_reject_other_or_group_mutation(mode: int) -> None:
    assert secret_permissions_are_unsafe(mode)


@pytest.mark.parametrize(
    ("model", "changes", "message"),
    [
        (TLSSettings, {"enabled": True}, "certificate_path"),
        (TLSSettings, {"minimum_tls_version": "1.1"}, "minimum_tls_version"),
        (TokenSettings, {"signing_secret": "short"}, "32 bytes"),
        (MessagingSettings, {"default_page_size": 101}, "maximum_page_size"),
        (
            AttachmentSettings,
            {"default_chunk_size_bytes": 1},
            "chunk-size range",
        ),
        (
            RetentionSettings,
            {"temporary_upload_hours": 24},
            "orphan_attachment_hours",
        ),
        (
            MonitoringSettings,
            {"storage_warning_percentage": 95},
            "below critical",
        ),
        (
            ProtocolSettings,
            {"current_version": 2},
            "must be supported",
        ),
    ],
)
def test_nested_relationship_validation(
    model: type[object], changes: dict[str, object], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        model(**changes)


def test_directory_requires_provider_specific_fields() -> None:
    with pytest.raises(ValidationError, match="Active directory provider requires"):
        DirectorySettings.model_validate({"provider": "ldap"})


def test_production_rejects_all_unsafe_development_defaults() -> None:
    settings = ServerSettings.model_validate(
        {
            "application": {"environment": "production", "debug": True},
            "authentication": {"provider": "mock"},
            "database": {"echo_sql": True},
            "logging": {"redact_sensitive_values": False},
        }
    )
    with pytest.raises(ConfigurationError) as captured:
        validate_production_safety(settings)
    message = str(captured.value)
    assert "network.trusted_proxy_count" in message
    assert "authentication.provider" in message
    assert "tokens.signing_secret" in message
    assert "redis.url" in message


def test_production_accepts_tls_termination_only_on_loopback_behind_one_proxy() -> None:
    settings = ServerSettings.model_validate(
        {
            "application": {"environment": "production"},
            "network": {
                "host": "127.0.0.1",
                "port": 8000,
                "trusted_proxy_count": 1,
            },
            "tls": {"enabled": False},
            "directory": {
                "provider": "active_directory",
                "server": "ad.example.internal",
                "port": 636,
                "bind_dn": "CN=service,DC=example,DC=internal",
                "bind_password": "directory-secret",
                "base_dn": "DC=example,DC=internal",
            },
            "authentication": {
                "provider": "directory",
                "allow_local_accounts": False,
            },
            "database": {
                "url": "postgresql+asyncpg://app:unique-secret@127.0.0.1/bluebubbles"
            },
            "redis": {"url": "redis://:unique-secret@127.0.0.1:6379/0"},
            "tokens": {"signing_secret": "x" * 64},
        }
    )

    validate_production_safety(settings)


def test_production_rejects_test_namespace() -> None:
    settings = ServerSettings.model_validate(
        {
            "application": {"environment": EnvironmentName.PRODUCTION},
            "redis": {"namespace": "test-production"},
        }
    )
    with pytest.raises(ConfigurationError, match="redis.namespace"):
        validate_no_test_defaults(settings)


def test_cross_setting_worker_interval_must_match() -> None:
    settings = ServerSettings.model_validate(
        {"workers": {"directory_sync_interval_seconds": 100}}
    )
    with pytest.raises(ConfigurationError, match="must equal"):
        validate_setting_relationships(settings)


def test_storage_validation_creates_distinct_directories(tmp_path: Path) -> None:
    settings = ServerSettings.model_validate(
        {
            "storage": {
                "root_path": tmp_path / "root",
                "temporary_path": tmp_path / "temporary",
                "export_path": tmp_path / "exports",
            }
        }
    )
    validate_path_permissions(settings, create=True)
    assert settings.storage.root_path.is_dir()

    duplicate = settings.model_copy(
        update={
            "storage": settings.storage.model_copy(
                update={"temporary_path": settings.storage.root_path}
            )
        }
    )
    with pytest.raises(ConfigurationError, match="distinct"):
        validate_path_permissions(duplicate)


def test_tls_validation_rejects_missing_files(tmp_path: Path) -> None:
    settings = ServerSettings.model_validate(
        {
            "tls": {
                "enabled": True,
                "certificate_path": tmp_path / "missing.crt",
                "private_key_path": tmp_path / "missing.key",
            }
        }
    )
    with pytest.raises(ConfigurationError, match="existing absolute file"):
        validate_tls_files(settings)


def test_complete_validation_accepts_development_defaults() -> None:
    validate_server_settings(ServerSettings())


def test_client_capability_projection_contains_no_secrets() -> None:
    capabilities = build_server_capabilities(ServerSettings())
    payload = capabilities.model_dump(mode="json")
    assert payload["limits"]["maximum_group_members"] == 100
    assert payload["capabilities"]["multi_device_sessions"] == "unavailable"
    assert "signing_secret" not in str(payload)
