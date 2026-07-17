"""Client operating-system secret-storage abstractions."""

from bluebubbles.client.security.attachment_crypto import (
    AttachmentCryptoContext,
    AttachmentEncryptionService,
    AuthenticatedAttachmentChunk,
)
from bluebubbles.client.security.key_manager import ClientKeyManager
from bluebubbles.client.security.key_store import EncryptedPrivateKeyStore
from bluebubbles.client.security.local_encryption import LocalEncryptionService
from bluebubbles.client.security.message_crypto import MessageEncryptionService
from bluebubbles.client.security.secure_store import (
    SecureStore,
    WindowsCredentialManagerStore,
)

__all__ = [
    "AttachmentCryptoContext",
    "AttachmentEncryptionService",
    "AuthenticatedAttachmentChunk",
    "ClientKeyManager",
    "EncryptedPrivateKeyStore",
    "LocalEncryptionService",
    "MessageEncryptionService",
    "SecureStore",
    "WindowsCredentialManagerStore",
]
