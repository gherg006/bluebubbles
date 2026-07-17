"""Small protocols implemented by encrypted local client repositories."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from bluebubbles.client.domain.messages import MessageDraft
from bluebubbles.client.domain.offline_actions import OfflineAction
from bluebubbles.client.domain.transfers import FileTransfer
from bluebubbles.client.repositories.models import (
    CachedConversationRecord,
    CachedUserRecord,
)
from bluebubbles.client.storage.models import CachedPublicKey


class CachedUserRepository(Protocol):
    """Persist versioned user profile cache records."""

    async def save(self, user: CachedUserRecord) -> bool: ...
    async def get(self, user_id: UUID) -> CachedUserRecord | None: ...
    async def delete(self, user_id: UUID) -> None: ...


class CachedConversationRepository(Protocol):
    """Persist versioned conversation summaries."""

    async def save(self, conversation: CachedConversationRecord) -> bool: ...
    async def get(
        self, conversation_id: UUID
    ) -> CachedConversationRecord | None: ...


class PublicKeyCacheRepository(Protocol):
    """Persist versioned public keys with explicit invalidation."""

    async def save(self, key: CachedPublicKey) -> None: ...
    async def get_valid(
        self, user_id: UUID, key_type: str, key_version: int
    ) -> CachedPublicKey | None: ...
    async def invalidate_user(self, user_id: UUID) -> None: ...


class LocalSettingsRepository(Protocol):
    """Persist validated user-controlled local preferences."""

    async def set(self, key: str, value: object) -> None: ...
    async def get(self, key: str) -> object | None: ...
    async def delete(self, key: str) -> None: ...


class DraftRepository(Protocol):
    """Persist encrypted unsent drafts."""

    async def save_draft(self, draft: MessageDraft) -> None: ...
    async def get_draft(self, conversation_id: UUID) -> MessageDraft | None: ...
    async def delete_draft(self, conversation_id: UUID) -> None: ...
    async def list_drafts(self) -> list[MessageDraft]: ...


class OfflineActionRepository(Protocol):
    """Persist locally re-encrypted retry actions."""

    async def save(self, action: OfflineAction) -> None: ...
    async def get(self, action_id: UUID) -> OfflineAction | None: ...
    async def list_pending(self) -> list[OfflineAction]: ...
    async def delete(self, action_id: UUID) -> None: ...


class TransferStateRepository(Protocol):
    """Persist encrypted resumable transfer state."""

    async def save(self, transfer: FileTransfer) -> None: ...
    async def get(self, transfer_id: UUID) -> FileTransfer | None: ...
    async def list_incomplete(self) -> list[FileTransfer]: ...
    async def delete(self, transfer_id: UUID) -> None: ...


__all__ = [
    "CachedConversationRepository",
    "CachedUserRepository",
    "DraftRepository",
    "LocalSettingsRepository",
    "OfflineActionRepository",
    "PublicKeyCacheRepository",
    "TransferStateRepository",
]
