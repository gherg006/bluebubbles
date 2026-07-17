"""Async SQLAlchemy implementations of server repository protocols."""

from bluebubbles.server.repositories.sqlalchemy.administration import (
    SqlAlchemyAdministrationRepository,
)
from bluebubbles.server.repositories.sqlalchemy.announcements import (
    SqlAlchemyAnnouncementRepository,
)
from bluebubbles.server.repositories.sqlalchemy.attachments import (
    SqlAlchemyAttachmentRepository,
)
from bluebubbles.server.repositories.sqlalchemy.audit import SqlAlchemyAuditRepository
from bluebubbles.server.repositories.sqlalchemy.configuration import (
    SqlAlchemyConfigurationRepository,
)
from bluebubbles.server.repositories.sqlalchemy.contacts import (
    SqlAlchemyContactRepository,
)
from bluebubbles.server.repositories.sqlalchemy.conversations import (
    SqlAlchemyConversationRepository,
)
from bluebubbles.server.repositories.sqlalchemy.keys import (
    SqlAlchemyPublicKeyRepository,
)
from bluebubbles.server.repositories.sqlalchemy.messages import (
    SqlAlchemyMessageRepository,
)
from bluebubbles.server.repositories.sqlalchemy.outbox import (
    SqlAlchemyOutboxRepository,
)
from bluebubbles.server.repositories.sqlalchemy.sessions import (
    SqlAlchemySessionRepository,
)
from bluebubbles.server.repositories.sqlalchemy.users import SqlAlchemyUserRepository

__all__ = [
    "SqlAlchemyAdministrationRepository",
    "SqlAlchemyAnnouncementRepository",
    "SqlAlchemyAttachmentRepository",
    "SqlAlchemyAuditRepository",
    "SqlAlchemyConfigurationRepository",
    "SqlAlchemyContactRepository",
    "SqlAlchemyConversationRepository",
    "SqlAlchemyMessageRepository",
    "SqlAlchemyOutboxRepository",
    "SqlAlchemyPublicKeyRepository",
    "SqlAlchemySessionRepository",
    "SqlAlchemyUserRepository",
]
