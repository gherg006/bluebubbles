"""Task 13 client encrypted send, retry, and incoming-message evidence."""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from bluebubbles.client.security.message_crypto import DecryptedMessage
from bluebubbles.client.services.messaging import (
    ClientMessagingService,
    InMemoryEncryptedMessageQueue,
)
from bluebubbles.shared.errors.exceptions import NetworkError
from bluebubbles.shared.models.messages import (
    EncryptedMessageResponse,
    MessageType,
    RecipientKeyEnvelopeRequest,
    SendMessageRequest,
    SendMessageResponse,
)
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    KeyEnvelopeAlgorithm,
    SignatureAlgorithm,
)


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _contracts() -> tuple[SendMessageRequest, EncryptedMessageResponse]:
    user_id, conversation_id, message_id = uuid4(), uuid4(), uuid4()
    key = RecipientKeyEnvelopeRequest(
        recipient_id=user_id,
        key_version=1,
        algorithm=KeyEnvelopeAlgorithm.X25519_HKDF_SHA256_AES_256_GCM_V1,
        ephemeral_public_key=_b64(b"p" * 32),
        nonce=_b64(b"n" * 12),
        encrypted_key=_b64(b"wrapped"),
    )
    now = datetime.now(UTC)
    request = SendMessageRequest(
        client_message_id=message_id,
        conversation_id=conversation_id,
        message_type=MessageType.TEXT,
        content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
        ciphertext=_b64(b"ciphertext"),
        nonce=_b64(b"m" * 12),
        signature_algorithm=SignatureAlgorithm.ED25519_V1,
        signature=_b64(b"s" * 64),
        sender_key_version=1,
        client_created_at=now,
        encrypted_keys=(key,),
    )
    response = EncryptedMessageResponse(
        id=message_id,
        client_message_id=message_id,
        conversation_id=conversation_id,
        sender_id=user_id,
        message_type=MessageType.TEXT,
        content_algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
        ciphertext=request.ciphertext,
        nonce=request.nonce,
        signature_algorithm=SignatureAlgorithm.ED25519_V1,
        signature=request.signature,
        sender_key_version=1,
        encrypted_key=key,
        recipient_envelope_digest=request.recipient_envelope_digest or "",
        sent_at=now,
    )
    return request, response


class _Crypto:
    def __init__(self, request: SendMessageRequest) -> None:
        self.request = request

    async def encrypt_message(self, command: object) -> SendMessageRequest:
        del command
        return self.request

    async def decrypt_message(
        self, response: EncryptedMessageResponse
    ) -> DecryptedMessage:
        return DecryptedMessage(response.id, "decrypted", 1)


class _Api:
    def __init__(self, response: EncryptedMessageResponse) -> None:
        self.response = response
        self.failures = 0
        self.acknowledged = 0

    async def send_message(self, request: SendMessageRequest) -> SendMessageResponse:
        del request
        if self.failures:
            self.failures -= 1
            raise NetworkError()
        return SendMessageResponse(message=self.response)

    async def acknowledge_delivery(self, *args: object) -> None:
        self.acknowledged += 1


class _Cache:
    def __init__(self) -> None:
        self.messages: list[EncryptedMessageResponse] = []

    async def store(self, message: EncryptedMessageResponse) -> None:
        self.messages.append(message)


@pytest.mark.asyncio
async def test_client_send_retries_ciphertext_with_stable_identifier() -> None:
    request, response = _contracts()
    queue = InMemoryEncryptedMessageQueue()
    api, cache = _Api(response), _Cache()
    service = ClientMessagingService(
        _Crypto(request),  # type: ignore[arg-type]
        api,
        queue,
        cache,
    )
    api.failures = 1
    with pytest.raises(NetworkError):
        await service.send(object())  # type: ignore[arg-type]
    due_later = datetime.now(UTC) + timedelta(seconds=31)
    assert await service.retry_due(due_later) == (request.client_message_id,)
    assert cache.messages == [response]
    sent = await service.send(object())  # type: ignore[arg-type]
    assert sent.message.id == request.client_message_id


@pytest.mark.asyncio
async def test_incoming_is_decrypted_cached_acknowledged_and_deduplicated() -> None:
    request, response = _contracts()
    api, cache = _Api(response), _Cache()
    service = ClientMessagingService(
        _Crypto(request),  # type: ignore[arg-type]
        api,
        InMemoryEncryptedMessageQueue(),
        cache,
    )
    decrypted = await service.process_incoming(response)
    assert decrypted is not None and decrypted.text == "decrypted"
    assert api.acknowledged == 1
    assert await service.process_incoming(response) is None


@pytest.mark.asyncio
async def test_offline_queue_is_bounded_and_retry_failure_remains_queued() -> None:
    request, response = _contracts()
    queue = InMemoryEncryptedMessageQueue(maximum_items=1)
    await queue.enqueue(request)
    second, _ = _contracts()
    with pytest.raises(NetworkError, match="full"):
        await queue.enqueue(second)
    api, cache = _Api(response), _Cache()
    api.failures = 1
    service = ClientMessagingService(
        _Crypto(request),  # type: ignore[arg-type]
        api,
        queue,
        cache,
    )
    assert await service.retry_due(datetime.now(UTC) + timedelta(seconds=1)) == ()
    assert cache.messages == []
