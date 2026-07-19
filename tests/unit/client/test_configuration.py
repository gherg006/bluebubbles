"""Tests for isolated Windows client settings and server policy resolution."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from bluebubbles.client.bootstrap import verify_client_environment
from bluebubbles.client.configuration.effective_settings import (
    EffectiveSettingsResolver,
)
from bluebubbles.client.configuration.loader import ClientConfigurationLoader
from bluebubbles.client.configuration.policies import ClientPolicy
from bluebubbles.client.configuration.preferences import UserPreferences
from bluebubbles.client.configuration.settings import (
    ClientSettings,
    ClientTLSSettings,
    ServerConnectionSettings,
)
from bluebubbles.shared.configuration import ConfigurationError


def test_client_loader_reads_only_client_namespace(tmp_path: Path) -> None:
    config = tmp_path / "client.yaml"
    config.write_text(
        "application:\n  environment: development\n"
        "server:\n  base_url: http://127.0.0.1:9000\n"
        "  websocket_url: ws://127.0.0.1:9000/ws\n",
        encoding="utf-8",
    )
    settings = ClientConfigurationLoader(
        config,
        {
            "BLUEBUBBLES_CLIENT_SERVER__RETRY_LIMIT": "7",
            "BLUEBUBBLES_SERVER_PORT": "9999",
        },
    ).load_client_settings()
    assert settings.server.retry_limit == 7
    assert settings.server.base_url.port == 9000


def test_client_loader_reports_unknown_setting_without_value(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="unknown"):
        ClientConfigurationLoader(
            tmp_path / "absent.yaml", {"BLUEBUBBLES_CLIENT_UNKNOWN": "secret"}
        ).load_client_settings()


def test_client_loader_uses_managed_program_data_or_explicit_file(
    tmp_path: Path,
) -> None:
    managed = tmp_path / "BlueBubbles" / "client.yaml"
    managed.parent.mkdir()
    managed.write_text(
        "application:\n  environment: development\n"
        "server:\n  base_url: http://127.0.0.1:9100\n"
        "  websocket_url: ws://127.0.0.1:9100/api/v1/ws\n",
        encoding="utf-8",
    )
    managed_settings = ClientConfigurationLoader(
        environ={"PROGRAMDATA": str(tmp_path)}
    ).load_client_settings()
    explicit_settings = ClientConfigurationLoader(
        environ={
            "BLUEBUBBLES_CLIENT_CONFIG_FILE": str(managed),
            "BLUEBUBBLES_CLIENT_SERVER__RETRY_LIMIT": "5",
        }
    ).load_client_settings()

    assert managed_settings.server.base_url.port == 9100
    assert explicit_settings.server.retry_limit == 5


def test_production_client_requires_encrypted_verified_transport() -> None:
    with pytest.raises(ValidationError, match="https and wss"):
        ClientSettings.model_validate(
            {
                "server": {
                    "base_url": "http://192.168.0.210:8443",
                    "websocket_url": "ws://192.168.0.210:8443/ws",
                }
            }
        )
    with pytest.raises(ValidationError, match="verify certificates"):
        ClientSettings.model_validate({"tls": {"verify_certificates": False}})


def test_websocket_scheme_and_pin_are_validated() -> None:
    with pytest.raises(ValidationError, match="ws or wss"):
        ServerConnectionSettings.model_validate(
            {"websocket_url": "https://server.invalid/ws"}
        )
    with pytest.raises(ValidationError, match="64 hexadecimal"):
        ClientTLSSettings(pinned_certificate_fingerprint="not-a-pin")
    tls = ClientTLSSettings(pinned_certificate_fingerprint="AA:" * 31 + "AA")
    assert tls.pinned_certificate_fingerprint == "AA" * 32


def test_pinned_fingerprint_requires_pinning_feature() -> None:
    with pytest.raises(ValidationError, match="requires certificate pinning"):
        ClientSettings.model_validate(
            {
                "tls": {
                    "allow_certificate_pinning": False,
                    "pinned_certificate_fingerprint": "A" * 64,
                }
            }
        )


def test_policy_constrains_preferences_without_mutating_them() -> None:
    installation = ClientSettings()
    preferences = UserPreferences(
        cache_limit_bytes=4_000_000_000,
        show_message_previews=True,
    )
    policy = ClientPolicy(
        maximum_attachment_bytes=1_000_000,
        maximum_cache_bytes=500_000_000,
        decrypted_cache_allowed=False,
        read_receipts_enabled=False,
        blocked_file_extensions=(".exe",),
        maximum_group_members=50,
    )
    effective = EffectiveSettingsResolver().resolve(installation, preferences, policy)
    assert effective.cache_limit_bytes == 500_000_000
    assert effective.show_message_previews is False
    assert effective.overridden_preferences == (
        "cache_limit_bytes",
        "show_message_previews",
    )
    assert preferences.show_message_previews is True


def test_client_environment_requires_absolute_paths() -> None:
    invalid = ClientSettings.model_construct(
        storage=ClientSettings().storage.model_copy(
            update={"profile_root": Path("relative")}
        ),
        transfers=ClientSettings().transfers,
    )
    with pytest.raises(ValueError, match="profile_root"):
        verify_client_environment(invalid)
