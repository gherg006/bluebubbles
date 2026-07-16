"""Safe projection of server settings into existing shared capability contracts."""

from bluebubbles.server.configuration.settings import ServerSettings
from bluebubbles.shared.models.health import (
    CapabilityState,
    ClientVisibleLimits,
    ClientVisiblePolicies,
    ServerCapabilities,
)
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    HashAlgorithm,
    KeyEnvelopeAlgorithm,
    SignatureAlgorithm,
)


def build_server_capabilities(settings: ServerSettings) -> ServerCapabilities:
    """Expose only protocol, feature, limit, and policy values clients require."""
    features = settings.features.model_dump()
    return ServerCapabilities(
        application_version=settings.application.version,
        protocol_versions=tuple(settings.protocol.supported_versions),
        capabilities={
            name: (
                CapabilityState.AVAILABLE if enabled else CapabilityState.UNAVAILABLE
            )
            for name, enabled in features.items()
        },
        algorithms=(
            ContentEncryptionAlgorithm.AES_256_GCM_V1.value,
            KeyEnvelopeAlgorithm.X25519_HKDF_SHA256_AES_256_GCM_V1.value,
            SignatureAlgorithm.ED25519_V1.value,
            HashAlgorithm.SHA256_V1.value,
        ),
        limits=ClientVisibleLimits(
            maximum_message_bytes=settings.messaging.maximum_encrypted_request_bytes,
            maximum_attachment_bytes=settings.attachments.maximum_plaintext_size_bytes,
            maximum_group_members=settings.messaging.maximum_group_members,
            maximum_page_size=settings.messaging.maximum_page_size,
        ),
        policies=ClientVisiblePolicies(
            message_edit_window_seconds=settings.messaging.edit_window_seconds,
            message_delete_window_seconds=settings.messaging.edit_window_seconds,
            session_idle_timeout_seconds=settings.tokens.access_token_lifetime_seconds,
        ),
    )
