"""Encrypted-attachment repository protocol."""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from bluebubbles.server.domain.attachments import (
    Attachment,
    AttachmentRecipientKey,
    UploadSession,
)
from bluebubbles.server.repositories.types import StoredAttachmentChunk


class AttachmentRepository(Protocol):
    """Define encrypted attachment metadata and upload persistence."""

    async def create_pending(self, attachment: Attachment) -> Attachment: ...

    async def create_attachment(self, attachment: Attachment) -> Attachment: ...

    async def create_upload_session(self, session: UploadSession) -> UploadSession: ...

    async def get_upload_session(
        self, upload_id: UUID, *, for_update: bool = False
    ) -> UploadSession | None: ...

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
    ) -> None: ...

    async def list_upload_chunks(
        self, upload_id: UUID
    ) -> list[StoredAttachmentChunk]: ...

    async def cancel_upload_session(
        self, upload_id: UUID, cancelled_at: datetime
    ) -> bool: ...

    async def get_by_id(self, attachment_id: UUID) -> Attachment | None: ...

    async def get_for_user(
        self, attachment_id: UUID, user_id: UUID
    ) -> Attachment | None: ...

    async def add_chunk(self, chunk: StoredAttachmentChunk) -> None: ...

    async def add_chunks(self, chunks: Sequence[StoredAttachmentChunk]) -> None: ...

    async def list_chunks(self, attachment_id: UUID) -> list[StoredAttachmentChunk]: ...

    async def add_recipient_keys(
        self, keys: Sequence[AttachmentRecipientKey]
    ) -> None: ...

    async def get_recipient_key(
        self, attachment_id: UUID, recipient_id: UUID
    ) -> AttachmentRecipientKey | None: ...

    async def mark_complete(
        self, attachment_id: UUID, completed_at: datetime, *, expected_version: int
    ) -> bool: ...

    async def set_storage_reference(
        self, attachment_id: UUID, storage_reference: str
    ) -> None: ...

    async def link_to_message(
        self, attachment_ids: Sequence[UUID], message_id: UUID
    ) -> None: ...

    async def mark_deleted(
        self, attachment_id: UUID, deleted_at: datetime, *, expected_version: int
    ) -> bool: ...

    async def list_expired_orphans(
        self, before: datetime, *, limit: int
    ) -> list[Attachment]: ...
