"""Infrastructure-independent server domain entities and business invariants."""

from bluebubbles.server.domain.alerts import SecurityAlert, SecurityAlertState
from bluebubbles.server.domain.announcements import Announcement
from bluebubbles.server.domain.attachments import (
    Attachment,
    AttachmentChunk,
    AttachmentRecipientKey,
    UploadSession,
)
from bluebubbles.server.domain.audit import (
    AuditChainState,
    AuditEvent,
    AuditSeverity,
    AuditVerificationResult,
    build_canonical_audit_data,
    calculate_audit_hash,
    verify_audit_link,
)
from bluebubbles.server.domain.common import BaseEntity, DomainEvent
from bluebubbles.server.domain.configuration import ConfigurationRevision
from bluebubbles.server.domain.contacts import Contact
from bluebubbles.server.domain.conversations import (
    Conversation,
    ConversationEvent,
    ConversationMember,
    DirectConversationPair,
)
from bluebubbles.server.domain.messages import (
    Message,
    MessageDelivery,
    MessageRecipientKey,
    MessageVersion,
)
from bluebubbles.server.domain.outbox import OutboxEvent
from bluebubbles.server.domain.sessions import AuthenticatedUser, LoginAttempt, Session
from bluebubbles.server.domain.users import (
    LocalCredential,
    Permission,
    PublicKeyRecord,
    Role,
    User,
)

__all__ = [
    "Attachment",
    "AttachmentChunk",
    "AttachmentRecipientKey",
    "Announcement",
    "AuditChainState",
    "AuditEvent",
    "AuditSeverity",
    "AuditVerificationResult",
    "AuthenticatedUser",
    "BaseEntity",
    "Conversation",
    "ConversationEvent",
    "ConversationMember",
    "DirectConversationPair",
    "DomainEvent",
    "ConfigurationRevision",
    "Contact",
    "LocalCredential",
    "LoginAttempt",
    "Message",
    "MessageDelivery",
    "MessageRecipientKey",
    "MessageVersion",
    "OutboxEvent",
    "Permission",
    "PublicKeyRecord",
    "Role",
    "SecurityAlert",
    "SecurityAlertState",
    "Session",
    "UploadSession",
    "User",
    "build_canonical_audit_data",
    "calculate_audit_hash",
    "verify_audit_link",
]
