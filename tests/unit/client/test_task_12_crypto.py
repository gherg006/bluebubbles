"""Task 12 cryptographic construction, storage, and streaming evidence."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from bluebubbles.client.security.attachment_crypto import (
    AttachmentEncryptionService,
    DecryptAttachmentCommand,
    PrepareAttachmentCommand,
)
from bluebubbles.client.security.key_manager import ClientKeyManager
from bluebubbles.client.security.key_store import (
    EncryptedPrivateKeyStore,
    PrivateKeyType,
)
from bluebubbles.client.security.local_encryption import (
    EncryptedLocalValue,
    LocalEncryptionPurpose,
    LocalEncryptionService,
)
from bluebubbles.client.security.message_crypto import (
    EncryptMessageCommand,
    MessageEncryptionService,
    RecipientPublicEncryptionKey,
)
from bluebubbles.shared.errors.exceptions import CryptographyError, LocalStorageError
from bluebubbles.shared.models.messages import EncryptedMessageResponse, MessageType
from bluebubbles.shared.security.key_models import (
    PublicKeyDescriptor,
    RegisterPublicKeyRequest,
)


class _PublicKeys:
    def __init__(self, owner_id: UUID) -> None:
        self.owner_id = owner_id
        self.registered: list[PublicKeyDescriptor] = []

    async def register(self, request: RegisterPublicKeyRequest) -> PublicKeyDescriptor:
        descriptor = PublicKeyDescriptor(
            owner_id=self.owner_id,
            key_type=request.key_type,
            version=request.version,
            algorithm=request.algorithm,
            public_key=request.public_key,
            fingerprint=request.fingerprint,
            created_at=datetime.now(UTC),
            is_primary=True,
        )
        self.registered.append(descriptor)
        return descriptor


class _SigningResolver:
    def __init__(self, service: _PublicKeys) -> None:
        self.service = service

    async def get_signing_key(self, user_id: UUID, version: int) -> bytes:
        descriptor = next(
            item
            for item in self.service.registered
            if item.owner_id == user_id
            and item.key_type.value == "signing"
            and item.version.value == version
        )
        return base64.b64decode(descriptor.public_key)


class _MasterKey:
    def __init__(self, value: bytes) -> None:
        self.value = value

    async def get_master_key(self) -> bytes:
        return self.value


class _NotCancelled:
    def raise_if_cancelled(self) -> None:
        return None


class _Cancelled:
    def raise_if_cancelled(self) -> None:
        raise RuntimeError("cancelled")


async def _identity(
    tmp_path: Path,
) -> tuple[UUID, EncryptedPrivateKeyStore, ClientKeyManager, _PublicKeys]:
    user_id = uuid4()
    store = EncryptedPrivateKeyStore(tmp_path / "keys.json")
    await store.unlock(b"k" * 32)
    public = _PublicKeys(user_id)
    manager = ClientKeyManager(store, public)
    await manager.ensure_identity_keys(user_id)
    return user_id, store, manager, public


@pytest.mark.asyncio
async def test_private_key_store_encrypts_locks_and_reloads(tmp_path: Path) -> None:
    user_id, store, manager, public = await _identity(tmp_path)
    assert user_id
    assert len(public.registered) == 2
    raw = (tmp_path / "keys.json").read_text(encoding="utf-8")
    assert "private_key" in raw
    assert "k" * 32 not in raw
    assert await store.list_key_versions(PrivateKeyType.ENCRYPTION) == (1,)
    assert (await manager.get_private_encryption_key(1)).version == 1
    await store.lock()
    with pytest.raises(LocalStorageError):
        await manager.get_private_signing_key(1)
    await store.unlock(b"k" * 32)
    restored = ClientKeyManager(store, public)
    keys = await restored.ensure_identity_keys(user_id)
    assert keys.encryption.version.value == 1
    assert len(public.registered) == 2


@pytest.mark.asyncio
async def test_private_key_store_rejects_wrong_key_and_tampering(
    tmp_path: Path,
) -> None:
    _, store, manager, _ = await _identity(tmp_path)
    await store.lock()
    await store.unlock(b"z" * 32)
    with pytest.raises(CryptographyError):
        await manager.get_private_encryption_key(1)
    await store.unlock(b"k" * 32)
    path = tmp_path / "keys.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    records["encryption:1"]["fingerprint"] = "AAAA-" * 15 + "AAAA"
    path.write_text(json.dumps(records), encoding="utf-8")
    await store.lock()
    await store.unlock(b"k" * 32)
    with pytest.raises(CryptographyError):
        await store.load_key(PrivateKeyType.ENCRYPTION, 1)


@pytest.mark.asyncio
async def test_message_round_trip_and_tamper_rejection(tmp_path: Path) -> None:
    user_id, _, manager, public = await _identity(tmp_path)
    other_id = uuid4()
    other_private = X25519PrivateKey.generate()
    other_public = other_private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    own_descriptor = next(
        item for item in public.registered if item.key_type.value == "encryption"
    )
    own_public = base64.b64decode(own_descriptor.public_key)
    service = MessageEncryptionService(manager, _SigningResolver(public))
    now = datetime.now(UTC)
    request = await service.encrypt_message(
        EncryptMessageCommand(
            message_id=uuid4(),
            conversation_id=uuid4(),
            sender_id=user_id,
            message_type=MessageType.TEXT,
            plaintext="authenticated hello",
            recipient_public_keys=(
                RecipientPublicEncryptionKey(user_id, 1, own_public),
                RecipientPublicEncryptionKey(other_id, 1, other_public),
            ),
            sender_signing_key_version=1,
            client_created_at=now,
        )
    )
    response = EncryptedMessageResponse(
        id=request.client_message_id,
        client_message_id=request.client_message_id,
        conversation_id=request.conversation_id,
        sender_id=user_id,
        message_type=request.message_type,
        content_algorithm=request.content_algorithm,
        ciphertext=request.ciphertext,
        nonce=request.nonce,
        signature_algorithm=request.signature_algorithm,
        signature=request.signature,
        sender_key_version=request.sender_key_version,
        encrypted_key=next(
            item for item in request.encrypted_keys if item.recipient_id == user_id
        ),
        recipient_envelope_digest=request.recipient_envelope_digest or "",
        sent_at=now,
    )
    assert (await service.decrypt_message(response)).text == "authenticated hello"
    bad_signature = base64.b64encode(b"x" * 64).decode("ascii")
    with pytest.raises(CryptographyError):
        await service.decrypt_message(
            response.model_copy(update={"signature": bad_signature})
        )
    tampered = base64.b64encode(base64.b64decode(response.ciphertext) + b"x").decode(
        "ascii"
    )
    with pytest.raises(CryptographyError):
        await service.decrypt_message(
            response.model_copy(update={"ciphertext": tampered})
        )


@pytest.mark.asyncio
async def test_message_encryption_rejects_missing_sender_and_long_text(
    tmp_path: Path,
) -> None:
    user_id, _, manager, public = await _identity(tmp_path)
    service = MessageEncryptionService(manager, _SigningResolver(public))
    key = (
        X25519PrivateKey.generate()
        .public_key()
        .public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    )
    with pytest.raises(ValueError, match="include the sender"):
        await service.encrypt_message(
            EncryptMessageCommand(
                message_id=uuid4(),
                conversation_id=uuid4(),
                sender_id=user_id,
                message_type=MessageType.TEXT,
                plaintext="x",
                recipient_public_keys=(RecipientPublicEncryptionKey(uuid4(), 1, key),),
                sender_signing_key_version=1,
                client_created_at=datetime.now(UTC),
            )
        )
    with pytest.raises(ValueError, match="exceeds"):
        await service.encrypt_message(
            EncryptMessageCommand(
                message_id=uuid4(),
                conversation_id=uuid4(),
                sender_id=user_id,
                message_type=MessageType.TEXT,
                plaintext="x" * 8001,
                recipient_public_keys=(RecipientPublicEncryptionKey(user_id, 1, key),),
                sender_signing_key_version=1,
                client_created_at=datetime.now(UTC),
            )
        )


@pytest.mark.asyncio
async def test_local_encryption_separates_purpose_and_authenticates_context() -> None:
    service = LocalEncryptionService(
        _MasterKey(b"m" * 32), random_bytes=lambda _: b"n" * 12
    )
    value = await service.encrypt(
        LocalEncryptionPurpose.MESSAGE_CACHE, b"secret cache", b"message:1"
    )
    assert (
        await service.decrypt(LocalEncryptionPurpose.MESSAGE_CACHE, value, b"message:1")
        == b"secret cache"
    )
    with pytest.raises(CryptographyError):
        await service.decrypt(LocalEncryptionPurpose.OFFLINE_QUEUE, value, b"message:1")
    with pytest.raises(CryptographyError):
        await service.decrypt(
            LocalEncryptionPurpose.MESSAGE_CACHE,
            EncryptedLocalValue(1, value.nonce, value.ciphertext[:-1] + b"x"),
            b"message:1",
        )


@pytest.mark.asyncio
async def test_attachment_streaming_round_trip_and_failure_cleanup(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes((b"bluebubbles" * 30_000) + b"tail")
    encrypted = tmp_path / "encrypted.bin"
    output = tmp_path / "output.bin"
    service = AttachmentEncryptionService()
    prepared = await service.encrypt_file(
        PrepareAttachmentCommand(source, encrypted, 262_144), _NotCancelled()
    )
    assert prepared.chunk_count == 2
    await service.decrypt_download(
        DecryptAttachmentCommand(
            encrypted,
            output,
            prepared.file_key,
            prepared.nonce_prefix,
            prepared.chunk_size,
            prepared.plaintext_size,
            prepared.plaintext_sha256,
        ),
        _NotCancelled(),
    )
    assert output.read_bytes() == source.read_bytes()
    cancelled_output = tmp_path / "cancelled.bin"
    with pytest.raises(RuntimeError, match="cancelled"):
        await service.encrypt_file(
            PrepareAttachmentCommand(source, cancelled_output, 262_144), _Cancelled()
        )
    assert not cancelled_output.exists()
