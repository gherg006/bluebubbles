"""Encrypted, user-profile-specific client private-key storage."""

from __future__ import annotations

import asyncio
import base64
import json
import secrets
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from bluebubbles.shared.errors.exceptions import CryptographyError, LocalStorageError


class PrivateKeyType(StrEnum):
    """Identify client-only identity key purposes."""

    ENCRYPTION = "encryption"
    SIGNING = "signing"


PrivateKeyObject = X25519PrivateKey | Ed25519PrivateKey


@dataclass(frozen=True, slots=True)
class PrivateKeyRecord:
    """Carry a newly generated private key only as far as encrypted storage."""

    key_type: PrivateKeyType
    version: int
    algorithm: str
    fingerprint: str
    private_key: bytes
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PrivateKeyHandle:
    """Restrict access to one parsed in-memory private-key object."""

    key_type: PrivateKeyType
    version: int
    algorithm: str
    fingerprint: str
    _key: PrivateKeyObject

    @contextmanager
    def use_key(self) -> Iterator[PrivateKeyObject]:
        """Yield the parsed private key for the shortest practical scope."""
        yield self._key


class EncryptedPrivateKeyStore:
    """Persist AES-GCM encrypted private keys and maintain explicit lock state."""

    def __init__(self, storage_path: Path) -> None:
        self._storage_path = storage_path
        self._unlock_key: bytearray | None = None
        self._loaded_key_handles: dict[tuple[PrivateKeyType, int], PrivateKeyHandle] = (
            {}
        )
        self._lock = asyncio.Lock()

    @property
    def unlocked(self) -> bool:
        return self._unlock_key is not None

    async def unlock(self, unlock_key: bytes) -> None:
        """Unlock the store with an OS-protected, profile-specific 256-bit key."""
        if len(unlock_key) != 32:
            raise ValueError("Private-key store unlock key must be 32 bytes")
        async with self._lock:
            await self._clear_locked()
            self._unlock_key = bytearray(unlock_key)

    async def lock(self) -> None:
        """Release handles and overwrite the mutable unlock-key buffer."""
        async with self._lock:
            await self._clear_locked()

    async def store_key(self, key: PrivateKeyRecord) -> None:
        """Encrypt and atomically persist one versioned private-key record."""
        if key.version < 1 or len(key.private_key) != 32:
            raise ValueError("A positive version and 32-byte private key are required")
        async with self._lock:
            unlock_key = self._require_key()
            records = await asyncio.to_thread(self._read_records)
            record_key = f"{key.key_type.value}:{key.version}"
            aad = self._metadata_aad(key)
            nonce = secrets.token_bytes(12)
            encrypted = AESGCM(unlock_key).encrypt(nonce, key.private_key, aad)
            records[record_key] = {
                "key_type": key.key_type.value,
                "version": key.version,
                "algorithm": key.algorithm,
                "fingerprint": key.fingerprint,
                "created_at": key.created_at.isoformat(),
                "nonce": self._encode(nonce),
                "encrypted_private_key": self._encode(encrypted),
            }
            await asyncio.to_thread(self._write_records, records)
            self._loaded_key_handles.pop((key.key_type, key.version), None)

    async def load_key(
        self, key_type: PrivateKeyType, version: int
    ) -> PrivateKeyHandle:
        """Authenticate, decrypt, parse, and cache one private-key handle."""
        if version < 1:
            raise ValueError("Private-key version must be positive")
        async with self._lock:
            cached = self._loaded_key_handles.get((key_type, version))
            if cached is not None:
                return cached
            unlock_key = self._require_key()
            records = await asyncio.to_thread(self._read_records)
            raw = records.get(f"{key_type.value}:{version}")
            if raw is None:
                raise LocalStorageError(
                    user_message="The requested private key is unavailable."
                )
            try:
                raw_version = raw["version"]
                if not isinstance(raw_version, int):
                    raise ValueError
                record = PrivateKeyRecord(
                    key_type=PrivateKeyType(str(raw["key_type"])),
                    version=raw_version,
                    algorithm=str(raw["algorithm"]),
                    fingerprint=str(raw["fingerprint"]),
                    private_key=b"",
                    created_at=datetime.fromisoformat(str(raw["created_at"])),
                )
                private_bytes = AESGCM(unlock_key).decrypt(
                    self._decode(str(raw["nonce"])),
                    self._decode(str(raw["encrypted_private_key"])),
                    self._metadata_aad(record),
                )
                parsed: PrivateKeyObject
                if key_type is PrivateKeyType.ENCRYPTION:
                    parsed = X25519PrivateKey.from_private_bytes(private_bytes)
                else:
                    parsed = Ed25519PrivateKey.from_private_bytes(private_bytes)
            except (InvalidTag, KeyError, TypeError, ValueError) as error:
                raise CryptographyError(
                    user_message="The stored private key could not be verified."
                ) from error
            handle = PrivateKeyHandle(
                key_type, version, record.algorithm, record.fingerprint, parsed
            )
            self._loaded_key_handles[(key_type, version)] = handle
            return handle

    async def list_key_versions(self, key_type: PrivateKeyType) -> tuple[int, ...]:
        """Return stored versions for one purpose while the store is unlocked."""
        async with self._lock:
            self._require_key()
            records = await asyncio.to_thread(self._read_records)
            versions: list[int] = []
            for value in records.values():
                if value.get("key_type") != key_type.value:
                    continue
                version = value.get("version")
                if isinstance(version, int) and version > 0:
                    versions.append(version)
            return tuple(sorted(set(versions)))

    def _require_key(self) -> bytes:
        if self._unlock_key is None:
            raise LocalStorageError(user_message="The private-key store is locked.")
        return bytes(self._unlock_key)

    async def _clear_locked(self) -> None:
        self._loaded_key_handles.clear()
        if self._unlock_key is not None:
            for index in range(len(self._unlock_key)):
                self._unlock_key[index] = 0
        self._unlock_key = None

    def _read_records(self) -> dict[str, dict[str, object]]:
        if not self._storage_path.exists():
            return {}
        try:
            value = json.loads(self._storage_path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError
            return {
                str(key): dict(item)
                for key, item in value.items()
                if isinstance(item, dict)
            }
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            raise LocalStorageError(
                user_message="The private-key store could not be read."
            ) from error

    def _write_records(self, records: dict[str, dict[str, object]]) -> None:
        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self._storage_path.with_suffix(
                self._storage_path.suffix + ".tmp"
            )
            temporary.write_text(
                json.dumps(records, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            temporary.replace(self._storage_path)
        except OSError as error:
            raise LocalStorageError(
                user_message="The private-key store could not be saved."
            ) from error

    @staticmethod
    def _metadata_aad(key: PrivateKeyRecord) -> bytes:
        return "\x00".join(
            (
                "bluebubbles-private-key-v1",
                key.key_type.value,
                str(key.version),
                key.algorithm,
                key.fingerprint,
                key.created_at.isoformat(),
            )
        ).encode("utf-8")

    @staticmethod
    def _encode(value: bytes) -> str:
        return base64.b64encode(value).decode("ascii")

    @staticmethod
    def _decode(value: str) -> bytes:
        return base64.b64decode(value, validate=True)
