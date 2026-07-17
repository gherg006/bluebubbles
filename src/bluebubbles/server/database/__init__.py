"""PostgreSQL schema, seed catalogue, and migration compatibility helpers."""

from bluebubbles.server.database.base import NAMING_CONVENTION, Base
from bluebubbles.server.database.engine import DatabaseManager
from bluebubbles.server.database.migrations import (
    EXPECTED_REVISION,
    SchemaRevisionMismatchError,
    get_current_revision,
    get_expected_revision,
    verify_revision,
)
from bluebubbles.server.database.session import create_session_factory, session_scope
from bluebubbles.server.database.unit_of_work import (
    RepositoryFactory,
    ServerRepositories,
    SqlAlchemyRepositoryFactory,
    UnitOfWork,
    UnitOfWorkFactory,
    UnitOfWorkStateError,
)

__all__ = [
    "Base",
    "DatabaseManager",
    "EXPECTED_REVISION",
    "NAMING_CONVENTION",
    "SchemaRevisionMismatchError",
    "RepositoryFactory",
    "ServerRepositories",
    "SqlAlchemyRepositoryFactory",
    "UnitOfWork",
    "UnitOfWorkFactory",
    "UnitOfWorkStateError",
    "create_session_factory",
    "get_current_revision",
    "get_expected_revision",
    "verify_revision",
    "session_scope",
]
