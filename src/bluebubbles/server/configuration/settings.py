"""Strict, secret-aware settings models for the BlueBubbles server."""

from enum import StrEnum
from pathlib import Path
from typing import Annotated
from uuid import UUID

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from bluebubbles.shared._model import ContractModel
from bluebubbles.version import __version__


class EnvironmentName(StrEnum):
    """Identify the supported deployment profiles."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    DEMONSTRATION = "demonstration"
    PRODUCTION = "production"


class DirectoryProviderName(StrEnum):
    """Identify the configured directory integration."""

    DISABLED = "disabled"
    LDAP = "ldap"
    ACTIVE_DIRECTORY = "active_directory"


class AuthenticationProviderName(StrEnum):
    """Identify an authentication adapter without constructing it."""

    LOCAL = "local"
    DIRECTORY = "directory"
    MOCK = "mock"


class LogLevel(StrEnum):
    """Define accepted application log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ApplicationSettings(ContractModel):
    """Define general server identity and environment behaviour."""

    name: str = "BlueBubbles"
    environment: EnvironmentName = EnvironmentName.DEVELOPMENT
    version: str = __version__
    debug: bool = False
    timezone: str = "UTC"
    instance_id: UUID = UUID(int=0)


class NetworkSettings(ContractModel):
    """Define the private server listener and request limits."""

    host: str = "127.0.0.1"
    port: Annotated[int, Field(ge=1, le=65535)] = 8443
    trusted_proxy_count: Annotated[int, Field(ge=0)] = 0
    request_timeout_seconds: Annotated[int, Field(gt=0)] = 30
    maximum_request_body_bytes: Annotated[int, Field(gt=0)] = 10_485_760
    websocket_auth_timeout_seconds: Annotated[int, Field(gt=0)] = 10
    websocket_heartbeat_seconds: Annotated[int, Field(gt=0)] = 30
    websocket_missed_heartbeat_limit: Annotated[int, Field(gt=0)] = 3


class TLSSettings(ContractModel):
    """Define server certificate configuration."""

    enabled: bool = False
    certificate_path: Path | None = None
    private_key_path: Path | None = None
    certificate_chain_path: Path | None = None
    minimum_tls_version: str = "1.2"

    @model_validator(mode="after")
    def validate_certificate_pair(self) -> "TLSSettings":
        """Require both certificate inputs whenever TLS is enabled."""
        if self.enabled and (
            self.certificate_path is None or self.private_key_path is None
        ):
            raise ValueError("TLS requires certificate_path and private_key_path")
        if self.minimum_tls_version not in {"1.2", "1.3"}:
            raise ValueError("minimum_tls_version must be 1.2 or 1.3")
        return self


class DatabaseSettings(ContractModel):
    """Define PostgreSQL connectivity and pooling."""

    url: SecretStr = SecretStr(
        "postgresql+asyncpg://bluebubbles:development-only@127.0.0.1/bluebubbles"
    )
    pool_size: Annotated[int, Field(gt=0)] = 10
    maximum_overflow: Annotated[int, Field(ge=0)] = 10
    connection_timeout_seconds: Annotated[int, Field(gt=0)] = 10
    statement_timeout_seconds: Annotated[int, Field(gt=0)] = 30
    pool_recycle_seconds: Annotated[int, Field(gt=0)] = 1800
    echo_sql: bool = False


class RedisSettings(ContractModel):
    """Define Redis connectivity and namespace behaviour."""

    url: SecretStr = SecretStr("redis://127.0.0.1:6379/0")
    namespace: Annotated[str, Field(min_length=1)] = "bluebubbles"
    connection_timeout_seconds: Annotated[int, Field(gt=0)] = 5
    operation_timeout_seconds: Annotated[int, Field(gt=0)] = 5
    maximum_connections: Annotated[int, Field(gt=0)] = 20
    fallback_enabled: bool = True


class DirectorySettings(ContractModel):
    """Define LDAP or Active Directory integration."""

    provider: DirectoryProviderName = DirectoryProviderName.DISABLED
    server: str | None = None
    port: Annotated[int, Field(ge=1, le=65535)] | None = None
    use_tls: bool = True
    bind_dn: str | None = None
    bind_password: SecretStr | None = None
    base_dn: str | None = None
    user_search_base: str | None = None
    group_search_base: str | None = None
    username_attribute: str = "sAMAccountName"
    guid_attribute: str = "objectGUID"
    email_attribute: str = "mail"
    department_attribute: str = "department"
    job_title_attribute: str = "title"
    connection_timeout_seconds: Annotated[int, Field(gt=0)] = 10
    search_timeout_seconds: Annotated[int, Field(gt=0)] = 10

    @model_validator(mode="after")
    def validate_active_provider(self) -> "DirectorySettings":
        """Require connection fields only for an active directory provider."""
        if self.provider is not DirectoryProviderName.DISABLED:
            missing = [
                name
                for name in ("server", "port", "bind_dn", "bind_password", "base_dn")
                if getattr(self, name) is None
            ]
            if missing:
                raise ValueError(
                    "Active directory provider requires: " + ", ".join(missing)
                )
        return self


class AuthenticationSettings(ContractModel):
    """Define authentication and account lockout behaviour."""

    provider: AuthenticationProviderName = AuthenticationProviderName.LOCAL
    allow_local_accounts: bool = True
    failed_login_limit: Annotated[int, Field(gt=0)] = 5
    failed_login_window_seconds: Annotated[int, Field(gt=0)] = 300
    application_lockout_seconds: Annotated[int, Field(gt=0)] = 900
    directory_sync_interval_seconds: Annotated[int, Field(gt=0)] = 3600
    default_role: str = "member"
    one_primary_crypto_device: bool = True


class TokenSettings(ContractModel):
    """Define session-token signing and lifetime rules."""

    signing_algorithm: str = "HS256"
    signing_secret: SecretStr = SecretStr(
        "development-only-token-secret-replace-before-production"
    )
    issuer: str = "bluebubbles"
    audience: str = "bluebubbles-client"
    access_token_lifetime_seconds: Annotated[int, Field(gt=0)] = 900
    refresh_token_lifetime_seconds: Annotated[int, Field(gt=0)] = 604_800
    rotation_enabled: bool = True
    reuse_detection_enabled: bool = True

    @model_validator(mode="after")
    def validate_secret_length(self) -> "TokenSettings":
        """Reject signing material shorter than 32 encoded bytes."""
        if len(self.signing_secret.get_secret_value().encode("utf-8")) < 32:
            raise ValueError("signing_secret must contain at least 32 bytes")
        return self


class StorageSettings(ContractModel):
    """Define encrypted attachment storage paths and capacity reserves."""

    root_path: Path = Path("data/attachments").resolve()
    temporary_path: Path = Path("data/temporary").resolve()
    export_path: Path = Path("data/exports").resolve()
    reserved_free_bytes: Annotated[int, Field(ge=0)] = 1_073_741_824
    reserved_free_percentage: Annotated[float, Field(ge=0, le=100)] = 5.0
    create_missing_directories: bool = True
    allow_network_filesystem: bool = False


class MessagingSettings(ContractModel):
    """Define message limits and conversation behaviour."""

    client_plaintext_character_limit: Annotated[int, Field(ge=1, le=50_000)] = 8000
    maximum_encrypted_request_bytes: Annotated[int, Field(gt=0)] = 1_048_576
    default_page_size: Annotated[int, Field(gt=0)] = 50
    maximum_page_size: Annotated[int, Field(gt=0)] = 100
    edit_window_seconds: Annotated[int, Field(ge=0)] = 900
    direct_conversation_unique: bool = True
    read_receipts_enabled: bool = True
    typing_indicators_enabled: bool = True
    maximum_group_members: Annotated[int, Field(gt=1)] = 100

    @model_validator(mode="after")
    def validate_page_sizes(self) -> "MessagingSettings":
        """Ensure the default page fits within the server maximum."""
        if self.default_page_size > self.maximum_page_size:
            raise ValueError("default_page_size cannot exceed maximum_page_size")
        return self


class AttachmentSettings(ContractModel):
    """Define encrypted attachment transfer limits."""

    maximum_plaintext_size_bytes: Annotated[int, Field(gt=0)] = 2_147_483_648
    default_chunk_size_bytes: Annotated[int, Field(gt=0)] = 1_048_576
    minimum_chunk_size_bytes: Annotated[int, Field(gt=0)] = 262_144
    maximum_chunk_size_bytes: Annotated[int, Field(gt=0)] = 8_388_608
    upload_session_lifetime_seconds: Annotated[int, Field(gt=0)] = 3600
    orphan_lifetime_seconds: Annotated[int, Field(gt=0)] = 86_400
    maximum_concurrent_uploads_per_user: Annotated[int, Field(gt=0)] = 3
    blocked_extensions: set[str] = Field(
        default_factory=lambda: {".exe", ".msi", ".bat"}
    )
    thumbnail_maximum_bytes: Annotated[int, Field(gt=0)] = 524_288

    @model_validator(mode="after")
    def validate_chunk_sizes(self) -> "AttachmentSettings":
        """Require the default chunk size to remain inside accepted bounds."""
        if (
            not self.minimum_chunk_size_bytes
            <= self.default_chunk_size_bytes
            <= self.maximum_chunk_size_bytes
        ):
            raise ValueError(
                "default_chunk_size_bytes must be inside the chunk-size range"
            )
        if self.maximum_chunk_size_bytes > self.maximum_plaintext_size_bytes:
            raise ValueError("maximum_chunk_size_bytes cannot exceed attachment size")
        return self


class RateLimitSettings(ContractModel):
    """Define protected endpoint request thresholds."""

    login_requests_per_window: Annotated[int, Field(gt=0)] = 10
    login_window_seconds: Annotated[int, Field(gt=0)] = 60
    message_requests_per_minute: Annotated[int, Field(gt=0)] = 120
    search_requests_per_minute: Annotated[int, Field(gt=0)] = 60
    administration_requests_per_minute: Annotated[int, Field(gt=0)] = 60
    upload_chunk_requests_per_minute: Annotated[int, Field(gt=0)] = 600
    websocket_events_per_minute: Annotated[int, Field(gt=0)] = 600


class RetentionSettings(ContractModel):
    """Define lifecycle periods for stored records."""

    expired_session_days: Annotated[int, Field(ge=0)] = 30
    temporary_upload_hours: Annotated[int, Field(gt=0)] = 1
    orphan_attachment_hours: Annotated[int, Field(gt=0)] = 24
    deleted_message_days: Annotated[int, Field(ge=0)] = 30
    deleted_attachment_days: Annotated[int, Field(ge=0)] = 30
    operational_log_days: Annotated[int, Field(gt=0)] = 30
    audit_event_days: Annotated[int, Field(gt=0)] | None = None
    export_file_hours: Annotated[int, Field(gt=0)] = 24

    @model_validator(mode="after")
    def validate_retention_order(self) -> "RetentionSettings":
        """Ensure temporary uploads expire before orphan cleanup."""
        if self.temporary_upload_hours >= self.orphan_attachment_hours:
            raise ValueError(
                "temporary_upload_hours must be less than orphan_attachment_hours"
            )
        return self


class LoggingSettings(ContractModel):
    """Define structured logging and rotation."""

    level: LogLevel = LogLevel.INFO
    directory: Path = Path("logs/server").resolve()
    json_format: bool = True
    console_enabled: bool = True
    maximum_file_bytes: Annotated[int, Field(gt=0)] = 10_485_760
    retained_files: Annotated[int, Field(gt=0)] = 10
    compress_rotated_files: bool = True
    redact_sensitive_values: bool = True


class MonitoringSettings(ContractModel):
    """Define health, metrics, and alert thresholds."""

    health_check_interval_seconds: Annotated[int, Field(gt=0)] = 30
    metrics_collection_interval_seconds: Annotated[int, Field(gt=0)] = 30
    storage_warning_percentage: Annotated[float, Field(ge=0, le=100)] = 80
    storage_critical_percentage: Annotated[float, Field(ge=0, le=100)] = 90
    database_latency_warning_ms: Annotated[float, Field(gt=0)] = 100
    redis_latency_warning_ms: Annotated[float, Field(gt=0)] = 50
    repeated_failure_alert_threshold: Annotated[int, Field(gt=0)] = 3

    @model_validator(mode="after")
    def validate_threshold_order(self) -> "MonitoringSettings":
        """Require critical storage usage to exceed warning usage."""
        if self.storage_warning_percentage >= self.storage_critical_percentage:
            raise ValueError("storage warning percentage must be below critical")
        return self


class WorkerSettings(ContractModel):
    """Define recurring background worker schedules."""

    session_cleanup_interval_seconds: Annotated[int, Field(ge=10)] = 3600
    attachment_cleanup_interval_seconds: Annotated[int, Field(ge=10)] = 3600
    audit_recent_check_interval_seconds: Annotated[int, Field(ge=10)] = 300
    audit_full_check_interval_seconds: Annotated[int, Field(ge=10)] = 86_400
    directory_sync_interval_seconds: Annotated[int, Field(ge=10)] = 3600
    statistics_interval_seconds: Annotated[int, Field(ge=10)] = 60


class FeatureFlagSettings(ContractModel):
    """Define fixed server-controlled optional feature availability."""

    message_editing: bool = True
    read_receipts: bool = True
    typing_indicators: bool = True
    attachment_uploads: bool = True
    image_thumbnails: bool = True
    local_search: bool = True
    announcements: bool = True
    audit_exports: bool = True
    multi_device_sessions: bool = False


class ProtocolSettings(ContractModel):
    """Define supported application protocol versions."""

    current_version: Annotated[int, Field(gt=0)] = 1
    minimum_supported_version: Annotated[int, Field(gt=0)] = 1
    supported_versions: list[int] = Field(default_factory=lambda: [1])
    deprecated_versions: list[int] = Field(default_factory=list)
    minimum_client_version: str = "0.1.0"

    @model_validator(mode="after")
    def validate_versions(self) -> "ProtocolSettings":
        """Require unique and internally consistent protocol versions."""
        supported = self.supported_versions
        if (
            not supported
            or len(supported) != len(set(supported))
            or any(value <= 0 for value in supported)
        ):
            raise ValueError("supported_versions must contain unique positive versions")
        if (
            self.current_version not in supported
            or self.minimum_supported_version not in supported
        ):
            raise ValueError("current and minimum protocol versions must be supported")
        if self.current_version != max(supported):
            raise ValueError("current_version must be the highest supported version")
        if not set(self.deprecated_versions).issubset(supported):
            raise ValueError("deprecated_versions must be supported")
        return self


class ServerSettings(BaseSettings):
    """Define and validate every installation-wide server setting."""

    model_config = SettingsConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    application: ApplicationSettings = Field(default_factory=ApplicationSettings)
    network: NetworkSettings = Field(default_factory=NetworkSettings)
    tls: TLSSettings = Field(default_factory=TLSSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    directory: DirectorySettings = Field(default_factory=DirectorySettings)
    authentication: AuthenticationSettings = Field(
        default_factory=AuthenticationSettings
    )
    tokens: TokenSettings = Field(default_factory=TokenSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    messaging: MessagingSettings = Field(default_factory=MessagingSettings)
    attachments: AttachmentSettings = Field(default_factory=AttachmentSettings)
    rate_limits: RateLimitSettings = Field(default_factory=RateLimitSettings)
    retention: RetentionSettings = Field(default_factory=RetentionSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    workers: WorkerSettings = Field(default_factory=WorkerSettings)
    features: FeatureFlagSettings = Field(default_factory=FeatureFlagSettings)
    protocol: ProtocolSettings = Field(default_factory=ProtocolSettings)

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
