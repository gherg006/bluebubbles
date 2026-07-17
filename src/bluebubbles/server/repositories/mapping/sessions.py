"""Pure session ORM/domain conversions."""

from bluebubbles.server.database.models.sessions import SessionORM
from bluebubbles.server.domain.sessions import Session


class SessionMapper:
    """Convert only hashed session data between persistence representations."""

    @staticmethod
    def to_domain(record: SessionORM) -> Session:
        """Return a detached session without exposing a raw token."""
        return Session(
            id=record.id,
            created_at=record.created_at,
            updated_at=record.last_seen_at,
            version=record.token_version,
            user_id=record.user_id,
            refresh_token_hash=record.refresh_token_hash.hex(),
            expires_at=record.refresh_expires_at,
            idle_expires_at=record.access_expires_at,
            ip_address=record.source_ip or "unknown",
            device_name=record.device_name,
            platform=record.client_version,
            login_time=record.created_at,
            invalidated_at=record.invalidated_at,
            invalidation_reason=record.invalidation_reason,
        )

    @staticmethod
    def to_orm(session: Session) -> SessionORM:
        """Return a new ORM row containing a one-way token hash only."""
        try:
            token_hash = bytes.fromhex(session.refresh_token_hash)
        except ValueError:
            token_hash = session.refresh_token_hash.encode("utf-8")
        return SessionORM(
            id=session.id,
            user_id=session.user_id,
            device_id=session.id,
            device_name=session.device_name,
            client_version=session.platform,
            source_ip=session.ip_address,
            refresh_token_hash=token_hash,
            last_seen_at=session.updated_at,
            access_expires_at=session.idle_expires_at,
            refresh_expires_at=session.expires_at,
            is_active=session.invalidated_at is None,
            invalidated_at=session.invalidated_at,
            invalidation_reason=session.invalidation_reason,
            token_version=session.version,
            created_at=session.created_at,
        )
