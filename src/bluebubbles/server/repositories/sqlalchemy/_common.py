"""Shared error translation for SQLAlchemy repository adapters."""

from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.shared.errors.exceptions import ConflictError, RepositoryError


async def flush_changes(session: AsyncSession) -> None:
    """Flush pending writes while translating database details safely."""
    try:
        await session.flush()
    except IntegrityError as error:
        raise ConflictError(
            user_message="The requested record conflicts with existing data.",
            technical_message="A named database integrity constraint was rejected.",
        ) from error
    except DBAPIError as error:
        raise RepositoryError(
            user_message="The database operation could not be completed.",
            technical_message="A database adapter operation failed.",
            retryable=bool(error.connection_invalidated),
        ) from error


def require_aware(timestamp: object, field_name: str) -> None:
    """Reject naive timestamps before they cross the persistence boundary."""
    if getattr(timestamp, "tzinfo", None) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
