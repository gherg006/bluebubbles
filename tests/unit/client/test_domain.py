"""Tests for client-only plaintext boundaries and transfer state."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from bluebubbles.client.domain.conversations import ClientConversation
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
    FileTransfer,
    TransferDirection,
    TransferProgress,
    TransferState,
)
from bluebubbles.shared.models.conversations import ConversationType
from bluebubbles.shared.models.messages import MessageType
from bluebubbles.shared.security.algorithms import (
    ContentEncryptionAlgorithm,
    SignatureAlgorithm,
)

NOW = datetime(2026, 7, 16, tzinfo=UTC)


def test_client_message_plaintext_can_be_attached_and_removed() -> None:
    transport = EncryptedTransportData(
        algorithm=ContentEncryptionAlgorithm.AES_256_GCM_V1,
        ciphertext=b"cipher",
        nonce=b"nonce",
        signature_algorithm=SignatureAlgorithm.ED25519_V1,
        signature=b"signature",
        sender_key_version=1,
    )
    local = EncryptedLocalContent(b"cache", b"nonce", "windows-store-key")
    message = ClientMessage(
        id=uuid4(),
        client_message_id=uuid4(),
        conversation_id=uuid4(),
        sender_id=uuid4(),
        message_type=MessageType.TEXT,
        sent_at=NOW,
        transport=transport,
        local_content=local,
    )
    displayed = message.with_decrypted_content(DecryptedMessageContent("Hello"))
    assert displayed.decrypted_content is not None
    assert displayed.without_plaintext().decrypted_content is None
    assert (
        displayed.with_display_state(MessageDisplayState.READ).display_state
        is MessageDisplayState.READ
    )
    assert "cipher" not in repr(transport)
    with pytest.raises(ValueError):
        DecryptedMessageContent("bad\x00text")


def test_draft_and_conversation_invariants() -> None:
    with pytest.raises(ValueError):
        MessageDraft(conversation_id=uuid4(), text="")
    attachment_id = uuid4()
    draft = MessageDraft(
        conversation_id=uuid4(), text="", attachment_ids=(attachment_id,)
    )
    assert draft.attachment_ids == (attachment_id,)
    conversation = ClientConversation(
        id=uuid4(),
        conversation_type=ConversationType.DIRECT,
        participant_ids=(uuid4(), uuid4()),
        last_activity=NOW,
        unread_count=3,
    )
    assert conversation.mark_read().unread_count == 0


def test_transfer_state_machine_and_monotonic_progress() -> None:
    initial = TransferProgress(0, 10)
    transfer = FileTransfer(
        id=uuid4(),
        attachment_id=uuid4(),
        direction=TransferDirection.UPLOAD,
        state=TransferState.QUEUED,
        progress=initial,
    )
    transfer = transfer.transition(TransferState.PREPARING).transition(
        TransferState.TRANSFERRING
    )
    transfer = transfer.update_progress(TransferProgress(5, 10, 5.0, 1.0))
    transfer = transfer.transition(TransferState.VERIFYING).transition(
        TransferState.COMPLETE
    )
    assert transfer.progress.transferred_bytes == 5
    with pytest.raises(ValueError, match="Invalid transfer"):
        transfer.transition(TransferState.PAUSED)
    with pytest.raises(ValueError, match="backwards"):
        transfer.update_progress(TransferProgress(4, 10))


def test_offline_action_and_local_search_models() -> None:
    action = OfflineAction(
        id=uuid4(),
        action_type="send_message",
        idempotency_key=uuid4(),
        encrypted_payload=b"encrypted",
        created_at=NOW,
    ).begin()
    assert action.state is OfflineActionState.IN_PROGRESS and action.attempts == 1
    with pytest.raises(ValueError):
        action.begin()
    query = SearchQuery("hello", limit=10)
    result = SearchResult(uuid4(), uuid4(), NOW, "hello world")
    assert query.limit == 10 and result.excerpt == "hello world"
    with pytest.raises(ValueError):
        SearchQuery(" ")
