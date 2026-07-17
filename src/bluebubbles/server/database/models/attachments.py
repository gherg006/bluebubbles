"""Encrypted attachment metadata, chunk, recipient-key, and upload mappings."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from bluebubbles.server.database.base import (
    Base,
    CreatedAtMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VersionMixin,
)


class AttachmentORM(
    Base, UUIDPrimaryKeyMixin, CreatedAtMixin, SoftDeleteMixin, VersionMixin
):
    """Map encrypted-file metadata while keeping physical bytes on the filesystem."""

    __tablename__ = "attachments"
    __table_args__ = (
        CheckConstraint("plaintext_size >= 0", name="plaintext_size_non_negative"),
        CheckConstraint("encrypted_size >= 0", name="encrypted_size_non_negative"),
        CheckConstraint("chunk_size > 0", name="chunk_size_positive"),
        CheckConstraint("chunk_count >= 0", name="chunk_count_non_negative"),
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint(
            "status IN ('initialised', 'uploading', 'complete', 'failed', 'deleted')",
            name="status_valid",
        ),
        CheckConstraint(
            "content_algorithm = 'AES-256-GCM-V1'", name="content_algorithm_valid"
        ),
        CheckConstraint("hash_algorithm = 'SHA256-V1'", name="hash_algorithm_valid"),
        CheckConstraint(
            "(encrypted_metadata IS NULL AND metadata_nonce IS NULL AND "
            "metadata_authentication_tag IS NULL) OR "
            "(encrypted_metadata IS NOT NULL AND metadata_nonce IS NOT NULL AND "
            "metadata_authentication_tag IS NOT NULL)",
            name="metadata_envelope_complete",
        ),
        Index("ix_attachments_message", "message_id"),
        Index("ix_attachments_conversation", "conversation_id", "created_at"),
        Index("ix_attachments_status", "status", "created_at"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    message_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"), unique=True
    )
    uploader_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    safe_display_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    content_algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    hash_algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    plaintext_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    encrypted_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False)
    encrypted_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    encrypted_metadata: Mapped[bytes | None] = mapped_column(LargeBinary)
    metadata_nonce: Mapped[bytes | None] = mapped_column(LargeBinary)
    metadata_authentication_tag: Mapped[bytes | None] = mapped_column(LargeBinary)
    storage_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AttachmentRecipientKeyORM(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """Map one recipient-specific encrypted attachment-key envelope."""

    __tablename__ = "attachment_recipient_keys"
    __table_args__ = (
        UniqueConstraint(
            "attachment_id", "recipient_user_id", name="uq_attachment_recipient"
        ),
        CheckConstraint(
            "recipient_key_version >= 1", name="recipient_key_version_positive"
        ),
        CheckConstraint(
            "key_algorithm = 'X25519-HKDF-SHA256-AES-256-GCM-V1'",
            name="key_algorithm_valid",
        ),
        Index(
            "ix_attachment_recipient_keys_recipient",
            "recipient_user_id",
            "attachment_id",
        ),
    )

    attachment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("attachments.id", ondelete="CASCADE"),
        nullable=False,
    )
    recipient_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    encrypted_file_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    ephemeral_public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    key_algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    recipient_key_version: Mapped[int] = mapped_column(Integer, nullable=False)


class AttachmentChunkORM(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """Map one durably stored encrypted attachment chunk."""

    __tablename__ = "attachment_chunks"
    __table_args__ = (
        UniqueConstraint("attachment_id", "chunk_index", name="uq_attachment_chunk"),
        CheckConstraint("chunk_index >= 0", name="chunk_index_non_negative"),
        CheckConstraint("encrypted_size >= 0", name="encrypted_size_non_negative"),
    )

    attachment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("attachments.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    encrypted_size: Mapped[int] = mapped_column(Integer, nullable=False)
    encrypted_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    authentication_tag: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    storage_reference: Mapped[str] = mapped_column(String(1000), nullable=False)


class UploadSessionORM(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Map enough upload state to recover safely after Redis loss."""

    __tablename__ = "upload_sessions"
    __table_args__ = (
        CheckConstraint(
            "expected_encrypted_size >= 0", name="expected_size_non_negative"
        ),
        CheckConstraint(
            "received_encrypted_size >= 0", name="received_size_non_negative"
        ),
        CheckConstraint(
            "received_encrypted_size <= expected_encrypted_size",
            name="received_within_expected",
        ),
        CheckConstraint("expected_chunk_count >= 0", name="chunk_count_non_negative"),
        CheckConstraint("chunk_size > 0", name="chunk_size_positive"),
        Index("ix_upload_sessions_expiry", "status", "expires_at"),
    )

    attachment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("attachments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    expected_encrypted_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expected_chunk_count: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False)
    received_encrypted_size: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UploadSessionChunkORM(Base):
    """Map recoverable receipt evidence for an upload-session chunk."""

    __tablename__ = "upload_session_chunks"
    __table_args__ = (
        CheckConstraint("chunk_index >= 0", name="chunk_index_non_negative"),
        CheckConstraint("encrypted_size >= 0", name="encrypted_size_non_negative"),
    )

    upload_session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("upload_sessions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, primary_key=True)
    encrypted_size: Mapped[int] = mapped_column(Integer, nullable=False)
    encrypted_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    authentication_tag: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
