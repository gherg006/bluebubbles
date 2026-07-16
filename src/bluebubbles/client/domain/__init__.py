"""Windows-client domain models; this package is never imported by the server."""

from bluebubbles.client.domain.attachments import ClientAttachment
from bluebubbles.client.domain.conversations import ClientConversation
from bluebubbles.client.domain.identity import ClientIdentity
from bluebubbles.client.domain.messages import (
    ClientMessage,
    DecryptedMessageContent,
    EncryptedLocalContent,
    EncryptedTransportData,
    MessageDisplayState,
    MessageDraft,
)
from bluebubbles.client.domain.offline_actions import OfflineAction, OfflineActionState
from bluebubbles.client.domain.search import SearchQuery, SearchResult
from bluebubbles.client.domain.transfers import (
    EncryptedChunk,
    FileTransfer,
    PreparedUpload,
    TransferDirection,
    TransferProgress,
    TransferState,
)

__all__ = [
    "ClientAttachment",
    "ClientConversation",
    "ClientIdentity",
    "ClientMessage",
    "DecryptedMessageContent",
    "EncryptedChunk",
    "EncryptedLocalContent",
    "EncryptedTransportData",
    "FileTransfer",
    "MessageDisplayState",
    "MessageDraft",
    "OfflineAction",
    "OfflineActionState",
    "PreparedUpload",
    "SearchQuery",
    "SearchResult",
    "TransferDirection",
    "TransferProgress",
    "TransferState",
]
