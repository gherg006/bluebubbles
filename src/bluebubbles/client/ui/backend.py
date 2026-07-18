"""Asynchronous service boundary consumed only by desktop ViewModels."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path
from typing import Protocol
from uuid import UUID

from bluebubbles.client.ui.models import (
    ConversationListItem,
    MessageListItem,
    SearchListItem,
    SessionListItem,
    TransferListItem,
)


class UiBackend(Protocol):
    """Define service operations needed by presentation without SQL or networking."""

    async def authenticate(self, server: str, username: str, password: str) -> None: ...
    async def load_conversations(self) -> Sequence[ConversationListItem]: ...
    async def load_messages(
        self, conversation_id: UUID
    ) -> Sequence[MessageListItem]: ...
    async def send_message(
        self,
        conversation_id: UUID,
        message_id: UUID,
        text: str,
        reply_to: UUID | None,
        edit_target: UUID | None,
        attachments: tuple[Path, ...],
    ) -> None: ...
    async def save_draft(self, conversation_id: UUID, text: str) -> None: ...
    async def load_draft(self, conversation_id: UUID) -> str: ...
    async def search(self, query: str) -> Sequence[SearchListItem]: ...
    async def load_transfers(self) -> Sequence[TransferListItem]: ...
    async def load_sessions(self) -> Sequence[SessionListItem]: ...
    async def revoke_session(self, session_id: UUID) -> None: ...
    async def save_settings(self, values: dict[str, object]) -> None: ...
    async def clear_cache(self, clear_all: bool) -> None: ...
    async def perform_action(self, section: str, action: str) -> str: ...
    async def logout(self) -> None: ...


class UnavailableUiBackend:
    """Provide clear offline responses until authenticated services are attached."""

    async def authenticate(self, server: str, username: str, password: str) -> None:
        del server, username, password
        raise RuntimeError("The client networking service is not available.")

    async def load_conversations(self) -> Sequence[ConversationListItem]:
        return ()

    async def load_messages(self, conversation_id: UUID) -> Sequence[MessageListItem]:
        del conversation_id
        return ()

    async def send_message(
        self,
        conversation_id: UUID,
        message_id: UUID,
        text: str,
        reply_to: UUID | None,
        edit_target: UUID | None,
        attachments: tuple[Path, ...],
    ) -> None:
        del conversation_id, message_id, text, reply_to, edit_target, attachments
        raise RuntimeError("Connect and sign in before sending messages.")

    async def save_draft(self, conversation_id: UUID, text: str) -> None:
        del conversation_id, text

    async def load_draft(self, conversation_id: UUID) -> str:
        del conversation_id
        return ""

    async def search(self, query: str) -> Sequence[SearchListItem]:
        del query
        return ()

    async def load_transfers(self) -> Sequence[TransferListItem]:
        return ()

    async def load_sessions(self) -> Sequence[SessionListItem]:
        return ()

    async def revoke_session(self, session_id: UUID) -> None:
        del session_id
        raise RuntimeError("Session management is unavailable while offline.")

    async def save_settings(self, values: dict[str, object]) -> None:
        del values

    async def clear_cache(self, clear_all: bool) -> None:
        del clear_all
        raise RuntimeError("Open an authenticated local profile first.")

    async def perform_action(self, section: str, action: str) -> str:
        del section, action
        return "This information is unavailable while offline."

    async def logout(self) -> None:
        return None


class CallbackUiBackend(UnavailableUiBackend):
    """Compose existing application services through explicitly supplied callables."""

    def __init__(
        self,
        *,
        authenticate: Callable[[str, str, str], Awaitable[None]] | None = None,
        load_conversations: (
            Callable[[], Awaitable[Sequence[ConversationListItem]]] | None
        ) = None,
        load_messages: (
            Callable[[UUID], Awaitable[Sequence[MessageListItem]]] | None
        ) = None,
        send_message: (
            Callable[
                [UUID, UUID, str, UUID | None, UUID | None, tuple[Path, ...]],
                Awaitable[None],
            ]
            | None
        ) = None,
        save_draft: Callable[[UUID, str], Awaitable[None]] | None = None,
        load_draft: Callable[[UUID], Awaitable[str]] | None = None,
        search: Callable[[str], Awaitable[Sequence[SearchListItem]]] | None = None,
        save_settings: Callable[[dict[str, object]], Awaitable[None]] | None = None,
        clear_cache: Callable[[bool], Awaitable[None]] | None = None,
        logout: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        self._authenticate = authenticate
        self._load_conversations = load_conversations
        self._load_messages = load_messages
        self._send_message = send_message
        self._save_draft = save_draft
        self._load_draft = load_draft
        self._search = search
        self._save_settings = save_settings
        self._clear_cache = clear_cache
        self._logout = logout

    async def authenticate(self, server: str, username: str, password: str) -> None:
        if self._authenticate is None:
            await super().authenticate(server, username, password)
            return
        await self._authenticate(server, username, password)

    async def load_conversations(self) -> Sequence[ConversationListItem]:
        if self._load_conversations is None:
            return await super().load_conversations()
        return await self._load_conversations()

    async def load_messages(self, conversation_id: UUID) -> Sequence[MessageListItem]:
        if self._load_messages is None:
            return await super().load_messages(conversation_id)
        return await self._load_messages(conversation_id)

    async def send_message(
        self,
        conversation_id: UUID,
        message_id: UUID,
        text: str,
        reply_to: UUID | None,
        edit_target: UUID | None,
        attachments: tuple[Path, ...],
    ) -> None:
        if self._send_message is None:
            await super().send_message(
                conversation_id,
                message_id,
                text,
                reply_to,
                edit_target,
                attachments,
            )
            return
        await self._send_message(
            conversation_id,
            message_id,
            text,
            reply_to,
            edit_target,
            attachments,
        )

    async def save_draft(self, conversation_id: UUID, text: str) -> None:
        if self._save_draft is None:
            await super().save_draft(conversation_id, text)
            return
        await self._save_draft(conversation_id, text)

    async def load_draft(self, conversation_id: UUID) -> str:
        if self._load_draft is None:
            return await super().load_draft(conversation_id)
        return await self._load_draft(conversation_id)

    async def search(self, query: str) -> Sequence[SearchListItem]:
        if self._search is None:
            return await super().search(query)
        return await self._search(query)

    async def save_settings(self, values: dict[str, object]) -> None:
        if self._save_settings is None:
            await super().save_settings(values)
            return
        await self._save_settings(values)

    async def clear_cache(self, clear_all: bool) -> None:
        if self._clear_cache is None:
            await super().clear_cache(clear_all)
            return
        await self._clear_cache(clear_all)

    async def logout(self) -> None:
        if self._logout is None:
            await super().logout()
            return
        await self._logout()
