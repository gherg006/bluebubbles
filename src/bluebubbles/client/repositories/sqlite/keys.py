"""Versioned public-key cache with expiry and revocation enforcement."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from bluebubbles.client.storage.database import LocalDatabaseManager
from bluebubbles.client.storage.models import CachedPublicKey


class SQLitePublicKeyCacheRepository:
    """Cache public keys while refusing expired or known-revoked versions."""

    def __init__(self, database: LocalDatabaseManager) -> None:
        self._database = database

    async def save(self, key: CachedPublicKey) -> None:
        """Upsert an exact user/type/version public key descriptor."""
        if key.key_version < 1 or not key.public_key or not key.fingerprint:
            raise ValueError("Public key cache metadata is invalid")
        await self._database.execute(
            "INSERT INTO cached_public_keys(user_id, key_type, key_version, "
            "public_key, "
            "fingerprint, retrieved_at, expires_at, is_revoked) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(user_id, key_type, key_version) DO UPDATE SET "
            "public_key=excluded.public_key, fingerprint=excluded.fingerprint, "
            "retrieved_at=excluded.retrieved_at, expires_at=excluded.expires_at, "
            "is_revoked=excluded.is_revoked",
            (
                str(key.user_id),
                key.key_type,
                key.key_version,
                key.public_key,
                key.fingerprint,
                key.retrieved_at.isoformat(),
                key.expires_at.isoformat(),
                int(key.is_revoked),
            ),
        )

    async def get_valid(
        self, user_id: UUID, key_type: str, key_version: int
    ) -> CachedPublicKey | None:
        """Return a key only while unrevoked and unexpired."""
        row = await self._database.fetch_one(
            "SELECT public_key, fingerprint, retrieved_at, expires_at, is_revoked "
            "FROM cached_public_keys WHERE user_id = ? AND key_type = ? "
            "AND key_version = ?",
            (str(user_id), key_type, key_version),
        )
        if row is None:
            return None
        expires = datetime.fromisoformat(str(row[3]))
        if bool(row[4]) or expires <= datetime.now(UTC):
            return None
        return CachedPublicKey(
            user_id,
            key_type,
            key_version,
            bytes(row[0]),
            str(row[1]),
            datetime.fromisoformat(str(row[2])),
            expires,
            False,
        )

    async def invalidate_user(self, user_id: UUID) -> None:
        """Mark every key version for a disabled or changed user revoked."""
        await self._database.execute(
            "UPDATE cached_public_keys SET is_revoked = 1 WHERE user_id = ?",
            (str(user_id),),
        )
