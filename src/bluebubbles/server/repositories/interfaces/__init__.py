"""Infrastructure-neutral repository protocols used by application services."""

from bluebubbles.server.repositories.interfaces.administration import (
    AdministrationRepository,
)
from bluebubbles.server.repositories.interfaces.announcements import (
    AnnouncementRepository,
)
from bluebubbles.server.repositories.interfaces.attachments import AttachmentRepository
from bluebubbles.server.repositories.interfaces.audit import AuditRepository
from bluebubbles.server.repositories.interfaces.authentication import (
    AuthenticationRepository,
)
from bluebubbles.server.repositories.interfaces.configuration import (
    ConfigurationRepository,
)
from bluebubbles.server.repositories.interfaces.contacts import ContactRepository
from bluebubbles.server.repositories.interfaces.conversations import (
    ConversationRepository,
)
from bluebubbles.server.repositories.interfaces.keys import PublicKeyRepository
from bluebubbles.server.repositories.interfaces.messages import MessageRepository
from bluebubbles.server.repositories.interfaces.outbox import OutboxRepository
from bluebubbles.server.repositories.interfaces.sessions import SessionRepository
from bluebubbles.server.repositories.interfaces.users import UserRepository

__all__ = [
    "AdministrationRepository",
    "AnnouncementRepository",
    "AttachmentRepository",
    "AuthenticationRepository",
    "AuditRepository",
    "ConfigurationRepository",
    "ContactRepository",
    "ConversationRepository",
    "MessageRepository",
    "OutboxRepository",
    "PublicKeyRepository",
    "SessionRepository",
    "UserRepository",
]
