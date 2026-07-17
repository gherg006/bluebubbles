"""Transaction-scoped repository composition and completion ownership."""

from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import Protocol, Self

from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bluebubbles.server.repositories.interfaces import (
    AdministrationRepository,
    AnnouncementRepository,
    AttachmentRepository,
    AuditRepository,
    ConfigurationRepository,
    ContactRepository,
    ConversationRepository,
    MessageRepository,
    OutboxRepository,
    PublicKeyRepository,
    SessionRepository,
    UserRepository,
)
from bluebubbles.server.repositories.sqlalchemy import (
    SqlAlchemyAdministrationRepository,
    SqlAlchemyAnnouncementRepository,
    SqlAlchemyAttachmentRepository,
    SqlAlchemyAuditRepository,
    SqlAlchemyConfigurationRepository,
    SqlAlchemyContactRepository,
    SqlAlchemyConversationRepository,
    SqlAlchemyMessageRepository,
    SqlAlchemyOutboxRepository,
    SqlAlchemyPublicKeyRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyUserRepository,
)
from bluebubbles.shared.errors.exceptions import ConflictError, RepositoryError


class UnitOfWorkStateError(RuntimeError):
    """Report use after closure or contradictory transaction completion."""


@dataclass(frozen=True, slots=True)
class ServerRepositories:
    """Group every server repository that shares one transaction session."""

    users: UserRepository
    sessions: SessionRepository
    contacts: ContactRepository
    public_keys: PublicKeyRepository
    conversations: ConversationRepository
    messages: MessageRepository
    attachments: AttachmentRepository
    audit: AuditRepository
    announcements: AnnouncementRepository
    administration: AdministrationRepository
    configuration: ConfigurationRepository
    outbox: OutboxRepository


class RepositoryFactory(Protocol):
    """Construct one complete repository bundle over a caller-owned session."""

    def __call__(self, session: AsyncSession) -> ServerRepositories:
        """Build repositories sharing ``session`` without taking ownership."""
        ...


class SqlAlchemyRepositoryFactory:
    """Construct the production SQLAlchemy repository bundle."""

    def __call__(self, session: AsyncSession) -> ServerRepositories:
        """Create all repository adapters over exactly one session.

        Args:
            session: Unit-of-Work-owned SQLAlchemy session.

        Returns:
            An immutable complete repository bundle.
        """
        return ServerRepositories(
            users=SqlAlchemyUserRepository(session),
            sessions=SqlAlchemySessionRepository(session),
            contacts=SqlAlchemyContactRepository(session),
            public_keys=SqlAlchemyPublicKeyRepository(session),
            conversations=SqlAlchemyConversationRepository(session),
            messages=SqlAlchemyMessageRepository(session),
            attachments=SqlAlchemyAttachmentRepository(session),
            audit=SqlAlchemyAuditRepository(session),
            announcements=SqlAlchemyAnnouncementRepository(session),
            administration=SqlAlchemyAdministrationRepository(session),
            configuration=SqlAlchemyConfigurationRepository(session),
            outbox=SqlAlchemyOutboxRepository(session),
        )


class UnitOfWorkFactory:
    """Create isolated transaction-scoped Units of Work."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        repository_factory: RepositoryFactory,
    ) -> None:
        """Store application-scoped factories without creating a session yet."""
        self._session_factory = session_factory
        self._repository_factory = repository_factory

    def __call__(self) -> UnitOfWork:
        """Create a fresh session, repositories, and Unit of Work.

        Returns:
            A new, uncompleted Unit of Work ready for async context management.
        """
        session = self._session_factory()
        repositories = self._repository_factory(session)
        return UnitOfWork(session, repositories)


class UnitOfWork:
    """Coordinate repositories sharing one explicit database transaction."""

    def __init__(
        self,
        session: AsyncSession,
        repositories: ServerRepositories,
    ) -> None:
        """Take ownership of one session and expose its repository bundle."""
        self._session = session
        self.repositories = repositories
        self.users = repositories.users
        self.sessions = repositories.sessions
        self.contacts = repositories.contacts
        self.public_keys = repositories.public_keys
        self.conversations = repositories.conversations
        self.messages = repositories.messages
        self.attachments = repositories.attachments
        self.audit = repositories.audit
        self.announcements = repositories.announcements
        self.administration = repositories.administration
        self.configuration = repositories.configuration
        self.outbox = repositories.outbox
        self._committed = False
        self._rolled_back = False
        self._closed = False
        self._entered = False

    @property
    def committed(self) -> bool:
        """Return whether this transaction completed by commit."""
        return self._committed

    @property
    def rolled_back(self) -> bool:
        """Return whether this transaction completed by rollback."""
        return self._rolled_back

    @property
    def closed(self) -> bool:
        """Return whether the owned session has been closed."""
        return self._closed

    async def __aenter__(self) -> Self:
        """Enter this Unit of Work exactly once.

        Returns:
            This Unit of Work.

        Raises:
            UnitOfWorkStateError: If it was already entered or closed.
        """
        if self._closed or self._entered:
            raise UnitOfWorkStateError("Unit of Work cannot be entered more than once")
        self._entered = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Roll back unfinished work and always close the owned session.

        An explicit successful commit is retained. Every other exit rolls back,
        including a normal exit without a commit. When a body exception exists,
        cleanup cannot replace it with a secondary rollback or close failure.
        """
        del exc_type, traceback
        cleanup_error: BaseException | None = None
        if not self._committed and not self._rolled_back:
            try:
                await self._rollback_session()
            except BaseException as error:
                cleanup_error = error
            finally:
                self._rolled_back = True
        try:
            await self._session.close()
        except BaseException as error:
            cleanup_error = cleanup_error or error
        finally:
            self._closed = True
        if exc is None and cleanup_error is not None:
            raise cleanup_error

    async def commit(self) -> None:
        """Commit all repository writes exactly once.

        Raises:
            UnitOfWorkStateError: If closed or already rolled back.
            ConflictError: If a database integrity constraint rejects the commit.
            RepositoryError: If the database adapter fails during commit.
        """
        self._require_open()
        if self._rolled_back:
            raise UnitOfWorkStateError("Cannot commit a rolled-back Unit of Work")
        if self._committed:
            return
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._rollback_after_failed_completion()
            raise ConflictError(
                user_message="The requested transaction conflicts with stored data.",
                technical_message=(
                    "A database integrity constraint rejected the commit."
                ),
            ) from error
        except DBAPIError as error:
            await self._rollback_after_failed_completion()
            raise RepositoryError(
                user_message="The database transaction could not be completed.",
                technical_message="A database adapter operation failed during commit.",
                retryable=bool(error.connection_invalidated),
            ) from error
        except BaseException:
            await self._rollback_after_failed_completion()
            raise
        self._committed = True

    async def rollback(self) -> None:
        """Roll back this transaction exactly once.

        Raises:
            UnitOfWorkStateError: If closed or already committed.
        """
        self._require_open()
        if self._committed:
            raise UnitOfWorkStateError("Cannot roll back a committed Unit of Work")
        if self._rolled_back:
            return
        try:
            await self._rollback_session()
        finally:
            self._rolled_back = True

    async def flush(self) -> None:
        """Flush pending changes without completing the transaction.

        Raises:
            UnitOfWorkStateError: If the transaction is closed or completed.
            ConflictError: If a database integrity constraint rejects the flush.
            RepositoryError: If the database adapter fails during the flush.
        """
        self._require_active()
        try:
            await self._session.flush()
        except IntegrityError as error:
            raise ConflictError(
                user_message="The requested record conflicts with existing data.",
                technical_message="A database integrity constraint rejected the flush.",
            ) from error
        except DBAPIError as error:
            raise RepositoryError(
                user_message="The database operation could not be completed.",
                technical_message="A database adapter operation failed during flush.",
                retryable=bool(error.connection_invalidated),
            ) from error

    def _require_open(self) -> None:
        if self._closed:
            raise UnitOfWorkStateError("Unit of Work is closed")

    def _require_active(self) -> None:
        self._require_open()
        if self._committed or self._rolled_back:
            raise UnitOfWorkStateError("Unit of Work transaction is already completed")

    async def _rollback_after_failed_completion(self) -> None:
        try:
            await self._rollback_session()
        except BaseException:
            # The primary commit/cancellation error remains authoritative. A later
            # lifecycle/monitoring stage can record secondary cleanup failures.
            return
        finally:
            self._rolled_back = True

    async def _rollback_session(self) -> None:
        try:
            await self._session.rollback()
        except DBAPIError as error:
            raise RepositoryError(
                user_message="The database transaction could not be rolled back.",
                technical_message=(
                    "A database adapter operation failed during rollback."
                ),
                retryable=bool(error.connection_invalidated),
            ) from error
