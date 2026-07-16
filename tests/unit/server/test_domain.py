"""Tests for infrastructure-free server domain invariants."""

from datetime import UTC, datetime, timedelta
from typing import TypedDict
from uuid import UUID, uuid4

import pytest

from bluebubbles.server.domain.alerts import SecurityAlert, SecurityAlertState
from bluebubbles.server.domain.announcements import Announcement
from bluebubbles.server.domain.attachments import Attachment, UploadSession
from bluebubbles.server.domain.audit import (
    AuditEvent,
    AuditSeverity,
    build_canonical_audit_data,
    calculate_audit_hash,
    verify_audit_link,
)
from bluebubbles.server.domain.common import BaseEntity
from bluebubbles.server.domain.configuration import ConfigurationRevision
from bluebubbles.server.domain.contacts import Contact
from bluebubbles.server.domain.conversations import (
    Conversation,
    ConversationMember,
    DirectConversationPair,
    can_add_member,
    can_remove_member,
    can_transfer_ownership,
)
from bluebubbles.server.domain.messages import (
    MessageDelivery,
    MessageVersion,
    validate_delivery_transition,
)
from bluebubbles.server.domain.outbox import OutboxEvent
from bluebubbles.server.domain.sessions import Session
from bluebubbles.server.domain.users import (
    Permission,
    Role,
    User,
    can_assign_role,
    can_disable_target,
    normalise_username,
)
from bluebubbles.shared.models.announcements import (
    AnnouncementPriority,
    AnnouncementTargetType,
)
from bluebubbles.shared.models.attachments import AttachmentStatus
from bluebubbles.shared.models.conversations import ConversationType, GroupRole
from bluebubbles.shared.models.messages import MessageDeliveryStatus
from bluebubbles.shared.models.users import PresenceState
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    HashAlgorithm,
)

NOW = datetime(2026, 7, 16, 12, tzinfo=UTC)


class _BaseValues(TypedDict):
    id: UUID
    created_at: datetime
    updated_at: datetime


def _base(entity_id: UUID | None = None) -> _BaseValues:
    return {"id": entity_id or uuid4(), "created_at": NOW, "updated_at": NOW}


def _member(
    conversation_id: UUID, user_id: UUID, role: GroupRole
) -> ConversationMember:
    return ConversationMember(
        **_base(),
        conversation_id=conversation_id,
        user_id=user_id,
        role=role,
        joined_at=NOW,
    )


def test_base_entity_soft_delete_restore_serialisation_and_validation() -> None:
    entity = BaseEntity(**_base())
    entity.touch(NOW + timedelta(seconds=1))
    assert entity.version == 2
    entity.mark_deleted(NOW + timedelta(seconds=2))
    assert entity.is_deleted
    entity.mark_deleted(NOW + timedelta(seconds=3))
    entity.restore(NOW + timedelta(seconds=3))
    assert entity.deleted_at is None
    assert entity.version == 4
    assert BaseEntity.from_dict(entity.to_dict()).id == entity.id
    with pytest.raises(ValueError, match="Unknown"):
        BaseEntity.from_dict({**entity.to_dict(), "unexpected": True})
    with pytest.raises(ValueError, match="timezone-aware"):
        BaseEntity(id=uuid4(), created_at=datetime.now(), updated_at=datetime.now())
    with pytest.raises(ValueError, match="monotonic"):
        entity.touch(NOW)


def test_user_role_and_profile_rules() -> None:
    manager_role = Role(uuid4(), "Manager", frozenset({Permission.MANAGE_USERS}))
    employee_role = Role(uuid4(), "Employee")
    actor = User(
        **_base(), username=" Boss ", display_name="Boss", role_id=manager_role.id
    )
    target = User(
        **_base(), username="User", display_name="User", role_id=employee_role.id
    )
    assert actor.username == "boss"
    assert can_assign_role(manager_role, employee_role)
    assert can_disable_target(actor, target, manager_role)
    actor.update_profile(
        display_name=" New Boss ",
        status_message=" Busy ",
        at=NOW + timedelta(seconds=1),
    )
    actor.change_presence(PresenceState.BUSY, NOW + timedelta(seconds=2))
    target.disable(NOW + timedelta(seconds=1))
    assert actor.display_name == "New Boss" and actor.status_message == "Busy"
    assert actor.presence is PresenceState.BUSY and not target.is_enabled
    assert normalise_username(" USER ") == "user"
    with pytest.raises(ValueError):
        normalise_username(" ")
    with pytest.raises(ValueError):
        Role(uuid4(), " ")


def test_session_expiry_refresh_and_idempotent_invalidation() -> None:
    session = Session(
        **_base(),
        user_id=uuid4(),
        refresh_token_hash="hash",
        expires_at=NOW + timedelta(hours=8),
        idle_expires_at=NOW + timedelta(hours=1),
        ip_address="192.0.2.1",
        device_name="Office PC",
        platform="Windows",
        login_time=NOW,
    )
    assert session.is_active(NOW) and session.can_refresh(NOW)
    assert session.is_expired(NOW + timedelta(hours=1))
    session.invalidate(NOW + timedelta(minutes=1), "logout")
    session.invalidate(NOW + timedelta(minutes=2), "ignored")
    assert not session.is_active(NOW + timedelta(minutes=2))
    assert session.invalidation_reason == "logout"
    with pytest.raises(ValueError):
        Session(
            **_base(),
            user_id=uuid4(),
            refresh_token_hash="",
            expires_at=NOW,
            idle_expires_at=NOW,
            ip_address="x",
            device_name="x",
            platform="x",
            login_time=NOW,
        )


def test_conversation_membership_and_ownership_rules() -> None:
    conversation_id = uuid4()
    owner_id, admin_id, member_id = uuid4(), uuid4(), uuid4()
    owner = _member(conversation_id, owner_id, GroupRole.OWNER)
    admin = _member(conversation_id, admin_id, GroupRole.ADMIN)
    conversation = Conversation(
        **_base(conversation_id),
        conversation_type=ConversationType.GROUP,
        created_by=owner_id,
        last_activity=NOW,
        title="Team",
        members={owner_id: owner, admin_id: admin},
    )
    assert can_add_member(conversation, admin_id)
    member = _member(conversation_id, member_id, GroupRole.MEMBER)
    conversation.add_member(member, NOW + timedelta(seconds=1))
    assert can_remove_member(conversation, admin_id, member_id)
    assert can_transfer_ownership(conversation, owner_id, admin_id)
    conversation.transfer_ownership(owner_id, admin_id, NOW + timedelta(seconds=2))
    assert admin.role is GroupRole.OWNER and owner.role is GroupRole.ADMIN
    conversation.remove_member(member_id, NOW + timedelta(seconds=3))
    assert not member.active
    conversation.rename("Renamed", NOW + timedelta(seconds=4))
    assert conversation.title == "Renamed"
    with pytest.raises(ValueError, match="already"):
        conversation.add_member(admin, NOW + timedelta(seconds=5))
    with pytest.raises(ValueError, match="owner"):
        conversation.remove_member(admin_id, NOW + timedelta(seconds=5))


def test_direct_pair_and_delivery_transitions() -> None:
    one, two, outsider = uuid4(), uuid4(), uuid4()
    pair = DirectConversationPair.create(one, two)
    assert pair.contains(one) and pair.other_user(one) == two
    with pytest.raises(ValueError, match="not part"):
        pair.other_user(outsider)
    with pytest.raises(ValueError, match="distinct"):
        DirectConversationPair(one, one)
    delivery = MessageDelivery(
        **_base(),
        message_id=uuid4(),
        recipient_id=uuid4(),
        status_at=NOW,
    )
    delivery.transition(MessageDeliveryStatus.STORED, NOW + timedelta(seconds=1))
    delivery.transition(MessageDeliveryStatus.DELIVERED, NOW + timedelta(seconds=2))
    delivery.transition(MessageDeliveryStatus.READ, NOW + timedelta(seconds=3))
    with pytest.raises(ValueError, match="Invalid delivery"):
        validate_delivery_transition(
            MessageDeliveryStatus.READ, MessageDeliveryStatus.STORED
        )
    with pytest.raises(ValueError):
        MessageVersion(
            message_id=uuid4(),
            version=0,
            ciphertext=b"c",
            nonce=b"n",
            signature=b"s",
            created_at=NOW,
        )


def test_upload_chunk_bounds_completion_and_attachment_linking() -> None:
    upload = UploadSession(
        **_base(),
        attachment_id=uuid4(),
        uploader_id=uuid4(),
        chunk_size=4,
        total_size=10,
        expires_at=NOW + timedelta(hours=1),
    )
    assert upload.expected_chunk_count == 3
    upload.accept_chunk(0, 4, NOW + timedelta(seconds=1))
    upload.accept_chunk(1, 4, NOW + timedelta(seconds=2))
    upload.accept_chunk(2, 2, NOW + timedelta(seconds=3))
    assert upload.is_complete()
    upload.complete(NOW + timedelta(seconds=4))
    with pytest.raises(ValueError):
        upload.accept_chunk(2, 2, NOW + timedelta(seconds=5))
    attachment = Attachment(
        **_base(),
        conversation_id=uuid4(),
        uploaded_by=uuid4(),
        filename="file.bin",
        media_type="application/octet-stream",
        encrypted_size=10,
        original_size=1,
        content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
        hash_algorithm=HashAlgorithm.SHA256_V1,
        encrypted_checksum=b"checksum",
        storage_reference="opaque/object",
        status=AttachmentStatus.COMPLETE,
    )
    attachment.link(uuid4(), NOW + timedelta(seconds=1))
    assert not attachment.can_be_linked()
    with pytest.raises(ValueError):
        attachment.link(uuid4(), NOW + timedelta(seconds=2))


def test_audit_hash_is_deterministic_and_verifiable() -> None:
    event_id = uuid4()
    actor_id = uuid4()
    digest = calculate_audit_hash(
        build_canonical_audit_data(
            event_id=event_id,
            event_type="session.login",
            occurred_at=NOW,
            actor_id=actor_id,
            source_address="192.0.2.1",
            severity=AuditSeverity.INFORMATIONAL,
            details={"result": "success"},
            previous_hash=None,
        )
    )
    event = AuditEvent(
        id=event_id,
        event_hash=digest,
        event_type="session.login",
        occurred_at=NOW,
        actor_id=actor_id,
        source_address="192.0.2.1",
        severity=AuditSeverity.INFORMATIONAL,
        details={"result": "success"},
        previous_hash=None,
    )
    assert verify_audit_link(event, None)
    assert not verify_audit_link(event, "wrong")


def test_contact_announcement_alert_configuration_and_outbox_lifecycles() -> None:
    contact = Contact(**_base(), owner_id=uuid4(), contact_id=uuid4())
    contact.set_favourite(True, NOW + timedelta(seconds=1))
    contact.increase_weight(2, NOW + timedelta(seconds=2))
    contact.set_blocked(True, NOW + timedelta(seconds=3))
    contact.reset_weight(NOW + timedelta(seconds=4))
    assert contact.is_blocked and not contact.is_favourite and contact.weight_score == 0
    with pytest.raises(ValueError):
        contact.increase_weight(0, NOW + timedelta(seconds=5))

    announcement = Announcement(
        **_base(),
        author_id=uuid4(),
        title="Maintenance",
        body="Tonight",
        priority=AnnouncementPriority.IMPORTANT,
        target_type=AnnouncementTargetType.ALL_USERS,
    )
    announcement.publish(NOW + timedelta(seconds=1))
    announcement.withdraw(NOW + timedelta(seconds=2))
    assert announcement.withdrawn_at is not None

    alert = SecurityAlert(**_base(), code="AUTH_SPIKE", summary="Login failures")
    alert.acknowledge(uuid4(), NOW + timedelta(seconds=1))
    alert.resolve(NOW + timedelta(seconds=2))
    assert alert.state is SecurityAlertState.RESOLVED

    revision = ConfigurationRevision(
        revision=1,
        changed_at=NOW,
        changed_by=uuid4(),
        changed_keys=frozenset({"limits.maximum_message_bytes"}),
        public_values={"limits.maximum_message_bytes": 1000},
    )
    assert revision.public_values["limits.maximum_message_bytes"] == 1000
    with pytest.raises(ValueError, match="secret"):
        ConfigurationRevision(1, NOW, uuid4(), frozenset(), {"password": "bad"})

    outbox = OutboxEvent(
        **_base(),
        event_type="message.stored",
        aggregate_id=uuid4(),
        protocol_version=1,
        payload={"message_id": str(uuid4())},
        available_at=NOW,
    )
    outbox.record_attempt(NOW + timedelta(seconds=1))
    outbox.mark_published(NOW + timedelta(seconds=2))
    outbox.mark_published(NOW + timedelta(seconds=3))
    assert outbox.attempts == 1 and outbox.published_at is not None
    with pytest.raises(ValueError):
        outbox.record_attempt(NOW + timedelta(seconds=4))
