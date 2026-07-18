"""Client encrypted-message send, retry, receive, and acknowledgement workflow."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from bluebubbles.client.domain.offline_actions import OfflineAction, OfflineActionState
from bluebubbles.client.repositories.interfaces import OfflineActionRepository
from bluebubbles.client.security.message_crypto import (
    DecryptedMessage,
    EncryptMessageCommand,
    MessageEncryptionService,
)
from bluebubbles.shared.errors.exceptions import NetworkError
from bluebubbles.shared.models.messages import (
    EncryptedMessageResponse,
    MessageDeliveryStatus,
    SendMessageRequest,
    SendMessageResponse,
)


class MessagingApi(Protocol):
    async def send_message(
        self, request: SendMessageRequest
    ) -> SendMessageResponse: ...

    async def acknowledge_delivery(
        self, message_id: UUID, conversation_id: UUID, occurred_at: datetime
    ) -> None: ...


class EncryptedMessageCache(Protocol):
    async def store(self, message: EncryptedMessageResponse) -> None: ...


class EncryptedMessageQueue(Protocol):
    """Define ciphertext retry storage independent of memory or SQLite."""

    async def enqueue(self, request: SendMessageRequest) -> None: ...
    async def mark_stored(self, message_id: UUID) -> None: ...
    async def mark_retry(self, message_id: UUID, error_code: str) -> None: ...
    async def due(self, now: datetime) -> tuple[QueuedEncryptedMessage, ...]: ...


@dataclass(frozen=True, slots=True)
class QueuedEncryptedMessage:
    """Retain ciphertext-only retry state with the stable client message UUID."""

    request: SendMessageRequest
    state: MessageDeliveryStatus
    attempt_count: int
    next_retry_at: datetime
    last_error_code: str | None = None


class InMemoryEncryptedMessageQueue:
    """Bounded ciphertext-only queue used until the local database stage."""

    def __init__(self, maximum_items: int = 1000) -> None:
        if maximum_items < 1:
            raise ValueError("Offline queue limit must be positive")
        self._maximum_items = maximum_items
        self._items: dict[UUID, QueuedEncryptedMessage] = {}

    async def enqueue(self, request: SendMessageRequest) -> None:
        if (
            request.client_message_id not in self._items
            and len(self._items) >= self._maximum_items
        ):
            raise NetworkError(user_message="The encrypted offline queue is full.")
        self._items.setdefault(
            request.client_message_id,
            QueuedEncryptedMessage(
                request,
                MessageDeliveryStatus.PENDING,
                0,
                datetime.now(UTC),
            ),
        )

    async def mark_stored(self, message_id: UUID) -> None:
        self._items.pop(message_id, None)

    async def mark_retry(self, message_id: UUID, error_code: str) -> None:
        item = self._items[message_id]
        attempts = item.attempt_count + 1
        delays = (2, 4, 8, 16, 30)
        delay = delays[min(attempts - 1, len(delays) - 1)]
        self._items[message_id] = replace(
            item,
            state=MessageDeliveryStatus.FAILED,
            attempt_count=attempts,
            next_retry_at=datetime.now(UTC) + timedelta(seconds=delay),
            last_error_code=error_code,
        )

    async def due(self, now: datetime) -> tuple[QueuedEncryptedMessage, ...]:
        return tuple(item for item in self._items.values() if item.next_retry_at <= now)


class DurableEncryptedMessageQueue:
    """Adapt the encrypted offline-action repository to the messaging queue API."""

    def __init__(self, repository: OfflineActionRepository) -> None:
        self._repository = repository

    async def enqueue(self, request: SendMessageRequest) -> None:
        """Persist a prepared ciphertext request with its stable message UUID."""
        action = OfflineAction(
            request.client_message_id,
            "send_message",
            request.client_message_id,
            request.model_dump_json().encode(),
            datetime.now(UTC),
        )
        await self._save(action)

    async def mark_stored(self, message_id: UUID) -> None:
        """Remove a queue item only after authoritative storage acknowledgement."""
        await self._delete(message_id)

    async def mark_retry(self, message_id: UUID, error_code: str) -> None:
        """Persist bounded backoff metadata after a retryable network failure."""
        action = await self._get(message_id)
        if action is None:
            raise KeyError(message_id)
        attempts = action.attempts + 1
        delay = (2, 4, 8, 16, 30)[min(attempts - 1, 4)]
        await self._save(
            replace(
                action,
                next_attempt_at=datetime.now(UTC) + timedelta(seconds=delay),
                state=OfflineActionState.FAILED,
                attempts=attempts,
                last_error_code=error_code,
            )
        )

    async def due(self, now: datetime) -> tuple[QueuedEncryptedMessage, ...]:
        """Return durable due requests in repository creation order."""
        actions = await self._list_pending()
        queued: list[QueuedEncryptedMessage] = []
        for action in actions:
            due_at = action.next_attempt_at or action.created_at
            if due_at > now:
                continue
            request = SendMessageRequest.model_validate_json(action.encrypted_payload)
            queued.append(
                QueuedEncryptedMessage(
                    request,
                    (
                        MessageDeliveryStatus.FAILED
                        if action.attempts
                        else MessageDeliveryStatus.PENDING
                    ),
                    action.attempts,
                    due_at,
                    action.last_error_code,
                )
            )
        return tuple(queued)

    async def _save(self, action: OfflineAction) -> None:
        await self._repository.save(action)

    async def _get(self, action_id: UUID) -> OfflineAction | None:
        return await self._repository.get(action_id)

    async def _delete(self, action_id: UUID) -> None:
        await self._repository.delete(action_id)

    async def _list_pending(self) -> list[OfflineAction]:
        return await self._repository.list_pending()


class ClientMessagingService:
    """Keep plaintext inside crypto calls and preserve encrypted retry identity."""

    def __init__(
        self,
        encryption_service: MessageEncryptionService,
        api: MessagingApi,
        queue: EncryptedMessageQueue,
        cache: EncryptedMessageCache,
    ) -> None:
        self._encryption_service = encryption_service
        self._api = api
        self._queue = queue
        self._cache = cache
        self._processed_ids: set[UUID] = set()

    async def send(self, command: EncryptMessageCommand) -> SendMessageResponse:
        request = await self._encryption_service.encrypt_message(command)
        await self._queue.enqueue(request)
        try:
            response = await self._api.send_message(request)
        except NetworkError:
            await self._queue.mark_retry(
                request.client_message_id, "network_unavailable"
            )
            raise
        await self._queue.mark_stored(request.client_message_id)
        await self._cache.store(response.message)
        return response

    async def retry_due(self, now: datetime | None = None) -> tuple[UUID, ...]:
        completed: list[UUID] = []
        for item in await self._queue.due(now or datetime.now(UTC)):
            try:
                response = await self._api.send_message(item.request)
            except NetworkError:
                await self._queue.mark_retry(
                    item.request.client_message_id, "network_unavailable"
                )
                continue
            await self._queue.mark_stored(item.request.client_message_id)
            await self._cache.store(response.message)
            completed.append(item.request.client_message_id)
        return tuple(completed)

    async def process_incoming(
        self, response: EncryptedMessageResponse
    ) -> DecryptedMessage | None:
        if response.id in self._processed_ids:
            return None
        decrypted = await self._encryption_service.decrypt_message(response)
        await self._cache.store(response)
        await self._api.acknowledge_delivery(
            response.id, response.conversation_id, datetime.now(UTC)
        )
        self._processed_ids.add(response.id)
        return decrypted
