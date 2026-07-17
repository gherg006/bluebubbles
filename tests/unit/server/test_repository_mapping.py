"""Task 06 repository value-object and pure-mapping tests."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from bluebubbles.server.database.models.attachments import UploadSessionORM
from bluebubbles.server.database.models.audit import AuditEventORM
from bluebubbles.server.database.models.conversations import (
    ConversationMemberORM,
    ConversationORM,
)
from bluebubbles.server.domain.attachments import (
    Attachment,
    AttachmentRecipientKey,
)
from bluebubbles.server.domain.audit import AuditSeverity
from bluebubbles.server.domain.conversations import Conversation, ConversationMember
from bluebubbles.server.domain.messages import Message, MessageRecipientKey
from bluebubbles.server.domain.sessions import Session
from bluebubbles.server.domain.users import User
from bluebubbles.server.repositories import (
    AuditQuery,
    ConversationListQuery,
    CursorPage,
    MessagePageQuery,
    StoredAttachmentChunk,
    UserSearchQuery,
)
from bluebubbles.server.repositories.interfaces import (
    AttachmentRepository,
    AuditRepository,
    ConversationRepository,
    MessageRepository,
    OutboxRepository,
    SessionRepository,
    UserRepository,
)
from bluebubbles.server.repositories.mapping.attachments import AttachmentMapper
from bluebubbles.server.repositories.mapping.audit import AuditMapper
from bluebubbles.server.repositories.mapping.conversations import ConversationMapper
from bluebubbles.server.repositories.mapping.messages import MessageMapper
from bluebubbles.server.repositories.mapping.sessions import SessionMapper
from bluebubbles.server.repositories.mapping.users import UserMapper
from bluebubbles.server.repositories.types import decode_cursor, encode_cursor
from bluebubbles.shared.constants import MAX_PAGE_SIZE
from bluebubbles.shared.models.attachments import AttachmentStatus
from bluebubbles.shared.models.conversations import ConversationType, GroupRole
from bluebubbles.shared.models.messages import MessageType
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    HashAlgorithm,
    KeyEnvelopeAlgorithm,
    SignatureAlgorithm,
)

NOW = datetime(2026, 7, 17, 12, tzinfo=UTC)


def test_repository_package_exports_contracts() -> None:
    """Repository imports expose every core protocol and query model."""
    assert all(
        item is not None
        for item in (
            AttachmentRepository,
            AuditRepository,
            ConversationRepository,
            MessageRepository,
            OutboxRepository,
            SessionRepository,
            UserRepository,
            AuditQuery,
            ConversationListQuery,
            MessagePageQuery,
            UserSearchQuery,
        )
    )
    page = CursorPage(items=(1, 2), next_cursor="next")
    assert page.items == (1, 2)


def test_repository_cursor_round_trip_and_validation() -> None:
    """Opaque cursors preserve scalar ordering values and reject corruption."""
    identifier = uuid4()
    cursor = encode_cursor(NOW, identifier, 4)
    assert decode_cursor(cursor, 3) == (NOW.isoformat(), str(identifier), 4)
    with pytest.raises(ValueError, match="Invalid repository cursor"):
        decode_cursor("not-json", 1)
    with pytest.raises(ValueError, match="Invalid repository cursor"):
        decode_cursor(encode_cursor(1, 2), 1)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: UserSearchQuery(limit=0),
        lambda: UserSearchQuery(limit=MAX_PAGE_SIZE + 1),
        lambda: ConversationListQuery(user_id=uuid4(), limit=0),
        lambda: MessagePageQuery(conversation_id=uuid4(), limit=0),
        lambda: AuditQuery(limit=0),
        lambda: AuditQuery(minimum_sequence=0),
        lambda: MessagePageQuery(
            conversation_id=uuid4(), membership_started_at=datetime(2026, 1, 1)
        ),
    ],
)
def test_repository_queries_reject_invalid_bounds(factory: object) -> None:
    """Every repository query enforces limits and aware timestamps."""
    with pytest.raises(ValueError):
        factory()  # type: ignore[operator]


def test_stored_attachment_chunk_requires_complete_safe_metadata() -> None:
    """Chunk records reject unsafe bounds, missing metadata, and naive time."""
    valid = StoredAttachmentChunk(
        id=uuid4(),
        attachment_id=uuid4(),
        index=0,
        encrypted_size=10,
        encrypted_checksum="checksum",
        nonce=b"nonce",
        authentication_tag=b"tag",
        storage_reference="opaque/ref",
        created_at=NOW,
    )
    assert valid.index == 0
    with pytest.raises(ValueError, match="cannot be negative"):
        StoredAttachmentChunk(
            id=valid.id,
            attachment_id=valid.attachment_id,
            index=-1,
            encrypted_size=valid.encrypted_size,
            encrypted_checksum=valid.encrypted_checksum,
            nonce=valid.nonce,
            authentication_tag=valid.authentication_tag,
            storage_reference=valid.storage_reference,
            created_at=valid.created_at,
        )


def test_user_mapper_round_trip_preserves_safe_domain_fields() -> None:
    """User mapping preserves identity while defaulting volatile presence."""
    user = User(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        username="Alice",
        display_name="Alice Smith",
        role_id=uuid4(),
        email="alice@example.test",
        active_directory_guid=uuid4(),
        is_enabled=True,
    )
    record = UserMapper.to_orm(user)
    mapped = UserMapper.to_domain(record)
    assert mapped.username == "alice"
    assert mapped.active_directory_guid == user.active_directory_guid
    assert mapped.display_name == user.display_name


def test_user_mapper_handles_local_users_and_optional_fields() -> None:
    """Local identities use explicit local persistence state."""
    user = User(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        username="local",
        display_name="Local",
        role_id=uuid4(),
    )
    record = UserMapper.to_orm(user)
    assert record.authentication_source == "local"
    assert record.directory_guid is None
    assert UserMapper.to_domain(record).active_directory_guid is None


def test_session_mapper_round_trip_never_stores_raw_token() -> None:
    """Session mapping converts the domain hash to binary persistence data."""
    session = Session(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        version=2,
        user_id=uuid4(),
        refresh_token_hash="ab" * 32,
        expires_at=NOW + timedelta(days=1),
        idle_expires_at=NOW + timedelta(hours=1),
        ip_address="127.0.0.1",
        device_name="Desktop",
        platform="1.0",
        login_time=NOW,
    )
    record = SessionMapper.to_orm(session)
    assert record.refresh_token_hash == bytes.fromhex(session.refresh_token_hash)
    mapped = SessionMapper.to_domain(record)
    assert mapped.refresh_token_hash == session.refresh_token_hash
    assert mapped.version == 2


def test_session_mapper_accepts_non_hex_one_way_hash_representation() -> None:
    """Legacy textual verifier hashes remain one-way binary values at rest."""
    session = Session(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        user_id=uuid4(),
        refresh_token_hash="$argon2id$hash",
        expires_at=NOW + timedelta(days=1),
        idle_expires_at=NOW + timedelta(hours=1),
        ip_address="127.0.0.1",
        device_name="Desktop",
        platform="1.0",
        login_time=NOW,
    )
    assert SessionMapper.to_orm(session).refresh_token_hash.startswith(b"$argon2id$")


def test_conversation_mapper_round_trip_includes_explicit_memberships() -> None:
    """Conversation mapping uses supplied rows without issuing hidden queries."""
    conversation_id = uuid4()
    member = ConversationMember(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        conversation_id=conversation_id,
        user_id=uuid4(),
        role=GroupRole.OWNER,
        joined_at=NOW,
    )
    conversation = Conversation(
        id=conversation_id,
        created_at=NOW,
        updated_at=NOW,
        conversation_type=ConversationType.GROUP,
        created_by=member.user_id,
        last_activity=NOW,
        title="Team",
        members={member.user_id: member},
    )
    record = ConversationMapper.to_orm(conversation)
    member_record = ConversationMapper.member_to_orm(member)
    mapped = ConversationMapper.to_domain(record, (member_record,))
    assert mapped.active_member(member.user_id) is not None
    assert mapped.title == "Team"


def test_conversation_mapper_handles_removed_members_and_null_activity() -> None:
    """Historical membership periods and legacy null activity map safely."""
    record = ConversationORM(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        deleted_at=None,
        version=1,
        conversation_type="direct",
        title=None,
        description=None,
        created_by=uuid4(),
        last_activity_at=None,
        is_archived_systemwide=False,
    )
    member = ConversationMemberORM(
        id=uuid4(),
        conversation_id=record.id,
        user_id=uuid4(),
        member_role="member",
        joined_at=NOW,
        removed_at=NOW + timedelta(minutes=1),
        last_read_message_id=None,
        last_read_at=None,
        is_muted=False,
        muted_until=None,
        is_pinned=False,
        is_archived=False,
        notification_level="all",
        membership_version=2,
    )
    mapped = ConversationMapper.to_domain(record, (member,))
    assert mapped.last_activity == NOW
    assert not next(iter(mapped.members.values())).active


def _message() -> Message:
    message_id = uuid4()
    key = MessageRecipientKey(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        message_id=message_id,
        recipient_id=uuid4(),
        key_version=1,
        algorithm=KeyEnvelopeAlgorithm.X25519_HKDF_SHA256_AES_256_GCM_V1,
        ephemeral_public_key=b"e" * 32,
        nonce=b"n" * 12,
        encrypted_key=b"encrypted-key",
    )
    return Message(
        id=message_id,
        created_at=NOW,
        updated_at=NOW,
        client_message_id=message_id,
        conversation_id=uuid4(),
        sender_id=uuid4(),
        message_type=MessageType.TEXT,
        content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
        ciphertext=b"ciphertext",
        nonce=b"n" * 12,
        signature_algorithm=SignatureAlgorithm.ED25519_V1,
        signature=b"s" * 64,
        sender_key_version=1,
        sent_at=NOW,
        recipient_keys=(key,),
    )


def test_message_mapper_round_trip_preserves_only_encrypted_values() -> None:
    """Message mapping reconstructs fixed algorithms and recipient envelopes."""
    message = _message()
    record = MessageMapper.to_orm(message)
    key_records = tuple(MessageMapper.key_to_orm(key) for key in message.recipient_keys)
    attachment_id = uuid4()
    mapped = MessageMapper.to_domain(record, key_records, (attachment_id,))
    assert mapped.ciphertext == b"ciphertext"
    assert mapped.recipient_keys[0].encrypted_key == b"encrypted-key"
    assert mapped.attachment_ids == (attachment_id,)


def test_message_mapper_rejects_incomplete_active_rows() -> None:
    """Corrupt active message rows cannot leak into the domain."""
    message = _message()
    record = MessageMapper.to_orm(message)
    record.signature = None
    with pytest.raises(ValueError, match="incomplete encrypted envelope"):
        MessageMapper.to_domain(record, ())
    record.signature = b"signature"
    record.signature_key_version = None
    with pytest.raises(ValueError, match="no signature key version"):
        MessageMapper.to_domain(record, ())


def _attachment() -> Attachment:
    attachment_id = uuid4()
    key = AttachmentRecipientKey(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        attachment_id=attachment_id,
        recipient_id=uuid4(),
        key_version=1,
        encrypted_key=b"encrypted-file-key",
        ephemeral_public_key=b"e" * 32,
    )
    return Attachment(
        id=attachment_id,
        created_at=NOW,
        updated_at=NOW,
        conversation_id=uuid4(),
        uploaded_by=uuid4(),
        filename="report.pdf",
        media_type="application/pdf",
        encrypted_size=101,
        original_size=80,
        content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
        hash_algorithm=HashAlgorithm.SHA256_V1,
        encrypted_checksum=b"checksum",
        storage_reference="opaque/ref",
        chunk_size=50,
        status=AttachmentStatus.INITIALISED,
        recipient_keys=(key,),
    )


def test_attachment_mapper_round_trip_preserves_binary_checksum() -> None:
    """Attachment mapping base64-encodes binary checksums at the schema boundary."""
    attachment = _attachment()
    record = AttachmentMapper.to_orm(attachment)
    keys = tuple(AttachmentMapper.key_to_orm(key) for key in attachment.recipient_keys)
    mapped = AttachmentMapper.to_domain(record, keys)
    assert mapped.encrypted_checksum == b"checksum"
    assert record.chunk_count == 3
    assert mapped.recipient_keys[0].ephemeral_public_key == b"e" * 32


def test_attachment_mapper_requires_persistence_metadata() -> None:
    """Persistence refuses missing chunk and key-envelope metadata."""
    attachment = _attachment()
    attachment.chunk_size = None
    with pytest.raises(ValueError, match="chunk size"):
        AttachmentMapper.to_orm(attachment)
    key = attachment.recipient_keys[0]
    key.ephemeral_public_key = b""
    with pytest.raises(ValueError, match="ephemeral public key"):
        AttachmentMapper.key_to_orm(key)


def test_upload_and_audit_mappers_preserve_state() -> None:
    """Upload recovery and immutable audit mapping preserve stored state."""
    upload = UploadSessionORM(
        id=uuid4(),
        attachment_id=uuid4(),
        user_id=uuid4(),
        conversation_id=uuid4(),
        expected_encrypted_size=100,
        expected_chunk_count=2,
        chunk_size=50,
        received_encrypted_size=50,
        status="uploading",
        expires_at=NOW + timedelta(hours=1),
        completed_at=None,
        created_at=NOW,
        updated_at=NOW,
    )
    assert AttachmentMapper.upload_to_domain(upload, {0: 50}).received_chunks == {0: 50}
    audit = AuditEventORM(
        sequence_number=1,
        id=uuid4(),
        category="authentication",
        action="login",
        severity="informational",
        actor_user_id=None,
        target_type=None,
        target_id=None,
        session_id=None,
        source_ip="127.0.0.1",
        result="success",
        details={"method": "local"},
        timestamp=NOW,
        correlation_id=uuid4(),
        previous_hash=None,
        entry_hash="a" * 64,
    )
    mapped = AuditMapper.to_domain(audit)
    assert mapped.severity is AuditSeverity.INFORMATIONAL
    assert mapped.details == {"method": "local"}
