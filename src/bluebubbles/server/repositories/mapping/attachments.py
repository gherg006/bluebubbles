"""Pure encrypted-attachment ORM/domain conversions."""

import base64

from bluebubbles.server.database.models.attachments import (
    AttachmentORM,
    AttachmentRecipientKeyORM,
    UploadSessionORM,
)
from bluebubbles.server.domain.attachments import (
    Attachment,
    AttachmentRecipientKey,
    UploadSession,
)
from bluebubbles.shared.models.attachments import AttachmentStatus
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    HashAlgorithm,
    KeyEnvelopeAlgorithm,
)


class AttachmentMapper:
    """Convert attachment metadata without accessing physical files."""

    @staticmethod
    def key_to_domain(record: AttachmentRecipientKeyORM) -> AttachmentRecipientKey:
        """Convert one recipient file-key envelope."""
        return AttachmentRecipientKey(
            id=record.id,
            created_at=record.created_at,
            updated_at=record.created_at,
            attachment_id=record.attachment_id,
            recipient_id=record.recipient_user_id,
            key_version=record.recipient_key_version,
            encrypted_key=record.encrypted_file_key,
            algorithm=KeyEnvelopeAlgorithm(record.key_algorithm),
            ephemeral_public_key=record.ephemeral_public_key,
        )

    @staticmethod
    def key_to_orm(key: AttachmentRecipientKey) -> AttachmentRecipientKeyORM:
        """Convert one domain recipient key to a new ORM row."""
        if not key.ephemeral_public_key:
            raise ValueError("Attachment key ephemeral public key is required")
        return AttachmentRecipientKeyORM(
            id=key.id,
            created_at=key.created_at,
            attachment_id=key.attachment_id,
            recipient_user_id=key.recipient_id,
            encrypted_file_key=key.encrypted_key,
            ephemeral_public_key=key.ephemeral_public_key,
            key_algorithm=key.algorithm.value,
            recipient_key_version=key.key_version,
        )

    @staticmethod
    def to_domain(
        record: AttachmentORM,
        keys: tuple[AttachmentRecipientKeyORM, ...] = (),
    ) -> Attachment:
        """Convert one attachment metadata row and explicitly loaded keys."""
        return Attachment(
            id=record.id,
            created_at=record.created_at,
            updated_at=record.completed_at or record.created_at,
            deleted_at=record.deleted_at,
            version=record.version,
            conversation_id=record.conversation_id,
            uploaded_by=record.uploader_id,
            filename=record.safe_display_filename,
            media_type=record.mime_type,
            encrypted_size=record.encrypted_size,
            original_size=record.plaintext_size,
            content_algorithm=ContentEncryptionAlgorithm(record.content_algorithm),
            hash_algorithm=HashAlgorithm(record.hash_algorithm),
            encrypted_checksum=base64.b64decode(
                record.encrypted_checksum.encode("ascii"), validate=True
            ),
            storage_reference=record.storage_reference,
            chunk_size=record.chunk_size,
            status=AttachmentStatus(record.status),
            recipient_keys=tuple(AttachmentMapper.key_to_domain(item) for item in keys),
            linked_message_id=record.message_id,
        )

    @staticmethod
    def to_orm(attachment: Attachment) -> AttachmentORM:
        """Convert complete attachment metadata to a new ORM row."""
        if attachment.chunk_size is None:
            raise ValueError("Attachment chunk size is required for persistence")
        return AttachmentORM(
            id=attachment.id,
            created_at=attachment.created_at,
            deleted_at=attachment.deleted_at,
            version=attachment.version,
            conversation_id=attachment.conversation_id,
            message_id=attachment.linked_message_id,
            uploader_id=attachment.uploaded_by,
            original_filename=attachment.filename,
            safe_display_filename=attachment.filename,
            mime_type=attachment.media_type,
            content_algorithm=attachment.content_algorithm.value,
            hash_algorithm=attachment.hash_algorithm.value,
            plaintext_size=attachment.original_size,
            encrypted_size=attachment.encrypted_size,
            chunk_size=attachment.chunk_size,
            chunk_count=attachment.chunk_count,
            encrypted_checksum=base64.b64encode(attachment.encrypted_checksum).decode(
                "ascii"
            ),
            encrypted_metadata=None,
            metadata_nonce=None,
            metadata_authentication_tag=None,
            storage_reference=attachment.storage_reference,
            status=attachment.status.value,
            completed_at=None,
        )

    @staticmethod
    def upload_to_domain(
        record: UploadSessionORM, received_chunks: dict[int, int]
    ) -> UploadSession:
        """Convert recoverable upload state to its domain representation."""
        return UploadSession(
            id=record.id,
            created_at=record.created_at,
            updated_at=record.updated_at,
            attachment_id=record.attachment_id,
            uploader_id=record.user_id,
            chunk_size=record.chunk_size,
            total_size=record.expected_encrypted_size,
            expires_at=record.expires_at,
            received_chunks=received_chunks,
            completed_at=record.completed_at,
        )
