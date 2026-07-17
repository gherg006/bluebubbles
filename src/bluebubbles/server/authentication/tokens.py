"""HS256 access-token validation and opaque refresh-token generation."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final, cast
from uuid import UUID, uuid4

from bluebubbles.server.configuration.settings import TokenSettings
from bluebubbles.server.domain.sessions import Session
from bluebubbles.server.domain.users import User
from bluebubbles.shared.errors.exceptions import InvalidTokenError

_TOKEN_VERSION: Final[int] = 1


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    """Contain validated immutable claims from one access token."""

    user_id: UUID
    session_id: UUID
    issued_at: datetime
    expires_at: datetime
    token_id: UUID
    token_version: int


class TokenManager:
    """Create signed access tokens and one-way-hashed refresh material."""

    def __init__(
        self,
        settings: TokenSettings,
        clock: Callable[[], datetime] | None = None,
        random_bytes: Callable[[int], bytes] | None = None,
    ) -> None:
        if settings.signing_algorithm != "HS256":
            raise ValueError("Only the configured HS256 token algorithm is supported")
        self._settings = settings
        self._clock = clock or (lambda: datetime.now(UTC))
        self._random_bytes = random_bytes or secrets.token_bytes
        self._secret = settings.signing_secret.get_secret_value().encode("utf-8")

    def create_access_token(self, user: User, session: Session) -> str:
        """Create a bounded HS256 access token for one persisted session."""
        now = self._require_aware(self._clock())
        expires = min(
            now + timedelta(seconds=self._settings.access_token_lifetime_seconds),
            session.access_expires_at,
        )
        payload: dict[str, object] = {
            "iss": self._settings.issuer,
            "aud": self._settings.audience,
            "sub": str(user.id),
            "sid": str(session.id),
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
            "jti": str(uuid4()),
            "ver": session.version,
            "typ": "access",
        }
        header = {"alg": "HS256", "typ": "JWT"}
        unsigned = f"{self._encode(header)}.{self._encode(payload)}"
        signature = hmac.new(self._secret, unsigned.encode("ascii"), hashlib.sha256)
        return f"{unsigned}.{self._b64encode(signature.digest())}"

    def create_refresh_token(self) -> str:
        """Return a URL-safe 256-bit opaque token intended for one-time issue."""
        return self._b64encode(self._random_bytes(32))

    def hash_refresh_token(self, refresh_token: str) -> bytes:
        """Return a fixed one-way SHA-256 digest for server-side comparison."""
        if not refresh_token:
            raise InvalidTokenError()
        return hashlib.sha256(refresh_token.encode("utf-8")).digest()

    def decode_access_token(self, token: str) -> AccessTokenClaims:
        """Validate all security claims and return typed immutable claim data."""
        try:
            encoded_header, encoded_payload, encoded_signature = token.split(".")
            unsigned = f"{encoded_header}.{encoded_payload}"
            expected = hmac.new(
                self._secret, unsigned.encode("ascii"), hashlib.sha256
            ).digest()
            supplied = self._b64decode(encoded_signature)
            if not hmac.compare_digest(expected, supplied):
                raise ValueError
            header = self._decode_json(encoded_header)
            payload = self._decode_json(encoded_payload)
            if header != {"alg": "HS256", "typ": "JWT"}:
                raise ValueError
            now = self._require_aware(self._clock())
            if (
                payload.get("iss") != self._settings.issuer
                or payload.get("aud") != self._settings.audience
                or payload.get("typ") != "access"
            ):
                raise ValueError
            issued = self._integer_claim(payload, "iat")
            expiry = self._integer_claim(payload, "exp")
            version = self._integer_claim(payload, "ver")
            issued_at = datetime.fromtimestamp(issued, UTC)
            expires_at = datetime.fromtimestamp(expiry, UTC)
            if version < _TOKEN_VERSION or issued_at > now or expires_at <= now:
                raise ValueError
            return AccessTokenClaims(
                user_id=UUID(self._string_claim(payload, "sub")),
                session_id=UUID(self._string_claim(payload, "sid")),
                issued_at=issued_at,
                expires_at=expires_at,
                token_id=UUID(self._string_claim(payload, "jti")),
                token_version=version,
            )
        except (
            KeyError,
            TypeError,
            ValueError,
            UnicodeError,
            json.JSONDecodeError,
        ) as error:
            raise InvalidTokenError() from error

    @staticmethod
    def _require_aware(value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Token clock must return a timezone-aware timestamp")
        return value

    @classmethod
    def _encode(cls, value: object) -> str:
        return cls._b64encode(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )

    @staticmethod
    def _decode_json(value: str) -> dict[str, object]:
        decoded = json.loads(TokenManager._b64decode(value))
        if not isinstance(decoded, dict):
            raise ValueError
        return cast(dict[str, object], decoded)

    @staticmethod
    def _b64encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    @staticmethod
    def _b64decode(value: str) -> bytes:
        return base64.b64decode(
            value + "=" * (-len(value) % 4), altchars=b"-_", validate=True
        )

    @staticmethod
    def _string_claim(payload: dict[str, object], name: str) -> str:
        value = payload[name]
        if not isinstance(value, str) or not value:
            raise ValueError
        return value

    @staticmethod
    def _integer_claim(payload: dict[str, object], name: str) -> int:
        value = payload[name]
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError
        return value
