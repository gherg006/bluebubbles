"""Async SQLAlchemy encrypted-attachment repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bluebubbles.server.database.models.attachments import (
    AttachmentChunkORM,
    AttachmentORM,
    AttachmentRecipientKeyORM,
    UploadSessionChunkORM,
    UploadSessionORM,
)
from bluebubbles.server.domain.attachments import (
    Attachment,
    AttachmentRecipientKey,
    UploadSession,
)
from bluebubbles.server.repositories.mapping.attachments import AttachmentMapper
from bluebubbles.server.repositories.sqlalchemy._common import (
    flush_changes,
    require_aware,
)
from bluebubbles.server.repositories.types import StoredAttachmentChunk
from bluebubbles.shared.errors.exceptions import ConflictError
from bluebubbles.shared.models.attachments import AttachmentStatus


class SqlAlchemyAttachmentRepository:
    """Persist encrypted attachment metadata, never physical file contents."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_pending(self, attachment: Attachment) -> Attachment:
        """Stage initial attachment metadata and recipient key envelopes."""
        return await self.create_attachment(attachment)

    async def create_attachment(self, attachment: Attachment) -> Attachment:
        """Stage initial attachment metadata and recipient key envelopes."""
        self._session.add(AttachmentMapper.to_orm(attachment))
        self._session.add_all(
            [AttachmentMapper.key_to_orm(key) for key in attachment.recipient_keys]
        )
        await flush_changes(self._session)
        return attachment

    async def create_upload_session(self, session: UploadSession) -> UploadSession:
        """Stage recoverable upload progress for an existing attachment."""
        if session.received_chunks:
            raise ValueError(
                "New upload sessions cannot contain unverified received chunks"
            )
        attachment = await self._session.get(AttachmentORM, session.attachment_id)
        if attachment is None:
            raise ValueError("Attachment must exist before its upload session")
        self._session.add(
            UploadSessionORM(
                id=session.id,
                attachment_id=session.attachment_id,
                user_id=session.uploader_id,
                conversation_id=attachment.conversation_id,
                expected_encrypted_size=session.total_size,
                expected_chunk_count=session.expected_chunk_count,
                chunk_size=session.chunk_size,
                received_encrypted_size=sum(session.received_chunks.values()),
                status=(
                    AttachmentStatus.COMPLETE.value
                    if session.completed_at is not None
                    else AttachmentStatus.UPLOADING.value
                ),
                expires_at=session.expires_at,
                completed_at=session.completed_at,
                created_at=session.created_at,
                updated_at=session.updated_at,
            )
        )
        await flush_changes(self._session)
        return session

    async def get_upload_session(
        self, upload_id: UUID, *, for_update: bool = False
    ) -> UploadSession | None:
        """Return recoverable upload progress, optionally row-locked."""
        statement = select(UploadSessionORM).where(UploadSessionORM.id == upload_id)
        if for_update:
            statement = statement.with_for_update()
        record = (await self._session.execute(statement)).scalar_one_or_none()
        if record is None:
            return None
        chunk_statement = select(UploadSessionChunkORM).where(
            UploadSessionChunkORM.upload_session_id == upload_id
        )
        chunks = (await self._session.scalars(chunk_statement)).all()
        received = {item.chunk_index: item.encrypted_size for item in chunks}
        return AttachmentMapper.upload_to_domain(record, received)

    async def get_by_id(self, attachment_id: UUID) -> Attachment | None:
        """Return one non-deleted attachment and its recipient key envelopes."""
        statement = select(AttachmentORM).where(
            AttachmentORM.id == attachment_id, AttachmentORM.deleted_at.is_(None)
        )
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return await self._map_record(record) if record is not None else None

    async def get_for_user(
        self, attachment_id: UUID, user_id: UUID
    ) -> Attachment | None:
        """Return metadata only where a recipient file-key envelope exists."""
        statement = (
            select(AttachmentORM)
            .join(
                AttachmentRecipientKeyORM,
                AttachmentRecipientKeyORM.attachment_id == AttachmentORM.id,
            )
            .where(
                AttachmentORM.id == attachment_id,
                AttachmentORM.deleted_at.is_(None),
                AttachmentRecipientKeyORM.recipient_user_id == user_id,
            )
        )
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return await self._map_record(record) if record is not None else None

    async def add_chunk(self, chunk: StoredAttachmentChunk) -> None:
        """Stage and flush one complete encrypted chunk metadata record."""
        await self.add_chunks((chunk,))

    async def add_chunks(
        self, chunks: tuple[StoredAttachmentChunk, ...] | list[StoredAttachmentChunk]
    ) -> None:
        """Stage and flush complete encrypted chunk metadata records."""
        self._session.add_all(
            [
                AttachmentChunkORM(
                    id=item.id,
                    created_at=item.created_at,
                    attachment_id=item.attachment_id,
                    chunk_index=item.index,
                    encrypted_size=item.encrypted_size,
                    encrypted_checksum=item.encrypted_checksum,
                    nonce=item.nonce,
                    authentication_tag=item.authentication_tag,
                    storage_reference=item.storage_reference,
                )
                for item in chunks
            ]
        )
        await flush_changes(self._session)

    async def list_chunks(self, attachment_id: UUID) -> list[StoredAttachmentChunk]:
        """Return encrypted chunk metadata in deterministic index order."""
        statement = (
            select(AttachmentChunkORM)
            .where(AttachmentChunkORM.attachment_id == attachment_id)
            .order_by(AttachmentChunkORM.chunk_index)
        )
        return [
            StoredAttachmentChunk(
                id=item.id,
                attachment_id=item.attachment_id,
                index=item.chunk_index,
                encrypted_size=item.encrypted_size,
                encrypted_checksum=item.encrypted_checksum,
                nonce=item.nonce,
                authentication_tag=item.authentication_tag,
                storage_reference=item.storage_reference,
                created_at=item.created_at,
            )
            for item in (await self._session.scalars(statement)).all()
        ]

    async def add_recipient_keys(
        self,
        keys: tuple[AttachmentRecipientKey, ...] | list[AttachmentRecipientKey],
    ) -> None:
        """Stage and flush unique recipient file-key envelopes."""
        self._session.add_all([AttachmentMapper.key_to_orm(key) for key in keys])
        await flush_changes(self._session)

    async def get_recipient_key(
        self, attachment_id: UUID, recipient_id: UUID
    ) -> AttachmentRecipientKey | None:
        """Return exactly one recipient file-key envelope."""
        statement = select(AttachmentRecipientKeyORM).where(
            AttachmentRecipientKeyORM.attachment_id == attachment_id,
            AttachmentRecipientKeyORM.recipient_user_id == recipient_id,
        )
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return AttachmentMapper.key_to_domain(record) if record is not None else None

    async def mark_complete(
        self, attachment_id: UUID, completed_at: datetime, *, expected_version: int
    ) -> bool:
        """Mark complete metadata after storage has durably finalized all bytes."""
        require_aware(completed_at, "completed_at")
        result = await self._session.execute(
            update(AttachmentORM)
            .where(
                AttachmentORM.id == attachment_id,
                AttachmentORM.deleted_at.is_(None),
                AttachmentORM.version == expected_version,
                AttachmentORM.status.in_(
                    [
                        AttachmentStatus.INITIALISED.value,
                        AttachmentStatus.UPLOADING.value,
                    ]
                ),
            )
            .values(
                status=AttachmentStatus.COMPLETE.value,
                completed_at=completed_at,
                version=expected_version + 1,
            )
        )
        if result.rowcount == 1:
            await self._session.execute(
                update(UploadSessionORM)
                .where(UploadSessionORM.attachment_id == attachment_id)
                .values(
                    status=AttachmentStatus.COMPLETE.value,
                    completed_at=completed_at,
                    updated_at=completed_at,
                )
            )
            return True
        return False

    async def link_to_message(
        self, attachment_ids: tuple[UUID, ...] | list[UUID], message_id: UUID
    ) -> None:
        """Link complete, currently unlinked attachments to one message."""
        if not attachment_ids:
            return
        if len(set(attachment_ids)) != len(attachment_ids):
            raise ValueError("Attachment identifiers must be unique")
        result = await self._session.execute(
            update(AttachmentORM)
            .where(
                AttachmentORM.id.in_(attachment_ids),
                AttachmentORM.deleted_at.is_(None),
                AttachmentORM.message_id.is_(None),
                AttachmentORM.status == AttachmentStatus.COMPLETE.value,
            )
            .values(message_id=message_id)
        )
        if result.rowcount != len(attachment_ids):
            raise ConflictError(
                user_message="One or more attachments cannot be linked."
            )

    async def mark_deleted(
        self, attachment_id: UUID, deleted_at: datetime, *, expected_version: int
    ) -> bool:
        """Soft-delete attachment metadata after storage deletion coordination."""
        require_aware(deleted_at, "deleted_at")
        result = await self._session.execute(
            update(AttachmentORM)
            .where(
                AttachmentORM.id == attachment_id,
                AttachmentORM.deleted_at.is_(None),
                AttachmentORM.version == expected_version,
            )
            .values(
                deleted_at=deleted_at,
                status=AttachmentStatus.DELETED.value,
                version=expected_version + 1,
            )
        )
        return result.rowcount == 1

    async def list_expired_orphans(
        self, before: datetime, *, limit: int
    ) -> list[Attachment]:
        """Return a bounded batch of old unlinked attachment metadata."""
        require_aware(before, "before")
        if limit < 1:
            raise ValueError("Cleanup limit must be positive")
        statement = (
            select(AttachmentORM)
            .where(
                AttachmentORM.message_id.is_(None),
                AttachmentORM.deleted_at.is_(None),
                AttachmentORM.created_at < before,
            )
            .order_by(AttachmentORM.created_at, AttachmentORM.id)
            .limit(limit)
        )
        records = list((await self._session.scalars(statement)).all())
        return [await self._map_record(record) for record in records]

    async def _map_record(self, record: AttachmentORM) -> Attachment:
        statement = select(AttachmentRecipientKeyORM).where(
            AttachmentRecipientKeyORM.attachment_id == record.id
        )
        keys = tuple((await self._session.scalars(statement)).all())
        return AttachmentMapper.to_domain(record, keys)
