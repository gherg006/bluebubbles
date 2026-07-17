"""Strict installation-wide settings models for Windows desktop clients."""

from pathlib import Path
from typing import Annotated

from pydantic import AnyHttpUrl, AnyUrl, Field, field_validator, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from bluebubbles.shared._model import ContractModel
from bluebubbles.version import __version__


def _windows_profile_root() -> Path:
    """Return a stable per-user profile location without requiring Windows APIs."""
    return Path.home() / "AppData" / "Local" / "BlueBubbles" / "profiles"


def _windows_download_root() -> Path:
    """Return the conventional per-user download location."""
    return Path.home() / "Downloads" / "BlueBubbles"


class ClientApplicationSettings(ContractModel):
    """Define desktop client identity and appearance defaults."""

    name: str = "BlueBubbles"
    version: str = __version__
    environment: str = "production"
    default_theme: str = "system"
    reduced_motion: bool = False


class ServerConnectionSettings(ContractModel):
    """Define how the desktop client reaches the LAN server."""

    base_url: AnyHttpUrl = AnyHttpUrl("https://192.168.0.210:8443")
    websocket_url: AnyUrl = AnyUrl("wss://192.168.0.210:8443/api/v1/ws")
    connect_timeout_seconds: Annotated[float, Field(gt=0, le=120)] = 10.0
    request_timeout_seconds: Annotated[float, Field(gt=0, le=300)] = 30.0
    retry_limit: Annotated[int, Field(ge=0, le=20)] = 3
    automatic_reconnect: bool = True

    @field_validator("websocket_url")
    @classmethod
    def validate_websocket_scheme(cls, value: AnyUrl) -> AnyUrl:
        """Reject URL schemes unsupported by the WebSocket transport."""
        if value.scheme not in {"ws", "wss"}:
            raise ValueError("websocket_url must use ws or wss")
        return value


class ClientTLSSettings(ContractModel):
    """Define client certificate verification and optional pinning."""

    verify_certificates: bool = True
    trusted_ca_path: Path | None = None
    expected_hostname: str | None = None
    allow_certificate_pinning: bool = True
    pinned_certificate_fingerprint: str | None = None

    @field_validator("pinned_certificate_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str | None) -> str | None:
        """Normalise a SHA-256 certificate fingerprint."""
        if value is None:
            return None
        normalised = value.replace(":", "").upper()
        if len(normalised) != 64 or any(
            character not in "0123456789ABCDEF" for character in normalised
        ):
            raise ValueError(
                "pinned certificate fingerprint must be 64 hexadecimal characters"
            )
        return normalised


class ClientNetworkSettings(ContractModel):
    """Define local networking limits and retry timing."""

    retry_base_delay_seconds: Annotated[float, Field(gt=0, le=60)] = 0.5
    retry_maximum_delay_seconds: Annotated[float, Field(gt=0, le=300)] = 30.0
    websocket_heartbeat_seconds: Annotated[int, Field(gt=0)] = 30

    @model_validator(mode="after")
    def validate_retry_delays(self) -> "ClientNetworkSettings":
        """Require the retry cap to be at least the initial delay."""
        if self.retry_maximum_delay_seconds < self.retry_base_delay_seconds:
            raise ValueError(
                "retry_maximum_delay_seconds cannot be below the base delay"
            )
        return self


class ClientStorageSettings(ContractModel):
    """Define installation-wide local storage defaults."""

    profile_root: Path = Field(default_factory=_windows_profile_root)
    default_cache_limit_bytes: Annotated[int, Field(gt=0)] = 2_147_483_648
    maximum_cache_limit_bytes: Annotated[int, Field(gt=0)] = 5_368_709_120
    thumbnail_cache_limit_bytes: Annotated[int, Field(ge=0)] = 268_435_456
    attachment_cache_limit_bytes: Annotated[int, Field(ge=0)] = 1_610_612_736
    encrypted_message_cache_limit_bytes: Annotated[int, Field(ge=0)] = 268_435_456
    recent_messages_per_conversation: Annotated[int, Field(ge=0, le=100_000)] = 500
    cleanup_target_ratio: Annotated[float, Field(ge=0.5, lt=1)] = 0.9
    disk_warning_free_bytes: Annotated[int, Field(gt=0)] = 2_147_483_648
    disk_critical_free_bytes: Annotated[int, Field(gt=0)] = 524_288_000
    local_database_backend: str = "sqlite"
    retain_cache_after_logout: bool = True

    @model_validator(mode="after")
    def validate_cache_limits(self) -> "ClientStorageSettings":
        """Require default and component limits to fit within the maximum."""
        if self.default_cache_limit_bytes > self.maximum_cache_limit_bytes:
            raise ValueError(
                "default_cache_limit_bytes cannot exceed maximum_cache_limit_bytes"
            )
        if self.disk_critical_free_bytes >= self.disk_warning_free_bytes:
            raise ValueError(
                "disk_critical_free_bytes must be below disk_warning_free_bytes"
            )
        return self


class ClientTransferSettings(ContractModel):
    """Define local encrypted attachment transfer behaviour."""

    default_download_directory: Path = Field(default_factory=_windows_download_root)
    upload_concurrency: Annotated[int, Field(gt=0, le=16)] = 2
    download_concurrency: Annotated[int, Field(gt=0, le=16)] = 3
    chunk_concurrency: Annotated[int, Field(gt=0, le=16)] = 2
    automatic_image_download_limit_bytes: Annotated[int, Field(ge=0)] = 10_485_760
    default_upload_limit_bytes_per_second: Annotated[int, Field(gt=0)] | None = None
    default_download_limit_bytes_per_second: Annotated[int, Field(gt=0)] | None = None


class ClientLoggingSettings(ContractModel):
    """Define safe client diagnostic logging."""

    level: str = "INFO"
    directory: Path = Path.home() / "AppData" / "Local" / "BlueBubbles" / "logs"
    json_format: bool = True
    console_enabled: bool = False
    maximum_file_bytes: Annotated[int, Field(gt=0)] = 10_485_760
    retained_files: Annotated[int, Field(gt=0)] = 5
    redact_sensitive_values: bool = True

    @field_validator("level")
    @classmethod
    def validate_level(cls, value: str) -> str:
        """Normalise and validate a standard logging level."""
        normalised = value.upper()
        if normalised not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("unsupported logging level")
        return normalised


class ClientFeatureFlagSettings(ContractModel):
    """Define locally available UI features, still constrained by server policy."""

    local_search: bool = True
    desktop_notifications: bool = True
    certificate_pinning: bool = True


class ClientProtocolSettings(ContractModel):
    """Define protocols implemented by this client build."""

    supported_versions: list[int] = Field(default_factory=lambda: [1])

    @field_validator("supported_versions")
    @classmethod
    def validate_versions(cls, values: list[int]) -> list[int]:
        """Require unique positive protocol versions."""
        if (
            not values
            or len(values) != len(set(values))
            or any(value <= 0 for value in values)
        ):
            raise ValueError("supported_versions must contain unique positive versions")
        return values


class ClientSettings(BaseSettings):
    """Define validated installation-wide desktop client configuration."""

    model_config = SettingsConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    application: ClientApplicationSettings = Field(
        default_factory=ClientApplicationSettings
    )
    server: ServerConnectionSettings = Field(default_factory=ServerConnectionSettings)
    tls: ClientTLSSettings = Field(default_factory=ClientTLSSettings)
    network: ClientNetworkSettings = Field(default_factory=ClientNetworkSettings)
    storage: ClientStorageSettings = Field(default_factory=ClientStorageSettings)
    transfers: ClientTransferSettings = Field(default_factory=ClientTransferSettings)
    logging: ClientLoggingSettings = Field(default_factory=ClientLoggingSettings)
    features: ClientFeatureFlagSettings = Field(
        default_factory=ClientFeatureFlagSettings
    )
    protocol: ClientProtocolSettings = Field(default_factory=ClientProtocolSettings)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Accept explicit model input while disabling implicit raw sources."""
        del settings_cls, env_settings, dotenv_settings, file_secret_settings
        return (init_settings,)

    @model_validator(mode="after")
    def validate_transport_security(self) -> "ClientSettings":
        """Require encrypted transports and certificate checking outside development."""
        if self.application.environment == "production":
            if (
                self.server.base_url.scheme != "https"
                or self.server.websocket_url.scheme != "wss"
            ):
                raise ValueError("production client endpoints must use https and wss")
            if not self.tls.verify_certificates:
                raise ValueError("production clients must verify certificates")
        if (
            self.tls.pinned_certificate_fingerprint
            and not self.tls.allow_certificate_pinning
        ):
            raise ValueError(
                "a pinned fingerprint requires certificate pinning to be enabled"
            )
        return self
