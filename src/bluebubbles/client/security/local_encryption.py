"""Purpose-separated authenticated encryption for local client records."""

from __future__ import annotations

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from bluebubbles.shared.errors.exceptions import CryptographyError


class LocalEncryptionPurpose(StrEnum):
    """Separate keys for unrelated local data classes."""

    PRIVATE_KEYS = "private_keys"
    MESSAGE_CACHE = "message_cache"
    DRAFT = "draft"
    OFFLINE_QUEUE = "offline_queue"
    SEARCH_INDEX = "search_index"
    TRANSFER_STATE = "transfer_state"
    THUMBNAIL = "thumbnail"


class LocalKeyProvider(Protocol):
    """Return the protected 256-bit master key for one local profile."""

    async def get_master_key(self) -> bytes: ...


@dataclass(frozen=True, slots=True)
class EncryptedLocalValue:
    """Hold one versioned AES-GCM value; the authentication tag is appended."""

    version: int
    nonce: bytes
    ciphertext: bytes


class LocalEncryptionService:
    """Encrypt local values with HKDF-derived purpose-specific keys."""

    def __init__(
        self,
        key_provider: LocalKeyProvider,
        random_bytes: Callable[[int], bytes] = secrets.token_bytes,
    ) -> None:
        self._key_provider = key_provider
        self._random_bytes = random_bytes

    async def encrypt(
        self,
        purpose: LocalEncryptionPurpose,
        plaintext: bytes,
        context: bytes,
    ) -> EncryptedLocalValue:
        """Encrypt one non-empty value using fresh randomness and bound context."""
        if not plaintext or not context:
            raise ValueError("Plaintext and local encryption context are required")
        nonce = self._random_bytes(12)
        key = await self._derive_key(purpose)
        aad = self._aad(purpose, context)
        return EncryptedLocalValue(1, nonce, AESGCM(key).encrypt(nonce, plaintext, aad))

    async def decrypt(
        self,
        purpose: LocalEncryptionPurpose,
        value: EncryptedLocalValue,
        context: bytes,
    ) -> bytes:
        """Authenticate and decrypt one value without exposing tag failures."""
        if value.version != 1 or len(value.nonce) != 12 or not context:
            raise CryptographyError(
                user_message="Protected local data could not be verified."
            )
        try:
            return AESGCM(await self._derive_key(purpose)).decrypt(
                value.nonce, value.ciphertext, self._aad(purpose, context)
            )
        except (InvalidTag, ValueError) as error:
            raise CryptographyError(
                user_message="Protected local data could not be verified."
            ) from error

    async def _derive_key(self, purpose: LocalEncryptionPurpose) -> bytes:
        master = await self._key_provider.get_master_key()
        if len(master) != 32:
            raise CryptographyError(
                user_message="The local protection key is unavailable."
            )
        return HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"bluebubbles-local-v1",
            info=b"bluebubbles:" + purpose.value.encode("ascii"),
        ).derive(master)

    @staticmethod
    def _aad(purpose: LocalEncryptionPurpose, context: bytes) -> bytes:
        return (
            b"bluebubbles-local-v1\x00"
            + purpose.value.encode("ascii")
            + b"\x00"
            + context
        )
