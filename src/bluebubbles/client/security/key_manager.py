"""Client identity-key generation, registration, rotation, and retrieval."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from bluebubbles.client.security.key_store import (
    EncryptedPrivateKeyStore,
    PrivateKeyHandle,
    PrivateKeyRecord,
    PrivateKeyType,
)
from bluebubbles.shared.security.fingerprints import calculate_public_key_fingerprint
from bluebubbles.shared.security.key_models import (
    KeyFingerprint,
    KeyVersion,
    PublicKeyAlgorithm,
    PublicKeyDescriptor,
    PublicKeyType,
    RegisterPublicKeyRequest,
)


class ClientPublicKeyService(Protocol):
    """Register public-only identity material with the authenticated server."""

    async def register(
        self, request: RegisterPublicKeyRequest
    ) -> PublicKeyDescriptor: ...


@dataclass(frozen=True, slots=True)
class PublicIdentityKeys:
    """Return one independently versioned encryption/signing public-key pair."""

    encryption: PublicKeyDescriptor
    signing: PublicKeyDescriptor


class ClientKeyManager:
    """Own client identity-key creation while private bytes stay client-side."""

    def __init__(
        self,
        private_key_store: EncryptedPrivateKeyStore,
        public_key_service: ClientPublicKeyService,
    ) -> None:
        self._private_key_store = private_key_store
        self._public_key_service = public_key_service
        self._user_id: UUID | None = None
        self._versions = {
            PrivateKeyType.ENCRYPTION: 0,
            PrivateKeyType.SIGNING: 0,
        }

    async def ensure_identity_keys(self, user_id: UUID) -> PublicIdentityKeys:
        """Generate and register the initial independent identity key pairs."""
        self._user_id = user_id
        if self._versions[PrivateKeyType.ENCRYPTION] == 0:
            encryption_versions = await self._private_key_store.list_key_versions(
                PrivateKeyType.ENCRYPTION
            )
            signing_versions = await self._private_key_store.list_key_versions(
                PrivateKeyType.SIGNING
            )
            if encryption_versions and signing_versions:
                self._versions[PrivateKeyType.ENCRYPTION] = encryption_versions[-1]
                self._versions[PrivateKeyType.SIGNING] = signing_versions[-1]
                return await self._descriptors_for_current()
            if encryption_versions or signing_versions:
                raise ValueError("The local identity-key pair is incomplete")
            return await self._generate_and_register(1, 1)
        return await self._descriptors_for_current()

    async def get_private_encryption_key(self, version: int) -> PrivateKeyHandle:
        return await self._private_key_store.load_key(
            PrivateKeyType.ENCRYPTION, version
        )

    async def get_private_signing_key(self, version: int) -> PrivateKeyHandle:
        return await self._private_key_store.load_key(PrivateKeyType.SIGNING, version)

    async def rotate_keys(self) -> PublicIdentityKeys:
        """Rotate both Version 1 identity-key purposes monotonically."""
        if self._user_id is None:
            raise ValueError("Identity keys must be initialised before rotation")
        return await self._generate_and_register(
            self._versions[PrivateKeyType.ENCRYPTION] + 1,
            self._versions[PrivateKeyType.SIGNING] + 1,
        )

    async def _generate_and_register(
        self, encryption_version: int, signing_version: int
    ) -> PublicIdentityKeys:
        user_id = self._require_user()
        encryption_private = X25519PrivateKey.generate()
        signing_private = Ed25519PrivateKey.generate()
        encryption = await self._store_and_register(
            user_id,
            PrivateKeyType.ENCRYPTION,
            encryption_version,
            PublicKeyAlgorithm.X25519_V1,
            encryption_private,
        )
        signing = await self._store_and_register(
            user_id,
            PrivateKeyType.SIGNING,
            signing_version,
            PublicKeyAlgorithm.ED25519_V1,
            signing_private,
        )
        self._versions[PrivateKeyType.ENCRYPTION] = encryption_version
        self._versions[PrivateKeyType.SIGNING] = signing_version
        return PublicIdentityKeys(encryption, signing)

    async def _store_and_register(
        self,
        user_id: UUID,
        key_type: PrivateKeyType,
        version: int,
        algorithm: PublicKeyAlgorithm,
        private_key: X25519PrivateKey | Ed25519PrivateKey,
    ) -> PublicKeyDescriptor:
        public_type = PublicKeyType(key_type.value)
        public_bytes = private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        private_bytes = private_key.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        )
        fingerprint = calculate_public_key_fingerprint(
            public_bytes,
            algorithm=algorithm.value,
            key_type=public_type.value,
            key_version=version,
        )
        created_at = datetime.now(UTC)
        await self._private_key_store.store_key(
            PrivateKeyRecord(
                key_type,
                version,
                algorithm.value,
                fingerprint,
                private_bytes,
                created_at,
            )
        )
        return await self._public_key_service.register(
            RegisterPublicKeyRequest(
                key_type=public_type,
                version=KeyVersion(value=version),
                algorithm=algorithm,
                public_key=base64.b64encode(public_bytes).decode("ascii"),
                fingerprint=KeyFingerprint(value=fingerprint),
            )
        )

    async def _descriptors_for_current(self) -> PublicIdentityKeys:
        """Reconstruct public descriptors from the encrypted key handles."""
        user_id = self._require_user()
        encryption = await self.get_private_encryption_key(
            self._versions[PrivateKeyType.ENCRYPTION]
        )
        signing = await self.get_private_signing_key(
            self._versions[PrivateKeyType.SIGNING]
        )
        return PublicIdentityKeys(
            self._descriptor_from_handle(user_id, encryption),
            self._descriptor_from_handle(user_id, signing),
        )

    @staticmethod
    def _descriptor_from_handle(
        user_id: UUID, handle: PrivateKeyHandle
    ) -> PublicKeyDescriptor:
        with handle.use_key() as key:
            public_key = key.public_key().public_bytes(
                serialization.Encoding.Raw, serialization.PublicFormat.Raw
            )
        return PublicKeyDescriptor(
            owner_id=user_id,
            key_type=PublicKeyType(handle.key_type.value),
            version=KeyVersion(value=handle.version),
            algorithm=PublicKeyAlgorithm(handle.algorithm),
            public_key=base64.b64encode(public_key).decode("ascii"),
            fingerprint=KeyFingerprint(value=handle.fingerprint),
            created_at=datetime.now(UTC),
            is_primary=True,
        )

    def _require_user(self) -> UUID:
        if self._user_id is None:
            raise ValueError("Identity key user is not initialised")
        return self._user_id
