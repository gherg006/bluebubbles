"""Unit tests for core Task 06 SQLAlchemy repository adapters."""

from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.attachments import (
    UploadSessionChunkORM,
    UploadSessionORM,
)
from bluebubbles.server.database.models.audit import AuditChainStateORM, AuditEventORM
from bluebubbles.server.database.models.outbox import OutboxEventORM
from bluebubbles.server.domain.attachments import (
    Attachment,
    AttachmentRecipientKey,
    UploadSession,
)
from bluebubbles.server.domain.audit import (
    AuditChainState,
    AuditEvent,
    AuditSeverity,
)
from bluebubbles.server.domain.conversations import Conversation, ConversationMember
from bluebubbles.server.domain.messages import (
    Message,
    MessageDelivery,
    MessageRecipientKey,
)
from bluebubbles.server.domain.outbox import OutboxEvent
from bluebubbles.server.repositories.mapping.attachments import AttachmentMapper
from bluebubbles.server.repositories.mapping.conversations import ConversationMapper
from bluebubbles.server.repositories.mapping.messages import MessageMapper
from bluebubbles.server.repositories.sqlalchemy import (
    SqlAlchemyAttachmentRepository,
    SqlAlchemyAuditRepository,
    SqlAlchemyConversationRepository,
    SqlAlchemyMessageRepository,
    SqlAlchemyOutboxRepository,
)
from bluebubbles.server.repositories.types import (
    AuditQuery,
    ConversationListQuery,
    MessagePageQuery,
    StoredAttachmentChunk,
)
from bluebubbles.shared.errors.exceptions import ConflictError, RepositoryError
from bluebubbles.shared.models.conversations import ConversationType, GroupRole
from bluebubbles.shared.models.messages import MessageDeliveryStatus, MessageType
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    HashAlgorithm,
    KeyEnvelopeAlgorithm,
    SignatureAlgorithm,
)
from tests.unit.server.test_repository_sqlalchemy_support import (
    FakeResult,
    FakeSession,
)

NOW = datetime(2026, 7, 17, 12, tzinfo=UTC)


def _session(fake: FakeSession) -> AsyncSession:
    return cast(AsyncSession, fake)


def _member(
    conversation_id: object,
    *,
    role: GroupRole = GroupRole.MEMBER,
    user_id: object | None = None,
) -> ConversationMember:
    return ConversationMember(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        conversation_id=conversation_id,  # type: ignore[arg-type]
        user_id=user_id or uuid4(),  # type: ignore[arg-type]
        role=role,
        joined_at=NOW,
    )


def _conversation(
    kind: ConversationType = ConversationType.GROUP,
) -> Conversation:
    conversation_id = uuid4()
    owner = _member(conversation_id, role=GroupRole.OWNER)
    second = _member(conversation_id)
    return Conversation(
        id=conversation_id,
        created_at=NOW,
        updated_at=NOW,
        conversation_type=kind,
        created_by=owner.user_id,
        last_activity=NOW,
        title="Team" if kind is ConversationType.GROUP else None,
        members={owner.user_id: owner, second.user_id: second},
    )


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
        encrypted_size=100,
        original_size=80,
        content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
        hash_algorithm=HashAlgorithm.SHA256_V1,
        encrypted_checksum=b"checksum",
        storage_reference="opaque/ref",
        chunk_size=50,
        recipient_keys=(key,),
    )


@pytest.mark.asyncio
async def test_conversation_repository_reads_and_lists_without_n_plus_one() -> None:
    """Conversation reads batch memberships and use deterministic cursors."""
    fake = FakeSession()
    conversation = _conversation()
    record = ConversationMapper.to_orm(conversation)
    member_records = [
        ConversationMapper.member_to_orm(member)
        for member in conversation.members.values()
    ]
    repository = SqlAlchemyConversationRepository(_session(fake))
    fake.execute_results = [FakeResult(record), FakeResult(), FakeResult(record)]
    fake.scalar_results = [member_records, member_records]
    assert await repository.get_by_id(conversation.id, for_update=True) == conversation
    assert await repository.get_by_id(uuid4()) is None
    assert (
        await repository.find_direct_pair(
            member_records[0].user_id, member_records[1].user_id
        )
        is not None
    )
    fake.execute_results = [FakeResult()]
    assert await repository.find_direct_pair(uuid4(), uuid4()) is None
    fake.scalar_results = [[record, record], member_records, [record], member_records]
    page = await repository.list_for_user(
        ConversationListQuery(user_id=member_records[0].user_id, limit=1)
    )
    assert page.next_cursor is not None
    final = await repository.list_for_user(
        ConversationListQuery(
            user_id=member_records[0].user_id,
            limit=1,
            cursor=page.next_cursor,
            include_archived=True,
        )
    )
    assert final.next_cursor is None


@pytest.mark.asyncio
async def test_conversation_repository_creation_and_membership_lifecycle() -> None:
    """Conversation creation enforces direct/group invariants and versioned writes."""
    fake = FakeSession()
    repository = SqlAlchemyConversationRepository(_session(fake))
    direct = _conversation(ConversationType.DIRECT)
    group = _conversation()
    assert await repository.create(direct) is direct
    assert await repository.create(group) is group
    assert await repository.create_direct(direct) is direct
    assert await repository.create_group(group) is group
    with pytest.raises(ValueError, match="direct conversation"):
        await repository.create_direct(group)
    with pytest.raises(ValueError, match="group conversation"):
        await repository.create_group(direct)
    direct.members.pop(next(iter(direct.members)))
    with pytest.raises(ValueError, match="exactly two"):
        await repository.create_direct(direct)
    group.members = {
        user_id: member
        for user_id, member in group.members.items()
        if member.role is not GroupRole.OWNER
    }
    with pytest.raises(ValueError, match="exactly one"):
        await repository.create_group(group)

    member = next(iter(_conversation().members.values()))
    fake.execute_results = [FakeResult(rowcount=1)]
    assert await repository.add_member(member) is member
    member_record = ConversationMapper.member_to_orm(member)
    fake.execute_results = [
        FakeResult(member_record),
        FakeResult(),
        FakeResult(member_record),
    ]
    assert await repository.get_membership(member.conversation_id, member.user_id)
    assert await repository.get_active_membership(uuid4(), uuid4()) is None
    assert await repository.get_active_membership(
        member.conversation_id, member.user_id, for_update=True
    )
    fake.scalar_results = [[member_record], [member_record]]
    assert len(await repository.get_active_members(member.conversation_id)) == 1
    assert (
        len(
            await repository.list_active_members(
                member.conversation_id, for_update=True
            )
        )
        == 1
    )
    fake.execute_results = [
        FakeResult(rowcount=1),
        FakeResult(rowcount=0),
        FakeResult(rowcount=1),
    ]
    assert await repository.remove_member(member.id, NOW, expected_version=1)
    assert not await repository.change_member_role(
        member.id, GroupRole.ADMIN, expected_version=1
    )
    assert await repository.update_last_activity(
        member.conversation_id, NOW, expected_version=1
    )


@pytest.mark.asyncio
async def test_message_repository_reads_pages_and_recipient_scope() -> None:
    """Message reads return complete encrypted envelopes with stable pages."""
    fake = FakeSession()
    message = _message()
    record = MessageMapper.to_orm(message)
    key_record = MessageMapper.key_to_orm(message.recipient_keys[0])
    repository = SqlAlchemyMessageRepository(_session(fake))
    fake.execute_results = [
        FakeResult(record),
        FakeResult(),
        FakeResult(record),
        FakeResult(record),
    ]
    fake.scalar_results = [
        [key_record],
        [],
        [key_record],
        [],
        [key_record],
        [],
    ]
    assert await repository.get_by_id(message.id, for_update=True) == message
    assert await repository.get_by_id(uuid4()) is None
    assert await repository.get_existing_idempotent_message(
        message.id, message.sender_id
    )
    assert await repository.get_for_user(message.id, key_record.recipient_user_id)
    fake.scalar_results = [
        [record, record],
        [key_record],
        [],
        [record],
        [key_record],
        [],
    ]
    page = await repository.list_for_conversation(
        MessagePageQuery(
            conversation_id=message.conversation_id,
            user_id=key_record.recipient_user_id,
            limit=1,
            membership_started_at=NOW,
        )
    )
    assert page.next_cursor is not None
    final = await repository.list_for_conversation(
        MessagePageQuery(
            conversation_id=message.conversation_id,
            limit=1,
            cursor=page.next_cursor,
            include_deleted=True,
        )
    )
    assert final.next_cursor is None


@pytest.mark.asyncio
async def test_message_repository_writes_versions_and_delivery_states() -> None:
    """Message writes preserve idempotency, prior versions, and delivery order."""
    fake = FakeSession()
    message = _message()
    record = MessageMapper.to_orm(message)
    repository = SqlAlchemyMessageRepository(_session(fake))
    assert await repository.create(message) is message
    message.client_message_id = uuid4()
    with pytest.raises(ValueError, match="idempotency"):
        await repository.create(message)
    message.client_message_id = message.id
    await repository.add_recipient_keys(list(message.recipient_keys))
    await repository.insert_recipient_keys(message.recipient_keys)
    key_record = MessageMapper.key_to_orm(message.recipient_keys[0])
    fake.execute_results = [FakeResult(key_record), FakeResult()]
    assert await repository.get_recipient_key(message.id, key_record.recipient_user_id)
    assert await repository.get_recipient_key(message.id, uuid4()) is None

    message.replace_envelope(
        ciphertext=b"new-ciphertext",
        nonce=b"x" * 12,
        signature=b"z" * 64,
        recipient_keys=message.recipient_keys,
        at=NOW + timedelta(minutes=1),
    )
    fake.execute_results = [
        FakeResult(record),
        FakeResult(rowcount=1),
        FakeResult(),
        FakeResult(record),
        FakeResult(rowcount=1),
        FakeResult(),
    ]
    assert await repository.update_payload(message, 1) is message
    assert (
        await repository.update_encrypted_payload(message, expected_version=1)
        is message
    )
    fake.execute_results = [FakeResult()]
    with pytest.raises(ConflictError, match="changed"):
        await repository.update_payload(message, 99)
    fake.execute_results = [FakeResult(rowcount=1)]
    assert await repository.soft_delete(message.id, NOW, expected_version=2)

    delivery = MessageDelivery(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        message_id=message.id,
        recipient_id=key_record.recipient_user_id,
        status=MessageDeliveryStatus.PENDING,
        status_at=NOW,
    )
    await repository.create_delivery_rows([delivery])
    fake.execute_results = [FakeResult(rowcount=1)]
    assert await repository.update_delivery_state(
        message.id,
        delivery.recipient_id,
        MessageDeliveryStatus.DELIVERED,
        NOW,
    )


@pytest.mark.asyncio
async def test_attachment_repository_complete_workflow() -> None:
    """Attachment metadata, upload recovery, chunks, keys, and links compose safely."""
    fake = FakeSession()
    attachment = _attachment()
    record = AttachmentMapper.to_orm(attachment)
    key_record = AttachmentMapper.key_to_orm(attachment.recipient_keys[0])
    repository = SqlAlchemyAttachmentRepository(_session(fake))
    assert await repository.create_pending(attachment) is attachment
    assert await repository.create_attachment(attachment) is attachment
    upload = UploadSession(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        attachment_id=attachment.id,
        uploader_id=attachment.uploaded_by,
        chunk_size=50,
        total_size=100,
        expires_at=NOW + timedelta(hours=1),
    )
    fake.get_results = [record]
    assert await repository.create_upload_session(upload) is upload
    fake.execute_results = [FakeResult(cast(UploadSessionORM, fake.added[-1]))]
    fake.scalar_results = [
        [
            UploadSessionChunkORM(
                upload_session_id=upload.id,
                chunk_index=0,
                encrypted_size=50,
                encrypted_checksum="sum",
                received_at=NOW,
            )
        ]
    ]
    recovered = await repository.get_upload_session(upload.id, for_update=True)
    assert recovered is not None and recovered.received_chunks == {0: 50}
    fake.execute_results = [FakeResult()]
    assert await repository.get_upload_session(uuid4()) is None

    fake.execute_results = [FakeResult(record), FakeResult(), FakeResult(record)]
    fake.scalar_results = [[key_record], [key_record]]
    assert await repository.get_by_id(attachment.id) is not None
    assert await repository.get_by_id(uuid4()) is None
    assert await repository.get_for_user(attachment.id, key_record.recipient_user_id)
    chunk = StoredAttachmentChunk(
        id=uuid4(),
        attachment_id=attachment.id,
        index=0,
        encrypted_size=50,
        encrypted_checksum="sum",
        nonce=b"nonce",
        authentication_tag=b"tag",
        storage_reference="opaque/chunk",
        created_at=NOW,
    )
    await repository.add_chunk(chunk)
    await repository.add_chunks([chunk])
    chunk_record = fake.added[-1]
    fake.scalar_results = [[chunk_record]]
    assert await repository.list_chunks(attachment.id) == [chunk]
    await repository.add_recipient_keys(list(attachment.recipient_keys))
    fake.execute_results = [FakeResult(key_record), FakeResult()]
    assert await repository.get_recipient_key(
        attachment.id, key_record.recipient_user_id
    )
    assert await repository.get_recipient_key(attachment.id, uuid4()) is None

    fake.execute_results = [
        FakeResult(rowcount=1),
        FakeResult(rowcount=1),
        FakeResult(rowcount=1),
        FakeResult(rowcount=0),
        FakeResult(rowcount=1),
    ]
    assert await repository.mark_complete(attachment.id, NOW, expected_version=1)
    await repository.link_to_message([attachment.id], uuid4())
    await repository.link_to_message([], uuid4())
    assert not await repository.mark_deleted(attachment.id, NOW, expected_version=2)
    assert await repository.mark_deleted(attachment.id, NOW, expected_version=2)
    fake.scalar_results = [[record]]
    fake.scalar_results.append([key_record])
    assert (
        len(await repository.list_expired_orphans(NOW + timedelta(days=1), limit=1))
        == 1
    )


@pytest.mark.asyncio
async def test_attachment_repository_validation_and_conflict_paths() -> None:
    """Attachment adapter rejects incomplete recovery and conflicting links."""
    fake = FakeSession()
    repository = SqlAlchemyAttachmentRepository(_session(fake))
    attachment = _attachment()
    upload = UploadSession(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        attachment_id=attachment.id,
        uploader_id=attachment.uploaded_by,
        chunk_size=50,
        total_size=100,
        expires_at=NOW + timedelta(hours=1),
        received_chunks={0: 50},
    )
    with pytest.raises(ValueError, match="unverified"):
        await repository.create_upload_session(upload)
    upload.received_chunks = {}
    fake.get_results = [None]
    with pytest.raises(ValueError, match="must exist"):
        await repository.create_upload_session(upload)
    with pytest.raises(ValueError, match="positive"):
        await repository.list_expired_orphans(NOW, limit=0)
    with pytest.raises(ValueError, match="unique"):
        await repository.link_to_message([attachment.id, attachment.id], uuid4())
    fake.execute_results = [FakeResult(rowcount=0), FakeResult(rowcount=0)]
    assert not await repository.mark_complete(attachment.id, NOW, expected_version=1)
    with pytest.raises(ConflictError, match="cannot be linked"):
        await repository.link_to_message([attachment.id], uuid4())


def _audit_event(previous_hash: str | None = None) -> AuditEvent:
    return AuditEvent(
        id=uuid4(),
        event_type="user.login",
        occurred_at=NOW,
        actor_id=uuid4(),
        source_address="127.0.0.1",
        severity=AuditSeverity.INFORMATIONAL,
        details={"result": "success"},
        previous_hash=previous_hash,
        event_hash="a" * 64,
    )


def _audit_record(event: AuditEvent, sequence: int = 1) -> AuditEventORM:
    return AuditEventORM(
        sequence_number=sequence,
        id=event.id,
        category="application",
        action=event.event_type,
        severity=event.severity.value,
        actor_user_id=event.actor_id,
        target_type=None,
        target_id=None,
        session_id=None,
        source_ip=event.source_address,
        result="success",
        details=dict(event.details),
        timestamp=event.occurred_at,
        correlation_id=event.id,
        previous_hash=event.previous_hash,
        entry_hash=event.event_hash,
    )


@pytest.mark.asyncio
async def test_audit_repository_lock_append_query_and_verify() -> None:
    """Audit adapter locks one chain head and exposes no update/delete event API."""
    fake = FakeSession()
    repository = SqlAlchemyAuditRepository(_session(fake))
    state_record = AuditChainStateORM(
        id=1, latest_sequence_number=0, latest_hash=None, updated_at=NOW
    )
    fake.execute_results = [FakeResult(state_record), FakeResult(state_record)]
    assert await repository.lock_chain_state() == AuditChainState(None, None, 0)
    assert await repository.get_latest_chain_state() == AuditChainState(None, None, 0)
    event = _audit_event()
    fake.execute_results = [
        FakeResult(state_record),
        FakeResult(rowcount=1),
    ]
    assert await repository.append(event) is event
    fake.execute_results = [FakeResult(rowcount=1)]
    await repository.update_chain_state(AuditChainState(event.id, event.event_hash, 1))
    record = _audit_record(event)
    fake.scalar_results = [[record, record], [record], [record], [record]]
    page = await repository.list_events(AuditQuery(limit=1))
    assert page.next_cursor is not None
    final = await repository.list_events(
        AuditQuery(
            limit=1,
            cursor=page.next_cursor,
            category="application",
            actor_user_id=event.actor_id,
        )
    )
    assert final.next_cursor is None
    fake.get_results = [record, None]
    assert await repository.get_by_sequence(1) == event
    assert await repository.get_by_sequence(2) is None
    assert await repository.list_range(1, 1) == [event]
    assert await repository.verify_range_data(1, 1) == [event]
    assert not hasattr(repository, "update_event")
    assert not hasattr(repository, "delete_event")


@pytest.mark.asyncio
async def test_audit_repository_failure_paths() -> None:
    """Missing chain state, invalid links, and invalid ranges fail safely."""
    fake = FakeSession()
    repository = SqlAlchemyAuditRepository(_session(fake))
    fake.execute_results = [FakeResult()]
    with pytest.raises(RepositoryError, match="missing"):
        await repository.lock_chain_state()
    state_record = AuditChainStateORM(
        id=1, latest_sequence_number=1, latest_hash="b" * 64, updated_at=NOW
    )
    fake.execute_results = [FakeResult(state_record)]
    fake.single_scalar_results = [uuid4()]
    state = await repository.lock_chain_state()
    assert state.event_count == 1
    fake.execute_results = [FakeResult(state_record)]
    fake.single_scalar_results = [uuid4()]
    with pytest.raises(ValueError, match="extend"):
        await repository.append(_audit_event())
    fake.execute_results = [FakeResult(rowcount=0)]
    with pytest.raises(ValueError, match="not initialized"):
        await repository.update_chain_state(state)
    with pytest.raises(ValueError, match="positive"):
        await repository.get_by_sequence(0)
    with pytest.raises(ValueError, match="range"):
        await repository.list_range(2, 1)


def _outbox() -> OutboxEvent:
    return OutboxEvent(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        event_type="message.stored",
        aggregate_type="message",
        aggregate_id=uuid4(),
        protocol_version=1,
        payload={"conversation_id": str(uuid4())},
        available_at=NOW,
    )


@pytest.mark.asyncio
async def test_outbox_repository_publication_lifecycle() -> None:
    """Outbox events are added, skip-locked claimed, retried, and retained safely."""
    fake = FakeSession()
    event = _outbox()
    repository = SqlAlchemyOutboxRepository(_session(fake))
    assert await repository.add(event) is event
    record = cast(OutboxEventORM, fake.added[-1])
    fake.scalar_results = [[record]]
    claimed = await repository.claim_batch("worker-1", 10, NOW)
    assert claimed[0].id == event.id
    assert record.locked_by == "worker-1"
    fake.execute_results = [
        FakeResult(rowcount=1),
        FakeResult(rowcount=1),
        FakeResult(rowcount=2),
    ]
    await repository.mark_published(event.id, NOW)
    await repository.mark_failed(event.id, "TEMPORARY", NOW + timedelta(seconds=5))
    assert await repository.release_expired_locks(NOW) == 2
    fake.scalar_results = [[record], [event.id]]
    assert len(await repository.list_repeated_failures(1, limit=1)) == 1
    fake.execute_results = [FakeResult(rowcount=1)]
    assert await repository.delete_old_published(NOW + timedelta(days=1), limit=1) == 1
    fake.scalar_results = [[]]
    assert await repository.delete_old_published(NOW, limit=1) == 0


@pytest.mark.asyncio
async def test_outbox_repository_validation_and_missing_paths() -> None:
    """Outbox operations reject invalid worker, retry, and cleanup inputs."""
    fake = FakeSession()
    repository = SqlAlchemyOutboxRepository(_session(fake))
    with pytest.raises(ValueError, match="Worker"):
        await repository.claim_batch(" ", 0, NOW)
    fake.execute_results = [FakeResult(rowcount=0), FakeResult(rowcount=0)]
    with pytest.raises(ValueError, match="not found"):
        await repository.mark_published(uuid4(), NOW)
    with pytest.raises(ValueError, match="not found"):
        await repository.mark_failed(uuid4(), "TEMP", NOW)
    with pytest.raises(ValueError, match="error code"):
        await repository.mark_failed(uuid4(), " ", NOW)
    with pytest.raises(ValueError, match="positive"):
        await repository.list_repeated_failures(0, limit=0)
    with pytest.raises(ValueError, match="positive"):
        await repository.delete_old_published(NOW, limit=0)
