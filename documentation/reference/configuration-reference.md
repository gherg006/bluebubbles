# Configuration reference

Generated from the strict Pydantic settings models. Unknown keys fail. Secret defaults are redacted. Environment variables use `__` between nested names.

## Server

| Setting | Type | Default | Constraints |
|---|---|---|---|
| `application.name` | `str` | `"BlueBubbles"` | - |
| `application.environment` | `EnvironmentName` | `"development"` | - |
| `application.version` | `str` | `"0.1.0"` | - |
| `application.debug` | `bool` | `false` | - |
| `application.timezone` | `str` | `"UTC"` | - |
| `application.instance_id` | `UUID` | `"00000000-0000-0000-0000-000000000000"` | - |
| `network.host` | `str` | `"127.0.0.1"` | - |
| `network.port` | `int` | `8443` | Ge(ge=1), Le(le=65535) |
| `network.trusted_proxy_count` | `int` | `0` | Ge(ge=0) |
| `network.request_timeout_seconds` | `int` | `30` | Gt(gt=0) |
| `network.maximum_request_body_bytes` | `int` | `10485760` | Gt(gt=0) |
| `network.websocket_auth_timeout_seconds` | `int` | `10` | Gt(gt=0) |
| `network.websocket_heartbeat_seconds` | `int` | `30` | Gt(gt=0) |
| `network.websocket_missed_heartbeat_limit` | `int` | `3` | Gt(gt=0) |
| `tls.enabled` | `bool` | `false` | - |
| `tls.certificate_path` | `pathlib._local.Path \| None` | `null` | - |
| `tls.private_key_path` | `pathlib._local.Path \| None` | `null` | - |
| `tls.certificate_chain_path` | `pathlib._local.Path \| None` | `null` | - |
| `tls.minimum_tls_version` | `str` | `"1.2"` | - |
| `database.url` | `SecretStr` | `<redacted>` | - |
| `database.pool_size` | `int` | `10` | Gt(gt=0) |
| `database.maximum_overflow` | `int` | `10` | Ge(ge=0) |
| `database.connection_timeout_seconds` | `int` | `10` | Gt(gt=0) |
| `database.statement_timeout_seconds` | `int` | `30` | Gt(gt=0) |
| `database.pool_recycle_seconds` | `int` | `1800` | Gt(gt=0) |
| `database.echo_sql` | `bool` | `false` | - |
| `redis.url` | `SecretStr` | `<redacted>` | - |
| `redis.namespace` | `str` | `"bluebubbles"` | MinLen(min_length=1) |
| `redis.connection_timeout_seconds` | `int` | `5` | Gt(gt=0) |
| `redis.operation_timeout_seconds` | `int` | `5` | Gt(gt=0) |
| `redis.maximum_connections` | `int` | `20` | Gt(gt=0) |
| `redis.fallback_enabled` | `bool` | `true` | - |
| `directory.provider` | `DirectoryProviderName` | `"disabled"` | - |
| `directory.server` | `str \| None` | `null` | - |
| `directory.port` | `Optional` | `null` | - |
| `directory.use_tls` | `bool` | `true` | - |
| `directory.bind_dn` | `str \| None` | `null` | - |
| `directory.bind_password` | `pydantic.types.SecretStr \| None` | `null` | - |
| `directory.base_dn` | `str \| None` | `null` | - |
| `directory.user_search_base` | `str \| None` | `null` | - |
| `directory.group_search_base` | `str \| None` | `null` | - |
| `directory.username_attribute` | `str` | `"sAMAccountName"` | - |
| `directory.guid_attribute` | `str` | `"objectGUID"` | - |
| `directory.email_attribute` | `str` | `"mail"` | - |
| `directory.department_attribute` | `str` | `"department"` | - |
| `directory.job_title_attribute` | `str` | `"title"` | - |
| `directory.group_membership_attribute` | `str` | `"memberOf"` | - |
| `directory.connection_timeout_seconds` | `int` | `10` | Gt(gt=0) |
| `directory.search_timeout_seconds` | `int` | `10` | Gt(gt=0) |
| `authentication.provider` | `AuthenticationProviderName` | `"local"` | - |
| `authentication.allow_local_accounts` | `bool` | `true` | - |
| `authentication.failed_login_limit` | `int` | `5` | Gt(gt=0) |
| `authentication.failed_login_window_seconds` | `int` | `900` | Gt(gt=0) |
| `authentication.application_lockout_seconds` | `int` | `900` | Gt(gt=0) |
| `authentication.directory_sync_interval_seconds` | `int` | `3600` | Gt(gt=0) |
| `authentication.default_role` | `str` | `"Employee"` | - |
| `authentication.directory_group_role_mapping` | `dict` | `{}` | - |
| `authentication.username_domain_prefix` | `str \| None` | `null` | - |
| `authentication.username_upn_suffix` | `str \| None` | `null` | - |
| `authentication.one_primary_crypto_device` | `bool` | `true` | - |
| `tokens.signing_algorithm` | `str` | `"HS256"` | - |
| `tokens.signing_secret` | `SecretStr` | `<redacted>` | - |
| `tokens.issuer` | `str` | `"bluebubbles"` | - |
| `tokens.audience` | `str` | `"bluebubbles-client"` | - |
| `tokens.access_token_lifetime_seconds` | `int` | `900` | Gt(gt=0) |
| `tokens.refresh_token_lifetime_seconds` | `int` | `604800` | Gt(gt=0) |
| `tokens.rotation_enabled` | `bool` | `true` | - |
| `tokens.reuse_detection_enabled` | `bool` | `true` | - |
| `storage.root_path` | `Path` | `C:\NEA\bluebubbles\data\attachments` | - |
| `storage.temporary_path` | `Path` | `C:\NEA\bluebubbles\data\temporary` | - |
| `storage.export_path` | `Path` | `C:\NEA\bluebubbles\data\exports` | - |
| `storage.reserved_free_bytes` | `int` | `1073741824` | Ge(ge=0) |
| `storage.reserved_free_percentage` | `float` | `5.0` | Ge(ge=0), Le(le=100) |
| `storage.create_missing_directories` | `bool` | `true` | - |
| `storage.allow_network_filesystem` | `bool` | `false` | - |
| `messaging.client_plaintext_character_limit` | `int` | `8000` | Ge(ge=1), Le(le=50000) |
| `messaging.maximum_encrypted_request_bytes` | `int` | `1048576` | Gt(gt=0) |
| `messaging.default_page_size` | `int` | `50` | Gt(gt=0) |
| `messaging.maximum_page_size` | `int` | `100` | Gt(gt=0) |
| `messaging.edit_window_seconds` | `int` | `900` | Ge(ge=0) |
| `messaging.direct_conversation_unique` | `bool` | `true` | - |
| `messaging.read_receipts_enabled` | `bool` | `true` | - |
| `messaging.typing_indicators_enabled` | `bool` | `true` | - |
| `messaging.maximum_group_members` | `int` | `100` | Gt(gt=1) |
| `attachments.maximum_plaintext_size_bytes` | `int` | `2147483648` | Gt(gt=0) |
| `attachments.default_chunk_size_bytes` | `int` | `1048576` | Gt(gt=0) |
| `attachments.minimum_chunk_size_bytes` | `int` | `262144` | Gt(gt=0) |
| `attachments.maximum_chunk_size_bytes` | `int` | `8388608` | Gt(gt=0) |
| `attachments.upload_session_lifetime_seconds` | `int` | `86400` | Gt(gt=0) |
| `attachments.orphan_lifetime_seconds` | `int` | `86400` | Gt(gt=0) |
| `attachments.maximum_concurrent_uploads_per_user` | `int` | `3` | Gt(gt=0) |
| `attachments.maximum_concurrent_downloads_per_user` | `int` | `3` | Gt(gt=0) |
| `attachments.chunk_retry_limit` | `int` | `3` | Ge(ge=0), Le(le=20) |
| `attachments.blocked_extensions` | `set` | `[".bat", ".exe", ".msi"]` | - |
| `attachments.thumbnail_maximum_bytes` | `int` | `524288` | Gt(gt=0) |
| `rate_limits.login_requests_per_window` | `int` | `10` | Gt(gt=0) |
| `rate_limits.login_window_seconds` | `int` | `60` | Gt(gt=0) |
| `rate_limits.message_requests_per_minute` | `int` | `120` | Gt(gt=0) |
| `rate_limits.search_requests_per_minute` | `int` | `60` | Gt(gt=0) |
| `rate_limits.administration_requests_per_minute` | `int` | `60` | Gt(gt=0) |
| `rate_limits.upload_chunk_requests_per_minute` | `int` | `600` | Gt(gt=0) |
| `rate_limits.websocket_events_per_minute` | `int` | `600` | Gt(gt=0) |
| `retention.expired_session_days` | `int` | `30` | Ge(ge=0) |
| `retention.temporary_upload_hours` | `int` | `1` | Gt(gt=0) |
| `retention.orphan_attachment_hours` | `int` | `24` | Gt(gt=0) |
| `retention.deleted_message_days` | `int` | `30` | Ge(ge=0) |
| `retention.deleted_attachment_days` | `int` | `30` | Ge(ge=0) |
| `retention.operational_log_days` | `int` | `30` | Gt(gt=0) |
| `retention.audit_event_days` | `Optional` | `null` | - |
| `retention.export_file_hours` | `int` | `24` | Gt(gt=0) |
| `logging.level` | `LogLevel` | `"INFO"` | - |
| `logging.directory` | `Path` | `C:\NEA\bluebubbles\logs\server` | - |
| `logging.json_format` | `bool` | `true` | - |
| `logging.console_enabled` | `bool` | `true` | - |
| `logging.maximum_file_bytes` | `int` | `10485760` | Gt(gt=0) |
| `logging.retained_files` | `int` | `10` | Gt(gt=0) |
| `logging.compress_rotated_files` | `bool` | `true` | - |
| `logging.redact_sensitive_values` | `bool` | `true` | - |
| `monitoring.health_check_interval_seconds` | `int` | `30` | Gt(gt=0) |
| `monitoring.metrics_collection_interval_seconds` | `int` | `30` | Gt(gt=0) |
| `monitoring.storage_warning_percentage` | `float` | `80` | Ge(ge=0), Le(le=100) |
| `monitoring.storage_critical_percentage` | `float` | `90` | Ge(ge=0), Le(le=100) |
| `monitoring.database_latency_warning_ms` | `float` | `100` | Gt(gt=0) |
| `monitoring.redis_latency_warning_ms` | `float` | `50` | Gt(gt=0) |
| `monitoring.repeated_failure_alert_threshold` | `int` | `3` | Gt(gt=0) |
| `monitoring.backup_status_path` | `pathlib._local.Path \| None` | `null` | - |
| `monitoring.backup_maximum_age_hours` | `int` | `24` | Gt(gt=0) |
| `workers.session_cleanup_interval_seconds` | `int` | `3600` | Ge(ge=10) |
| `workers.attachment_cleanup_interval_seconds` | `int` | `3600` | Ge(ge=10) |
| `workers.audit_recent_check_interval_seconds` | `int` | `300` | Ge(ge=10) |
| `workers.audit_full_check_interval_seconds` | `int` | `86400` | Ge(ge=10) |
| `workers.directory_sync_interval_seconds` | `int` | `3600` | Ge(ge=10) |
| `workers.statistics_interval_seconds` | `int` | `60` | Ge(ge=10) |
| `workers.outbox_interval_seconds` | `float` | `1.0` | Gt(gt=0) |
| `workers.outbox_batch_size` | `int` | `100` | Ge(ge=1), Le(le=1000) |
| `workers.outbox_retry_base_seconds` | `int` | `2` | Ge(ge=1) |
| `workers.outbox_retry_maximum_seconds` | `int` | `30` | Ge(ge=1) |
| `workers.outbox_lock_timeout_seconds` | `int` | `60` | Ge(ge=1) |
| `features.message_editing` | `bool` | `true` | - |
| `features.read_receipts` | `bool` | `true` | - |
| `features.typing_indicators` | `bool` | `true` | - |
| `features.attachment_uploads` | `bool` | `true` | - |
| `features.image_thumbnails` | `bool` | `true` | - |
| `features.local_search` | `bool` | `true` | - |
| `features.announcements` | `bool` | `true` | - |
| `features.audit_exports` | `bool` | `true` | - |
| `features.multi_device_sessions` | `bool` | `false` | - |
| `protocol.current_version` | `int` | `1` | Gt(gt=0) |
| `protocol.minimum_supported_version` | `int` | `1` | Gt(gt=0) |
| `protocol.supported_versions` | `list` | `[1]` | - |
| `protocol.deprecated_versions` | `list` | `[]` | - |
| `protocol.minimum_client_version` | `str` | `"0.1.0"` | - |

## Windows client

| Setting | Type | Default | Constraints |
|---|---|---|---|
| `application.name` | `str` | `"BlueBubbles"` | - |
| `application.version` | `str` | `"0.1.0"` | - |
| `application.environment` | `str` | `"production"` | - |
| `application.default_theme` | `str` | `"system"` | - |
| `application.reduced_motion` | `bool` | `false` | - |
| `server.base_url` | `AnyHttpUrl` | `"https://192.168.0.210:8443/"` | - |
| `server.websocket_url` | `AnyUrl` | `"wss://192.168.0.210:8443/api/v1/ws"` | - |
| `server.connect_timeout_seconds` | `float` | `10.0` | Gt(gt=0), Le(le=120) |
| `server.request_timeout_seconds` | `float` | `30.0` | Gt(gt=0), Le(le=300) |
| `server.retry_limit` | `int` | `3` | Ge(ge=0), Le(le=20) |
| `server.automatic_reconnect` | `bool` | `true` | - |
| `tls.verify_certificates` | `bool` | `true` | - |
| `tls.trusted_ca_path` | `pathlib._local.Path \| None` | `null` | - |
| `tls.expected_hostname` | `str \| None` | `null` | - |
| `tls.allow_certificate_pinning` | `bool` | `true` | - |
| `tls.pinned_certificate_fingerprint` | `str \| None` | `null` | - |
| `network.retry_base_delay_seconds` | `float` | `0.5` | Gt(gt=0), Le(le=60) |
| `network.retry_maximum_delay_seconds` | `float` | `30.0` | Gt(gt=0), Le(le=300) |
| `network.websocket_heartbeat_seconds` | `int` | `30` | Gt(gt=0) |
| `storage.profile_root` | `Path` | `C:\Users\zakma\AppData\Local\BlueBubbles\profiles` | - |
| `storage.default_cache_limit_bytes` | `int` | `2147483648` | Gt(gt=0) |
| `storage.maximum_cache_limit_bytes` | `int` | `5368709120` | Gt(gt=0) |
| `storage.thumbnail_cache_limit_bytes` | `int` | `268435456` | Ge(ge=0) |
| `storage.attachment_cache_limit_bytes` | `int` | `1610612736` | Ge(ge=0) |
| `storage.encrypted_message_cache_limit_bytes` | `int` | `268435456` | Ge(ge=0) |
| `storage.recent_messages_per_conversation` | `int` | `500` | Ge(ge=0), Le(le=100000) |
| `storage.cleanup_target_ratio` | `float` | `0.9` | Ge(ge=0.5), Lt(lt=1) |
| `storage.disk_warning_free_bytes` | `int` | `2147483648` | Gt(gt=0) |
| `storage.disk_critical_free_bytes` | `int` | `524288000` | Gt(gt=0) |
| `storage.local_database_backend` | `str` | `"sqlite"` | - |
| `storage.retain_cache_after_logout` | `bool` | `true` | - |
| `transfers.default_download_directory` | `Path` | `C:\Users\zakma\Downloads\BlueBubbles` | - |
| `transfers.upload_concurrency` | `int` | `2` | Gt(gt=0), Le(le=16) |
| `transfers.download_concurrency` | `int` | `3` | Gt(gt=0), Le(le=16) |
| `transfers.chunk_concurrency` | `int` | `2` | Gt(gt=0), Le(le=16) |
| `transfers.automatic_image_download_limit_bytes` | `int` | `10485760` | Ge(ge=0) |
| `transfers.default_upload_limit_bytes_per_second` | `Optional` | `null` | - |
| `transfers.default_download_limit_bytes_per_second` | `Optional` | `null` | - |
| `logging.level` | `str` | `"INFO"` | - |
| `logging.directory` | `Path` | `C:\Users\zakma\AppData\Local\BlueBubbles\logs` | - |
| `logging.json_format` | `bool` | `true` | - |
| `logging.console_enabled` | `bool` | `false` | - |
| `logging.maximum_file_bytes` | `int` | `10485760` | Gt(gt=0) |
| `logging.retained_files` | `int` | `5` | Gt(gt=0) |
| `logging.redact_sensitive_values` | `bool` | `true` | - |
| `features.local_search` | `bool` | `true` | - |
| `features.desktop_notifications` | `bool` | `true` | - |
| `features.certificate_pinning` | `bool` | `true` | - |
| `protocol.supported_versions` | `list` | `[1]` | - |

