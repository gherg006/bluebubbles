"""Task 15 server attachment service integration with in-memory persistence."""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from bluebubbles.client.security.attachment_crypto import (
    AttachmentCryptoContext,
    AttachmentEncryptionService,
    AuthenticatedAttachmentChunk,
)
from bluebubbles.server.configuration.settings import (
    AttachmentSettings,
    StorageSettings,
)
from bluebubbles.server.domain.attachments import (
    Attachment,
    AttachmentRecipientKey,
    UploadSession,
)
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.repositories.types import StoredAttachmentChunk
from bluebubbles.server.services.attachments import (
    AttachmentService,
    IncomingEncryptedChunk,
)
from bluebubbles.server.storage import (
    AttachmentPathBuilder,
    ChecksumService,
    LocalFileStorage,
)
from bluebubbles.shared.errors.exceptions import (
    ConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from bluebubbles.shared.models.attachments import (
    AttachmentRecipientKeyRequest,
    AttachmentStatus,
    InitialiseUploadRequest,
)
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    HashAlgorithm,
)


def encoded(value: bytes) -> str:
    """Encode binary contract material."""
    return base64.b64encode(value).decode("ascii")


class Attachments:
    """Persist enough attachment state to exercise application coordination."""

    def __init__(self) -> None:
        self.items: dict[UUID, Attachment] = {}
        self.sessions: dict[UUID, UploadSession] = {}
        self.upload_chunks: dict[UUID, list[StoredAttachmentChunk]] = {}
        self.chunks: dict[UUID, list[StoredAttachmentChunk]] = {}

    async def get_by_id(self, attachment_id: UUID) -> Attachment | None:
        return self.items.get(attachment_id)

    async def create_pending(self, attachment: Attachment) -> Attachment:
        self.items[attachment.id] = attachment
        return attachment

    async def create_upload_session(self, session: UploadSession) -> UploadSession:
        self.sessions[session.id] = session
        return session

    async def get_upload_session(
        self, upload_id: UUID, *, for_update: bool = False
    ) -> UploadSession | None:
        del for_update
        return self.sessions.get(upload_id)

    async def list_upload_chunks(self, upload_id: UUID) -> list[StoredAttachmentChunk]:
        return self.upload_chunks.get(upload_id, [])

    async def record_upload_chunk(
        self,
        upload_id: UUID,
        *,
        chunk_index: int,
        encrypted_size: int,
        encrypted_checksum: str,
        nonce: bytes,
        authentication_tag: bytes,
        received_at: datetime,
    ) -> None:
        session = self.sessions[upload_id]
        self.upload_chunks.setdefault(upload_id, []).append(
            StoredAttachmentChunk(
                uuid4(),
                session.attachment_id,
                chunk_index,
                encrypted_size,
                encrypted_checksum,
                nonce,
                authentication_tag,
                f"pending:{upload_id}:{chunk_index}",
                received_at,
            )
        )

    async def add_chunks(self, chunks: list[StoredAttachmentChunk]) -> None:
        for chunk in chunks:
            self.chunks.setdefault(chunk.attachment_id, []).append(chunk)

    async def set_storage_reference(
        self, attachment_id: UUID, storage_reference: str
    ) -> None:
        self.items[attachment_id].storage_reference = storage_reference

    async def mark_complete(
        self, attachment_id: UUID, completed_at: datetime, *, expected_version: int
    ) -> bool:
        attachment = self.items[attachment_id]
        if attachment.version != expected_version:
            return False
        attachment.status = AttachmentStatus.COMPLETE
        session = next(
            item
            for item in self.sessions.values()
            if item.attachment_id == attachment_id
        )
        session.completed_at = completed_at
        return True

    async def get_for_user(
        self, attachment_id: UUID, user_id: UUID
    ) -> Attachment | None:
        attachment = self.items.get(attachment_id)
        if attachment and any(
            key.recipient_id == user_id for key in attachment.recipient_keys
        ):
            return attachment
        return None

    async def get_recipient_key(
        self, attachment_id: UUID, recipient_id: UUID
    ) -> AttachmentRecipientKey | None:
        attachment = self.items.get(attachment_id)
        if attachment is None:
            return None
        return next(
            (
                key
                for key in attachment.recipient_keys
                if key.recipient_id == recipient_id
            ),
            None,
        )

    async def list_chunks(self, attachment_id: UUID) -> list[StoredAttachmentChunk]:
        return sorted(self.chunks.get(attachment_id, []), key=lambda item: item.index)

    async def cancel_upload_session(
        self, upload_id: UUID, cancelled_at: datetime
    ) -> bool:
        session = self.sessions[upload_id]
        if session.completed_at is not None:
            return False
        session.status = AttachmentStatus.CANCELLED
        session.updated_at = cancelled_at
        return True


@dataclass(frozen=True, slots=True)
class Member:
    """Represent the membership fields consumed by the service."""

    user_id: UUID
    active: bool = True


class Conversations:
    """Return one fixed conversation membership set."""

    def __init__(self, conversation_id: UUID, users: tuple[UUID, ...]) -> None:
        self.conversation_id = conversation_id
        self.members = [Member(user) for user in users]

    async def get_by_id(self, conversation_id: UUID) -> object | None:
        return object() if conversation_id == self.conversation_id else None

    async def get_active_members(self, conversation_id: UUID) -> list[Member]:
        return self.members if conversation_id == self.conversation_id else []

    async def get_active_membership(
        self, conversation_id: UUID, user_id: UUID
    ) -> Member | None:
        return next(
            (
                member
                for member in self.members
                if conversation_id == self.conversation_id and member.user_id == user_id
            ),
            None,
        )


class UnitOfWork:
    """Expose shared in-memory repositories through fresh contexts."""

    def __init__(self, attachments: Attachments, conversations: Conversations) -> None:
        self.attachments = attachments
        self.conversations = conversations
        self.audit = object()
        self.commits = 0

    async def __aenter__(self) -> UnitOfWork:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1


class Factory:
    """Return transaction contexts over stable fake repositories."""

    def __init__(self, attachments: Attachments, conversations: Conversations) -> None:
        self.attachments = attachments
        self.conversations = conversations

    def __call__(self) -> UnitOfWork:
        return UnitOfWork(self.attachments, self.conversations)


class Permissions:
    """Record protected operations while granting the synthetic user."""

    def __init__(self) -> None:
        self.checked = 0

    async def require_authenticated_permission(self, *args: object) -> None:
        self.checked += 1


class Audit:
    """Collect safe event types without storing content."""

    def __init__(self) -> None:
        self.events: list[str] = []

    async def append(self, repository: object, **values: object) -> None:
        del repository
        self.events.append(str(values["event_type"]))


def request_for(
    attachment_id: UUID,
    conversation_id: UUID,
    users: tuple[UUID, ...],
    chunks: tuple[AuthenticatedAttachmentChunk, ...],
) -> InitialiseUploadRequest:
    """Build one upload declaration matching the client checksum contract."""
    digest = hashlib.sha256()
    for item in chunks:
        digest.update(item.nonce + item.ciphertext + item.authentication_tag)
    keys = tuple(
        AttachmentRecipientKeyRequest(
            recipient_id=user,
            key_version=1,
            encrypted_key=encoded(b"wrapped"),
            ephemeral_public_key=encoded(b"e" * 32),
            nonce=encoded(b"n" * 12),
        )
        for user in users
    )
    return InitialiseUploadRequest(
        attachment_id=attachment_id,
        conversation_id=conversation_id,
        filename="report.bin",
        media_type="application/octet-stream",
        encrypted_size=sum(len(item.ciphertext) for item in chunks),
        original_size=sum(item.plaintext_length for item in chunks),
        chunk_size=262_144,
        chunk_count=len(chunks),
        content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
        hash_algorithm=HashAlgorithm.SHA256_V1,
        encrypted_checksum=encoded(digest.digest()),
        recipient_keys=keys,
    )


@pytest.mark.asyncio
async def test_complete_resumable_upload_and_authorised_download(
    tmp_path: Path,
) -> None:
    (tmp_path / "stored").mkdir()
    (tmp_path / "temporary").mkdir()
    uploader_id, recipient_id = uuid4(), uuid4()
    users = (uploader_id, recipient_id)
    conversation_id, attachment_id = uuid4(), uuid4()
    crypto = AttachmentEncryptionService()
    key = crypto.generate_file_key()
    context = AttachmentCryptoContext(attachment_id, conversation_id, uploader_id, 2)
    chunks = (
        crypto.encrypt_chunk(key, context, 0, b"a" * 262_144),
        crypto.encrypt_chunk(key, context, 1, b"final"),
    )
    attachments = Attachments()
    conversations = Conversations(conversation_id, users)
    storage = LocalFileStorage(
        AttachmentPathBuilder(tmp_path / "stored", tmp_path / "temporary"),
        ChecksumService(),
    )
    audit = Audit()
    service = AttachmentService(
        Factory(attachments, conversations),  # type: ignore[arg-type]
        Permissions(),  # type: ignore[arg-type]
        storage,
        ChecksumService(),
        audit,  # type: ignore[arg-type]
        AttachmentSettings(
            maximum_plaintext_size_bytes=1_000_000,
            default_chunk_size_bytes=262_144,
            maximum_chunk_size_bytes=262_144,
        ),
        StorageSettings(
            root_path=tmp_path / "stored",
            temporary_path=tmp_path / "temporary",
            export_path=tmp_path / "exports",
            reserved_free_bytes=0,
        ),
    )
    uploader = AuthenticatedUser(uploader_id, uuid4(), "uploader", uuid4(), frozenset())
    initialised = await service.initialise_upload(
        uploader, request_for(attachment_id, conversation_id, users, chunks)
    )
    first = chunks[0]
    first_result = await service.upload_chunk(
        uploader,
        initialised.upload_id,
        0,
        IncomingEncryptedChunk(
            first.ciphertext,
            hashlib.sha256(first.ciphertext).digest(),
            first.nonce,
            first.authentication_tag,
        ),
    )
    assert not first_result.is_complete
    status = await service.get_upload_status(uploader, initialised.upload_id)
    assert status.missing_chunks == (1,)
    repeated = await service.upload_chunk(
        uploader,
        initialised.upload_id,
        0,
        IncomingEncryptedChunk(
            first.ciphertext,
            hashlib.sha256(first.ciphertext).digest(),
            first.nonce,
            first.authentication_tag,
        ),
    )
    assert repeated.received_chunk_count == 1
    second = chunks[1]
    await service.upload_chunk(
        uploader,
        initialised.upload_id,
        1,
        IncomingEncryptedChunk(
            second.ciphertext,
            hashlib.sha256(second.ciphertext).digest(),
            second.nonce,
            second.authentication_tag,
        ),
    )
    completed = await service.complete_upload(uploader, initialised.upload_id)
    assert completed.status is AttachmentStatus.COMPLETE
    attachments.items[attachment_id].linked_message_id = uuid4()
    recipient = AuthenticatedUser(
        recipient_id, uuid4(), "recipient", uuid4(), frozenset()
    )
    authorised = await service.get_authorised_attachment(recipient, attachment_id)
    assert authorised.recipient_key.recipient_id == recipient_id
    downloaded = await service.download_chunk(recipient, attachment_id, 1)
    assert b"".join([block async for block in downloaded.stream]) == second.ciphertext
    assert audit.events == [
        "attachment_upload_initialised",
        "attachment_upload_completed",
    ]


@pytest.mark.asyncio
async def test_upload_rejections_and_cancellation(tmp_path: Path) -> None:
    (tmp_path / "stored").mkdir()
    (tmp_path / "temporary").mkdir()
    user_id, conversation_id = uuid4(), uuid4()
    attachments = Attachments()
    service = AttachmentService(
        Factory(attachments, Conversations(conversation_id, (user_id,))),  # type: ignore[arg-type]
        Permissions(),  # type: ignore[arg-type]
        LocalFileStorage(
            AttachmentPathBuilder(tmp_path / "stored", tmp_path / "temporary"),
            ChecksumService(),
        ),
        ChecksumService(),
        Audit(),  # type: ignore[arg-type]
        AttachmentSettings(
            maximum_plaintext_size_bytes=1_000_000,
            default_chunk_size_bytes=262_144,
            maximum_chunk_size_bytes=262_144,
        ),
        StorageSettings(
            root_path=tmp_path / "stored",
            temporary_path=tmp_path / "temporary",
            export_path=tmp_path / "exports",
            reserved_free_bytes=0,
        ),
    )
    crypto = AttachmentEncryptionService()
    attachment_id = uuid4()
    chunk = crypto.encrypt_chunk(
        crypto.generate_file_key(),
        AttachmentCryptoContext(attachment_id, conversation_id, user_id, 1),
        0,
        b"x" * 262_144,
    )
    request = request_for(attachment_id, conversation_id, (user_id,), (chunk,))
    user = AuthenticatedUser(user_id, uuid4(), "user", uuid4(), frozenset())
    initialised = await service.initialise_upload(user, request)
    with pytest.raises(ValidationError):
        await service.complete_upload(user, initialised.upload_id)
    with pytest.raises(ValidationError):
        await service.upload_chunk(
            user,
            initialised.upload_id,
            0,
            IncomingEncryptedChunk(
                chunk.ciphertext, b"wrong", chunk.nonce, chunk.authentication_tag
            ),
        )
    await service.cancel_upload(user, initialised.upload_id)
    with pytest.raises(ConflictError):
        await service.upload_chunk(
            user,
            initialised.upload_id,
            0,
            IncomingEncryptedChunk(
                chunk.ciphertext,
                hashlib.sha256(chunk.ciphertext).digest(),
                chunk.nonce,
                chunk.authentication_tag,
            ),
        )
    with pytest.raises(ResourceNotFoundError):
        await service.get_upload_status(user, uuid4())
