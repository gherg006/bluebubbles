"""Authorised resumable encrypted-attachment transfer use cases."""

from __future__ import annotations

import base64
import binascii
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from bluebubbles.server.configuration.settings import (
    AttachmentSettings,
    StorageSettings,
)
from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.attachments import (
    Attachment,
    AttachmentRecipientKey,
    UploadSession,
)
from bluebubbles.server.domain.audit import AuditSeverity
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission
from bluebubbles.server.repositories.types import StoredAttachmentChunk
from bluebubbles.server.services.audit import AuthenticationAuditWriter
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.server.storage import ChecksumService, FileStorage
from bluebubbles.shared.errors.exceptions import (
    ConflictError,
    ResourceNotFoundError,
    StorageError,
    ValidationError,
)
from bluebubbles.shared.models.attachments import (
    AttachmentRecipientKeyResponse,
    AttachmentResponse,
    AttachmentStatus,
    AuthorisedAttachmentResponse,
    InitialiseUploadRequest,
    InitialiseUploadResponse,
    UploadChunkResponse,
    UploadStatusResponse,
)
from bluebubbles.shared.security.algorithms import KeyEnvelopeAlgorithm


@dataclass(frozen=True, slots=True)
class IncomingEncryptedChunk:
    """Carry one bounded ciphertext body and its authenticated metadata."""

    data: bytes
    checksum: bytes
    nonce: bytes
    authentication_tag: bytes


@dataclass(frozen=True, slots=True)
class DownloadChunk:
    """Return a ciphertext stream plus verified server metadata."""

    stream: AsyncIterator[bytes]
    metadata: StoredAttachmentChunk
    total_chunks: int


class AttachmentService:
    """Coordinate permissions, storage, and attachment database transactions."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        file_storage: FileStorage,
        checksum_service: ChecksumService,
        audit_writer: AuthenticationAuditWriter,
        settings: AttachmentSettings,
        storage_settings: StorageSettings,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._permissions = permission_service
        self._storage = file_storage
        self._checksums = checksum_service
        self._audit = audit_writer
        self._settings = settings
        self._storage_settings = storage_settings

    async def initialise_upload(
        self, uploader: AuthenticatedUser, request: InitialiseUploadRequest
    ) -> InitialiseUploadResponse:
        await self._permissions.require_authenticated_permission(
            uploader, Permission.UPLOAD_FILE
        )
        chunk_count = (
            request.chunk_count
            or (request.encrypted_size + request.chunk_size - 1) // request.chunk_size
        )
        self._validate_declarations(request, chunk_count)
        free_bytes = await self._storage.get_free_bytes()
        if (
            free_bytes - request.encrypted_size
            < self._storage_settings.reserved_free_bytes
        ):
            raise StorageError(
                user_message=(
                    "The server does not currently have enough storage for this file."
                )
            )
        now = datetime.now(UTC)
        upload_id = uuid4()
        await self._storage.create_upload_area(upload_id)
        try:
            async with self._unit_of_work_factory() as uow:
                if await uow.attachments.get_by_id(request.attachment_id) is not None:
                    raise ConflictError(
                        user_message="The attachment identifier is already in use."
                    )
                conversation = await uow.conversations.get_by_id(
                    request.conversation_id
                )
                members = await uow.conversations.get_active_members(
                    request.conversation_id
                )
                active_ids = {member.user_id for member in members if member.active}
                if conversation is None or uploader.user_id not in active_ids:
                    raise ResourceNotFoundError()
                supplied_ids = {item.recipient_id for item in request.recipient_keys}
                if supplied_ids != active_ids or len(supplied_ids) != len(
                    request.recipient_keys
                ):
                    raise ValidationError(
                        user_message=(
                            "Attachment keys must cover every active participant."
                        )
                    )
                keys = tuple(
                    self._recipient_key(request.attachment_id, item, now)
                    for item in request.recipient_keys
                )
                attachment = Attachment(
                    id=request.attachment_id,
                    created_at=now,
                    updated_at=now,
                    conversation_id=request.conversation_id,
                    uploaded_by=uploader.user_id,
                    filename=request.filename,
                    media_type=request.media_type,
                    encrypted_size=request.encrypted_size,
                    original_size=request.original_size,
                    content_algorithm=request.content_algorithm,
                    hash_algorithm=request.hash_algorithm,
                    encrypted_checksum=self._decode(request.encrypted_checksum),
                    storage_reference=f"pending:{upload_id}",
                    chunk_size=request.chunk_size,
                    recipient_keys=keys,
                    encrypted_metadata=(
                        self._decode(request.encrypted_metadata)
                        if request.encrypted_metadata
                        else None
                    ),
                    metadata_nonce=(
                        self._decode(request.metadata_nonce)
                        if request.metadata_nonce
                        else None
                    ),
                    metadata_authentication_tag=(
                        self._decode(request.metadata_authentication_tag)
                        if request.metadata_authentication_tag
                        else None
                    ),
                )
                await uow.attachments.create_pending(attachment)
                session = UploadSession(
                    id=upload_id,
                    created_at=now,
                    updated_at=now,
                    attachment_id=attachment.id,
                    uploader_id=uploader.user_id,
                    chunk_size=request.chunk_size,
                    total_size=request.encrypted_size,
                    expires_at=now
                    + timedelta(seconds=self._settings.upload_session_lifetime_seconds),
                )
                if session.expected_chunk_count != chunk_count:
                    raise ValidationError(
                        user_message="The declared chunk count is invalid."
                    )
                await uow.attachments.create_upload_session(session)
                await self._audit.append(
                    uow.audit,
                    event_type="attachment_upload_initialised",
                    occurred_at=now,
                    actor_id=uploader.user_id,
                    source_ip=None,
                    severity=AuditSeverity.INFORMATIONAL,
                    details={
                        "attachment_id": str(attachment.id),
                        "conversation_id": str(attachment.conversation_id),
                        "encrypted_size": attachment.encrypted_size,
                    },
                )
                await uow.commit()
        except BaseException:
            await self._storage.delete_upload(upload_id)
            raise
        return InitialiseUploadResponse(
            attachment_id=request.attachment_id,
            upload_id=upload_id,
            chunk_size=request.chunk_size,
            expected_chunk_count=chunk_count,
            expires_at=session.expires_at,
        )

    async def get_upload_status(
        self, uploader: AuthenticatedUser, upload_id: UUID
    ) -> UploadStatusResponse:
        async with self._unit_of_work_factory() as uow:
            session = await uow.attachments.get_upload_session(upload_id)
        self._require_owned_active(session, uploader.user_id, allow_complete=True)
        assert session is not None
        received = tuple(sorted(session.received_chunks))
        missing = tuple(
            index
            for index in range(session.expected_chunk_count)
            if index not in session.received_chunks
        )
        status = (
            AttachmentStatus.COMPLETE
            if session.completed_at
            else (
                AttachmentStatus.EXPIRED
                if session.is_expired(datetime.now(UTC))
                else AttachmentStatus.UPLOADING
            )
        )
        return UploadStatusResponse(
            upload_id=upload_id,
            attachment_id=session.attachment_id,
            status=status,
            received_bytes=sum(session.received_chunks.values()),
            total_bytes=session.total_size,
            received_chunks=received,
            missing_chunks=missing,
            expires_at=session.expires_at,
        )

    async def upload_chunk(
        self,
        uploader: AuthenticatedUser,
        upload_id: UUID,
        chunk_index: int,
        chunk: IncomingEncryptedChunk,
    ) -> UploadChunkResponse:
        if not self._checksums.verify(
            chunk.checksum, self._checksums.digest(chunk.data)
        ):
            raise ValidationError(
                user_message="The encrypted chunk checksum is invalid."
            )
        if len(chunk.nonce) != 12 or len(chunk.authentication_tag) != 16:
            raise ValidationError(
                user_message="The encrypted chunk metadata is invalid."
            )
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as uow:
            session = await uow.attachments.get_upload_session(
                upload_id, for_update=True
            )
            self._require_owned_active(session, uploader.user_id)
            assert session is not None
            existing_size = session.received_chunks.get(chunk_index)
            temporary_chunks = await uow.attachments.list_upload_chunks(upload_id)
            existing = next(
                (item for item in temporary_chunks if item.index == chunk_index), None
            )
            if existing_size is not None:
                if (
                    existing is None
                    or existing_size != len(chunk.data)
                    or existing.encrypted_checksum
                    != base64.b64encode(chunk.checksum).decode("ascii")
                    or existing.nonce != chunk.nonce
                    or existing.authentication_tag != chunk.authentication_tag
                ):
                    raise ConflictError(
                        user_message="The upload chunk conflicts with stored data."
                    )
            elif not session.can_accept_chunk(chunk_index, len(chunk.data), now):
                raise ValidationError(
                    user_message="The encrypted chunk size or index is invalid."
                )
            if existing_size is None:
                stored = await self._storage.write_chunk(
                    upload_id, chunk_index, chunk.data
                )
                if not self._checksums.verify(chunk.checksum, stored.checksum):
                    raise ValidationError(
                        user_message="The stored chunk checksum is invalid."
                    )
                await uow.attachments.record_upload_chunk(
                    upload_id,
                    chunk_index=chunk_index,
                    encrypted_size=stored.size,
                    encrypted_checksum=base64.b64encode(stored.checksum).decode(
                        "ascii"
                    ),
                    nonce=chunk.nonce,
                    authentication_tag=chunk.authentication_tag,
                    received_at=now,
                )
                session.accept_chunk(chunk_index, stored.size, now)
            await uow.commit()
        total = sum(session.received_chunks.values())
        return UploadChunkResponse(
            upload_id=upload_id,
            chunk_index=chunk_index,
            received_bytes=len(chunk.data),
            total_received_bytes=total,
            received_chunk_count=len(session.received_chunks),
            expected_chunk_count=session.expected_chunk_count,
            is_complete=session.is_complete(),
        )

    async def complete_upload(
        self, uploader: AuthenticatedUser, upload_id: UUID
    ) -> AttachmentResponse:
        now = datetime.now(UTC)
        finalised_attachment_id: UUID | None = None
        try:
            async with self._unit_of_work_factory() as uow:
                session = await uow.attachments.get_upload_session(
                    upload_id, for_update=True
                )
                self._require_owned_active(session, uploader.user_id)
                assert session is not None
                if not session.is_complete():
                    raise ValidationError(user_message="The upload is incomplete.")
                attachment = await uow.attachments.get_by_id(session.attachment_id)
                if attachment is None:
                    raise ResourceNotFoundError()
                temporary_chunks = await uow.attachments.list_upload_chunks(upload_id)
                if len(temporary_chunks) != session.expected_chunk_count:
                    raise ValidationError(
                        user_message="The upload metadata is incomplete."
                    )
                digest = await self._checksums.hash_stream(
                    self._ordered_upload_stream(session, temporary_chunks)
                )
                if not self._checksums.verify(attachment.encrypted_checksum, digest):
                    raise ValidationError(
                        user_message="The encrypted attachment checksum is invalid."
                    )
                reference = await self._storage.finalise_upload(
                    upload_id, attachment.id
                )
                finalised_attachment_id = attachment.id
                chunk_records: list[StoredAttachmentChunk] = []
                for item in temporary_chunks:
                    index = item.index
                    path_reference = f"{reference}/{index:08d}.chunk"
                    chunk_records.append(
                        StoredAttachmentChunk(
                            id=uuid4(),
                            attachment_id=attachment.id,
                            index=index,
                            encrypted_size=item.encrypted_size,
                            encrypted_checksum=item.encrypted_checksum,
                            nonce=item.nonce,
                            authentication_tag=item.authentication_tag,
                            storage_reference=path_reference,
                            created_at=now,
                        )
                    )
                await uow.attachments.add_chunks(chunk_records)
                await uow.attachments.set_storage_reference(attachment.id, reference)
                if not await uow.attachments.mark_complete(
                    attachment.id, now, expected_version=attachment.version
                ):
                    raise ConflictError(
                        user_message="The attachment changed during finalisation."
                    )
                await self._audit.append(
                    uow.audit,
                    event_type="attachment_upload_completed",
                    occurred_at=now,
                    actor_id=uploader.user_id,
                    source_ip=None,
                    severity=AuditSeverity.INFORMATIONAL,
                    details={
                        "attachment_id": str(attachment.id),
                        "conversation_id": str(attachment.conversation_id),
                        "chunk_count": session.expected_chunk_count,
                    },
                )
                await uow.commit()
        except BaseException:
            if finalised_attachment_id is not None:
                await self._storage.delete_attachment(finalised_attachment_id)
            raise
        attachment.status = AttachmentStatus.COMPLETE
        return self._response(attachment)

    async def get_authorised_attachment(
        self, requester: AuthenticatedUser, attachment_id: UUID
    ) -> AuthorisedAttachmentResponse:
        await self._permissions.require_authenticated_permission(
            requester, Permission.DOWNLOAD_FILE
        )
        async with self._unit_of_work_factory() as uow:
            attachment = await uow.attachments.get_for_user(
                attachment_id, requester.user_id
            )
            if (
                attachment is None
                or attachment.status is not AttachmentStatus.COMPLETE
                or attachment.linked_message_id is None
            ):
                raise ResourceNotFoundError()
            membership = await uow.conversations.get_active_membership(
                attachment.conversation_id, requester.user_id
            )
            key = await uow.attachments.get_recipient_key(
                attachment.id, requester.user_id
            )
        if membership is None or key is None:
            raise ResourceNotFoundError()
        response = self._response(attachment)
        return AuthorisedAttachmentResponse(
            **response.model_dump(),
            download_url=f"/api/v1/attachments/{attachment.id}/chunks/{{chunk_index}}",
            recipient_key=AttachmentRecipientKeyResponse(
                attachment_id=attachment.id,
                recipient_id=key.recipient_id,
                key_version=key.key_version,
                encrypted_key=base64.b64encode(key.encrypted_key).decode("ascii"),
                algorithm=key.algorithm.value,
                ephemeral_public_key=base64.b64encode(key.ephemeral_public_key).decode(
                    "ascii"
                ),
                nonce=base64.b64encode(key.nonce).decode("ascii"),
            ),
            encrypted_metadata=(
                base64.b64encode(attachment.encrypted_metadata).decode("ascii")
                if attachment.encrypted_metadata
                else None
            ),
            metadata_nonce=(
                base64.b64encode(attachment.metadata_nonce).decode("ascii")
                if attachment.metadata_nonce
                else None
            ),
            metadata_authentication_tag=(
                base64.b64encode(attachment.metadata_authentication_tag).decode("ascii")
                if attachment.metadata_authentication_tag
                else None
            ),
        )

    async def download_chunk(
        self, requester: AuthenticatedUser, attachment_id: UUID, chunk_index: int
    ) -> DownloadChunk:
        await self.get_authorised_attachment(requester, attachment_id)
        async with self._unit_of_work_factory() as uow:
            chunks = await uow.attachments.list_chunks(attachment_id)
        selected = next((item for item in chunks if item.index == chunk_index), None)
        if selected is None:
            raise ResourceNotFoundError()
        return DownloadChunk(
            self._storage.read_attachment_chunk(attachment_id, chunk_index),
            selected,
            len(chunks),
        )

    async def cancel_upload(self, uploader: AuthenticatedUser, upload_id: UUID) -> None:
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as uow:
            session = await uow.attachments.get_upload_session(
                upload_id, for_update=True
            )
            self._require_owned_active(session, uploader.user_id)
            if not await uow.attachments.cancel_upload_session(upload_id, now):
                raise ConflictError(user_message="The upload cannot be cancelled.")
            await uow.commit()
        await self._storage.delete_upload(upload_id)

    async def _ordered_upload_stream(
        self,
        session: UploadSession,
        chunks: list[StoredAttachmentChunk],
    ) -> AsyncIterator[bytes]:
        by_index = {item.index: item for item in chunks}
        for index in range(session.expected_chunk_count):
            metadata = by_index[index]
            yield metadata.nonce
            async for block in self._storage.read_upload_chunk(session.id, index):
                yield block
            yield metadata.authentication_tag

    def _validate_declarations(
        self, request: InitialiseUploadRequest, chunk_count: int
    ) -> None:
        if request.original_size > self._settings.maximum_plaintext_size_bytes:
            raise ValidationError(user_message="The selected file is too large.")
        if (
            not self._settings.minimum_chunk_size_bytes
            <= request.chunk_size
            <= self._settings.maximum_chunk_size_bytes
        ):
            raise ValidationError(
                user_message="The encrypted chunk size is outside server policy."
            )
        if chunk_count < 1 or chunk_count > 1_000_000:
            raise ValidationError(user_message="The declared chunk count is invalid.")
        if Path(request.filename).suffix.casefold() in {
            value.casefold() for value in self._settings.blocked_extensions
        }:
            raise ValidationError(
                user_message="This file type is blocked by server policy."
            )

    @staticmethod
    def _require_owned_active(
        session: UploadSession | None, user_id: UUID, *, allow_complete: bool = False
    ) -> None:
        if session is None or session.uploader_id != user_id:
            raise ResourceNotFoundError()
        if session.is_expired(datetime.now(UTC)):
            raise ConflictError(user_message="The upload session has expired.")
        if session.status in {
            AttachmentStatus.CANCELLED,
            AttachmentStatus.EXPIRED,
            AttachmentStatus.FAILED,
        }:
            raise ConflictError(user_message="The upload session is not active.")
        if session.completed_at is not None and not allow_complete:
            raise ConflictError(user_message="The upload session is already complete.")

    @staticmethod
    def _decode(value: str) -> bytes:
        try:
            return base64.b64decode(value.encode("ascii"), validate=True)
        except (ValueError, UnicodeError, binascii.Error) as error:
            raise ValidationError(
                user_message="Encrypted attachment metadata is invalid."
            ) from error

    @classmethod
    def _recipient_key(
        cls, attachment_id: UUID, request: object, now: datetime
    ) -> AttachmentRecipientKey:
        from bluebubbles.shared.models.attachments import AttachmentRecipientKeyRequest

        if (
            not isinstance(request, AttachmentRecipientKeyRequest)
            or not request.ephemeral_public_key
            or not request.nonce
        ):
            raise ValidationError(
                user_message="Attachment key envelope metadata is incomplete."
            )
        try:
            algorithm = (
                KeyEnvelopeAlgorithm(request.algorithm)
                if request.algorithm
                else KeyEnvelopeAlgorithm.X25519_HKDF_SHA256_AES_256_GCM_V1
            )
        except ValueError as error:
            raise ValidationError(
                user_message="Attachment key envelope algorithm is unsupported."
            ) from error
        return AttachmentRecipientKey(
            id=uuid4(),
            created_at=now,
            updated_at=now,
            attachment_id=attachment_id,
            recipient_id=request.recipient_id,
            key_version=request.key_version,
            encrypted_key=cls._decode(request.encrypted_key),
            algorithm=algorithm,
            ephemeral_public_key=cls._decode(request.ephemeral_public_key),
            nonce=cls._decode(request.nonce),
        )

    @staticmethod
    def _response(attachment: Attachment) -> AttachmentResponse:
        return AttachmentResponse(
            id=attachment.id,
            conversation_id=attachment.conversation_id,
            uploaded_by=attachment.uploaded_by,
            filename=attachment.filename,
            media_type=attachment.media_type,
            encrypted_size=attachment.encrypted_size,
            original_size=attachment.original_size,
            chunk_count=attachment.chunk_count,
            status=attachment.status,
            created_at=attachment.created_at,
        )
