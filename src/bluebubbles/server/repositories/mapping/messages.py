"""Pure encrypted-message ORM/domain conversions."""

from uuid import UUID

from bluebubbles.server.database.models.messages import (
    MessageORM,
    MessageRecipientKeyORM,
)
from bluebubbles.server.domain.messages import Message, MessageRecipientKey
from bluebubbles.shared.models.messages import MessageType
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    KeyEnvelopeAlgorithm,
    SignatureAlgorithm,
)


class MessageMapper:
    """Convert encrypted envelopes without decrypting or authorizing them."""

    @staticmethod
    def key_to_domain(record: MessageRecipientKeyORM) -> MessageRecipientKey:
        """Convert one recipient key envelope."""
        return MessageRecipientKey(
            id=record.id,
            created_at=record.created_at,
            updated_at=record.created_at,
            message_id=record.message_id,
            recipient_id=record.recipient_user_id,
            key_version=record.recipient_key_version,
            algorithm=KeyEnvelopeAlgorithm(record.key_algorithm),
            ephemeral_public_key=record.ephemeral_public_key,
            nonce=record.key_nonce or b"",
            encrypted_key=record.encrypted_content_key,
        )

    @staticmethod
    def key_to_orm(key: MessageRecipientKey) -> MessageRecipientKeyORM:
        """Convert one domain recipient key to a new ORM row."""
        return MessageRecipientKeyORM(
            id=key.id,
            created_at=key.created_at,
            message_id=key.message_id,
            recipient_user_id=key.recipient_id,
            encrypted_content_key=key.encrypted_key,
            ephemeral_public_key=key.ephemeral_public_key,
            key_nonce=key.nonce,
            key_algorithm=key.algorithm.value,
            recipient_key_version=key.key_version,
        )

    @staticmethod
    def to_domain(
        record: MessageORM,
        keys: tuple[MessageRecipientKeyORM, ...],
        attachment_ids: tuple[UUID, ...] = (),
    ) -> Message:
        """Convert one complete encrypted message record."""
        if (
            record.ciphertext is None
            or record.nonce is None
            or record.signature is None
        ):
            raise ValueError("Active message row has an incomplete encrypted envelope")
        if record.signature_key_version is None:
            raise ValueError("Active message row has no signature key version")
        mapped_keys = tuple(MessageMapper.key_to_domain(item) for item in keys)
        return Message(
            id=record.id,
            created_at=record.server_created_at,
            updated_at=record.edited_at or record.server_created_at,
            deleted_at=record.deleted_at,
            version=record.version,
            client_message_id=record.id,
            conversation_id=record.conversation_id,
            sender_id=record.sender_id,
            message_type=MessageType(record.message_type),
            content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
            ciphertext=record.ciphertext,
            nonce=record.nonce,
            signature_algorithm=SignatureAlgorithm.ED25519_V1,
            signature=record.signature,
            sender_key_version=record.signature_key_version,
            sent_at=record.client_created_at,
            recipient_keys=mapped_keys,
            reply_to_id=record.reply_to_message_id,
            attachment_ids=tuple(attachment_ids),
            edited_at=record.edited_at,
        )

    @staticmethod
    def to_orm(message: Message) -> MessageORM:
        """Convert a domain message to a new encrypted ORM row."""
        return MessageORM(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            message_type=message.message_type.value,
            ciphertext=message.ciphertext,
            nonce=message.nonce,
            authentication_tag=None,
            signature=message.signature,
            signature_key_version=message.sender_key_version,
            protocol_version=1,
            reply_to_message_id=message.reply_to_id,
            client_created_at=message.sent_at,
            server_created_at=message.created_at,
            edited_at=message.edited_at,
            encrypted_payload_size=len(message.ciphertext),
            deleted_at=message.deleted_at,
            version=message.version,
        )
