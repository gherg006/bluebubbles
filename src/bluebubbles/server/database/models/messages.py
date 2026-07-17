"""Encrypted message, recipient envelope, version, and delivery mappings."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from bluebubbles.server.database.base import (
    Base,
    CreatedAtMixin,
    SoftDeleteMixin,
    UUIDPrimaryKeyMixin,
    VersionMixin,
)


class MessageORM(Base, UUIDPrimaryKeyMixin, SoftDeleteMixin, VersionMixin):
    """Map a signed encrypted payload without any plaintext-capable column."""

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint(
            "message_type IN ('text', 'system', 'attachment', "
            "'text_with_attachment')",
            name="message_type_valid",
        ),
        CheckConstraint("protocol_version >= 1", name="protocol_version_positive"),
        CheckConstraint(
            "encrypted_payload_size >= 0", name="payload_size_non_negative"
        ),
        CheckConstraint(
            "signature_key_version IS NULL OR signature_key_version >= 1",
            name="signature_key_version_positive",
        ),
        Index(
            "ix_messages_conversation_order",
            "conversation_id",
            "server_created_at",
            "id",
        ),
        Index("ix_messages_sender", "sender_id", "server_created_at"),
        Index(
            "ix_messages_reply",
            "reply_to_message_id",
            postgresql_where=text("reply_to_message_id IS NOT NULL"),
        ),
        Index(
            "ix_messages_deleted",
            "deleted_at",
            postgresql_where=text("deleted_at IS NOT NULL"),
        ),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sender_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    message_type: Mapped[str] = mapped_column(String(30), nullable=False)
    ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)
    nonce: Mapped[bytes | None] = mapped_column(LargeBinary)
    authentication_tag: Mapped[bytes | None] = mapped_column(LargeBinary)
    signature: Mapped[bytes | None] = mapped_column(LargeBinary)
    signature_key_version: Mapped[int | None] = mapped_column(Integer)
    protocol_version: Mapped[int] = mapped_column(Integer, nullable=False)
    reply_to_message_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL")
    )
    client_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    server_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    encrypted_payload_size: Mapped[int] = mapped_column(Integer, nullable=False)


class MessageRecipientKeyORM(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """Map one recipient-specific encrypted content-key envelope."""

    __tablename__ = "message_recipient_keys"
    __table_args__ = (
        UniqueConstraint(
            "message_id", "recipient_user_id", name="uq_message_recipient"
        ),
        CheckConstraint(
            "recipient_key_version >= 1", name="recipient_key_version_positive"
        ),
        CheckConstraint(
            "key_algorithm = 'X25519-HKDF-SHA256-AES-256-GCM-V1'",
            name="key_algorithm_valid",
        ),
        Index("ix_message_recipient_keys_recipient", "recipient_user_id", "message_id"),
    )

    message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    recipient_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    encrypted_content_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    ephemeral_public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    key_nonce: Mapped[bytes | None] = mapped_column(LargeBinary)
    key_algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    recipient_key_version: Mapped[int] = mapped_column(Integer, nullable=False)


class MessageVersionORM(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """Map an immutable prior encrypted envelope retained after an edit."""

    __tablename__ = "message_versions"
    __table_args__ = (
        UniqueConstraint("message_id", "version_number", name="uq_message_version"),
        CheckConstraint("version_number >= 1", name="version_number_positive"),
    )

    message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    authentication_tag: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    signature: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    signature_key_version: Mapped[int] = mapped_column(Integer, nullable=False)
    edited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MessageDeliveryORM(Base):
    """Map one recipient's durable per-message delivery state."""

    __tablename__ = "message_deliveries"
    __table_args__ = (
        CheckConstraint(
            "delivery_state IN ('pending', 'stored', 'delivered', 'read', 'failed')",
            name="state_valid",
        ),
        CheckConstraint(
            "read_at IS NULL OR delivered_at IS NOT NULL", name="read_implies_delivered"
        ),
        Index("ix_message_deliveries_recipient", "recipient_user_id", "updated_at"),
    )

    message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        primary_key=True,
    )
    recipient_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    delivery_state: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
