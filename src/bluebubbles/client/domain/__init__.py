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
from bluebubbles.client.domain.offline_actions import (
    OfflineAction,
    OfflineActionExecutionResult,
    OfflineActionOutcome,
    OfflineActionState,
    OfflineActionSummary,
    OfflineActionType,
    PendingOfflineAction,
    QueueProcessingResult,
)
from bluebubbles.client.domain.search import SearchQuery, SearchResult
from bluebubbles.client.domain.synchronisation import (
    CancellationToken,
    ConflictCategory,
    ConflictResolution,
    ConnectivityState,
    LocalTombstone,
    ScopeSynchronisationResult,
    SynchronisationConflict,
    SynchronisationResult,
    SynchronisationScope,
)
from bluebubbles.client.domain.transfers import (
    EncryptedChunk,
    FileTransfer,
    PreparedUpload,
    TransferDirection,
    TransferProgress,
    TransferRecovery,
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
    "OfflineActionExecutionResult",
    "OfflineActionOutcome",
    "OfflineActionState",
    "OfflineActionSummary",
    "OfflineActionType",
    "PendingOfflineAction",
    "QueueProcessingResult",
    "CancellationToken",
    "ConflictCategory",
    "ConflictResolution",
    "ConnectivityState",
    "LocalTombstone",
    "ScopeSynchronisationResult",
    "SynchronisationConflict",
    "SynchronisationResult",
    "SynchronisationScope",
    "PreparedUpload",
    "SearchQuery",
    "SearchResult",
    "TransferDirection",
    "TransferProgress",
    "TransferRecovery",
    "TransferState",
]
