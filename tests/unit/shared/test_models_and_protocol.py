"""Compatibility tests spanning API models and WebSocket protocol contracts."""

import base64
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import SecretStr, ValidationError

from bluebubbles.shared.models.administration import (
    AdminDashboardResponse,
    AdminUserSummary,
    AuditEventResponse,
    AuditPageResponse,
    ConfigurationSummary,
    DataExportJobResponse,
    JobState,
    SecurityAlertResponse,
    WorkerStatusResponse,
)
from bluebubbles.shared.models.announcements import (
    AnnouncementPriority,
    AnnouncementResponse,
    AnnouncementTargetType,
    CreateAnnouncementRequest,
)
from bluebubbles.shared.models.attachments import (
    AttachmentRecipientKeyRequest,
    AttachmentStatus,
    InitialiseUploadRequest,
)
from bluebubbles.shared.models.contacts import (
    AddContactRequest,
    BlockContactRequest,
    ContactListResponse,
    ContactSummary,
    UpdateContactRequest,
)
from bluebubbles.shared.models.conversations import (
    ChangeGroupRoleRequest,
    CreateGroupConversationRequest,
    GroupRole,
)
from bluebubbles.shared.models.health import (
    CapabilityState,
    ClientVisibleLimits,
    ClientVisiblePolicies,
    ServerCapabilities,
)
from bluebubbles.shared.models.messages import (
    MessageType,
    RecipientKeyEnvelopeRequest,
    SendMessageRequest,
)
from bluebubbles.shared.models.sessions import LoginRequest
from bluebubbles.shared.protocol.envelope import WebSocketEventEnvelope
from bluebubbles.shared.protocol.event_types import WebSocketEventType
from bluebubbles.shared.protocol.events import (
    AnnouncementPublishedEventData,
    HeartbeatEventData,
    validate_event_data,
)
from bluebubbles.shared.protocol.negotiation import (
    ProtocolNegotiationRequest,
    ProtocolNegotiationResponse,
    negotiate_protocol,
)
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    HashAlgorithm,
    KeyEnvelopeAlgorithm,
    SignatureAlgorithm,
)
from bluebubbles.shared.types import AttachmentId, ConversationId, MessageId, UserId


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode()


def test_login_secrets_are_redacted() -> None:
    request = LoginRequest(
        username="user", password=SecretStr("secret"), device_name="Office PC"
    )
    assert isinstance(request.password, SecretStr)
    assert "secret" not in repr(request)


def test_required_administration_contact_and_identifier_contracts_are_importable() -> (
    None
):
    """Guard the public model catalogue against missing required definitions."""
    required_models = (
        AdminDashboardResponse,
        AdminUserSummary,
        AuditEventResponse,
        AuditPageResponse,
        ConfigurationSummary,
        DataExportJobResponse,
        SecurityAlertResponse,
        WorkerStatusResponse,
        AddContactRequest,
        BlockContactRequest,
        ContactListResponse,
        ContactSummary,
        UpdateContactRequest,
    )
    assert all(model.model_fields is not None for model in required_models)
    identifier = uuid4()
    assert UserId(identifier) == identifier
    assert (
        ConversationId(identifier) == MessageId(identifier) == AttachmentId(identifier)
    )
    assert JobState.RUNNING.value == "running"


def test_group_requests_reject_duplicate_members_and_owner_role_assignment() -> None:
    member = uuid4()
    with pytest.raises(ValidationError, match="unique"):
        CreateGroupConversationRequest(name="Team", member_ids=(member, member))
    with pytest.raises(ValidationError, match="TransferOwnershipRequest"):
        ChangeGroupRoleRequest(user_id=member, role=GroupRole.OWNER)


def test_encrypted_message_request_contains_no_plaintext_field() -> None:
    recipient = RecipientKeyEnvelopeRequest(
        recipient_id=uuid4(),
        key_version=1,
        algorithm=KeyEnvelopeAlgorithm.X25519_HKDF_SHA256_AES_256_GCM_V1,
        ephemeral_public_key=_b64(b"p" * 32),
        nonce=_b64(b"n" * 12),
        encrypted_key=_b64(b"key"),
    )
    request = SendMessageRequest(
        client_message_id=uuid4(),
        conversation_id=uuid4(),
        message_type=MessageType.TEXT,
        content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
        ciphertext=_b64(b"ciphertext"),
        nonce=_b64(b"n" * 12),
        signature_algorithm=SignatureAlgorithm.ED25519_V1,
        signature=_b64(b"s" * 64),
        sender_key_version=1,
        encrypted_keys=(recipient,),
    )
    assert "plaintext" not in SendMessageRequest.model_fields
    assert request.encrypted_keys[0].recipient_id == recipient.recipient_id
    with pytest.raises(ValidationError, match="unique"):
        SendMessageRequest.model_validate(
            {**request.model_dump(), "encrypted_keys": [recipient, recipient]}
        )


def test_attachment_initialisation_validates_display_filename() -> None:
    recipient = AttachmentRecipientKeyRequest(
        recipient_id=uuid4(), key_version=1, encrypted_key=_b64(b"key")
    )
    request = InitialiseUploadRequest(
        conversation_id=uuid4(),
        filename="report.pdf",
        media_type="application/pdf",
        encrypted_size=12,
        original_size=10,
        chunk_size=12,
        content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
        hash_algorithm=HashAlgorithm.SHA256_V1,
        encrypted_checksum=_b64(b"checksum"),
        recipient_keys=(recipient,),
    )
    assert request.filename == "report.pdf"
    assert AttachmentStatus.COMPLETE.value == "complete"
    with pytest.raises(ValidationError):
        request.model_copy(update={"filename": "../report.pdf"}).model_validate(
            {**request.model_dump(), "filename": "../report.pdf"}
        )


def test_announcement_plain_text_and_capabilities_are_validated() -> None:
    announcement = CreateAnnouncementRequest(
        title="Maintenance",
        body="Tonight at 18:00",
        priority=AnnouncementPriority.IMPORTANT,
        target_type=AnnouncementTargetType.ALL_USERS,
    )
    assert announcement.body == "Tonight at 18:00"
    with pytest.raises(ValidationError, match="control"):
        CreateAnnouncementRequest(
            title="Bad\x00title",
            body="body",
            target_type=AnnouncementTargetType.ALL_USERS,
        )
    capabilities = ServerCapabilities(
        application_version="0.1.0",
        protocol_versions=(1,),
        capabilities={"messaging": CapabilityState.AVAILABLE},
        algorithms=(ContentEncryptionAlgorithm.AES_256_GCM_V1,),
        limits=ClientVisibleLimits(
            maximum_message_bytes=100,
            maximum_attachment_bytes=1000,
            maximum_group_members=250,
            maximum_page_size=250,
        ),
        policies=ClientVisiblePolicies(
            message_edit_window_seconds=300,
            message_delete_window_seconds=300,
            session_idle_timeout_seconds=3600,
        ),
    )
    assert capabilities.protocol_versions == (1,)


def test_protocol_negotiation_is_server_authoritative() -> None:
    request = ProtocolNegotiationRequest(
        client_version="0.1.0", supported_protocols=(1, 2)
    )
    response = negotiate_protocol(
        request,
        server_protocols=(1,),
        server_version="0.1.0",
        minimum_client_version="0.1.0",
    )
    assert response.selected_protocol == 1
    rejected = negotiate_protocol(
        request,
        server_protocols=(3,),
        server_version="0.1.0",
        minimum_client_version="0.1.0",
    )
    assert not rejected.accepted and rejected.reason
    with pytest.raises(ValidationError, match="selected protocol"):
        ProtocolNegotiationResponse(
            accepted=True,
            selected_protocol=None,
            server_version="0.1.0",
            minimum_client_version="0.1.0",
        )


def test_websocket_envelope_and_registered_event_data_are_compatible() -> None:
    timestamp = datetime.now(UTC)
    event = WebSocketEventEnvelope(
        event_id=uuid4(),
        event_type=WebSocketEventType.HEARTBEAT,
        protocol_version=1,
        timestamp=timestamp,
        data={"sent_at": timestamp.isoformat()},
    )
    parsed = validate_event_data(event.event_type, event.data)
    assert isinstance(parsed, HeartbeatEventData)
    assert parsed.sent_at == timestamp
    with pytest.raises(ValueError, match="No data model"):
        validate_event_data("UNKNOWN", {})


def test_announcement_event_data_uses_the_api_contract() -> None:
    now = datetime.now(UTC)
    announcement = AnnouncementResponse(
        id=uuid4(),
        author_id=uuid4(),
        title="Notice",
        body="Message",
        priority=AnnouncementPriority.NORMAL,
        target_type=AnnouncementTargetType.ALL_USERS,
        published_at=now,
        expires_at=now + timedelta(days=1),
    )
    parsed = validate_event_data(
        WebSocketEventType.ANNOUNCEMENT_PUBLISHED,
        {"announcement": announcement.model_dump()},
    )
    assert isinstance(parsed, AnnouncementPublishedEventData)
    assert parsed.announcement.id == announcement.id
