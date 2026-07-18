"""Qt ViewModels coordinating presentation state with injected services."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from PySide6.QtCore import QObject, Signal

from bluebubbles.client.domain.synchronisation import ConnectivityState
from bluebubbles.client.ui.backend import UiBackend
from bluebubbles.client.ui.models import (
    ConversationListItem,
    MessageListItem,
    NavigationSection,
    SearchListItem,
    SessionListItem,
    ThemeName,
    TransferListItem,
    UiMessageState,
)
from bluebubbles.client.ui.tasks import TaskRunner


class LoginViewModel(QObject):
    """Validate login input and execute authentication outside the GUI thread."""

    state_changed = Signal()
    authenticated = Signal()

    def __init__(self, backend: UiBackend, runner: TaskRunner) -> None:
        super().__init__()
        self._backend = backend
        self._runner = runner
        self.busy = False
        self.error_message = ""

    def submit(self, server: str, username: str, password: str) -> bool:
        """Validate fields, begin authentication and report whether work started."""
        if self.busy:
            return False
        server, username = server.strip(), username.strip()
        if not server:
            self.error_message = "Enter the BlueBubbles server address."
        elif not username:
            self.error_message = "Enter your username."
        elif not password:
            self.error_message = "Enter your password."
        else:
            self.error_message = ""
        if self.error_message:
            self.state_changed.emit()
            return False
        self.busy = True
        self.state_changed.emit()

        async def authenticate() -> object:
            await self._backend.authenticate(server, username, password)
            return None

        self._runner.submit(authenticate, self._authentication_succeeded, self._failed)
        return True

    def _authentication_succeeded(self, result: object) -> None:
        del result
        self.busy = False
        self.error_message = ""
        self.state_changed.emit()
        self.authenticated.emit()

    def _failed(self, message: str) -> None:
        self.busy = False
        self.error_message = message
        self.state_changed.emit()


class DesktopViewModel(QObject):
    """Own desktop presentation state while delegating all business operations."""

    navigation_changed = Signal(str)
    connection_changed = Signal(str)
    conversations_changed = Signal()
    messages_changed = Signal()
    draft_changed = Signal(str)
    transfers_changed = Signal()
    search_changed = Signal()
    sessions_changed = Signal()
    theme_changed = Signal(str)
    page_state_changed = Signal(str, str)
    toast_requested = Signal(str)
    logged_out = Signal()

    def __init__(
        self,
        backend: UiBackend,
        runner: TaskRunner,
        *,
        administrative_sections: frozenset[NavigationSection] = frozenset(),
    ) -> None:
        super().__init__()
        self._backend = backend
        self._runner = runner
        self.navigation = NavigationSection.CHATS
        self.connection_state = ConnectivityState.STARTING
        self.theme = ThemeName.LIGHT
        self.font_scale = 1.0
        self.administrative_sections = administrative_sections
        self.conversations: list[ConversationListItem] = []
        self.filtered_conversations: list[ConversationListItem] = []
        self.messages: list[MessageListItem] = []
        self.transfers: list[TransferListItem] = []
        self.search_results: list[SearchListItem] = []
        self.sessions: list[SessionListItem] = []
        self.active_conversation_id: UUID | None = None
        self.reply_to: UUID | None = None
        self.edit_target: UUID | None = None
        self.draft = ""
        self.attachments: tuple[Path, ...] = ()

    def navigate(self, section: NavigationSection) -> None:
        """Select an authorised section and publish a stable route value."""
        is_administrative = section.value.startswith("admin") or section in {
            NavigationSection.ADMIN_USERS,
            NavigationSection.ADMIN_CONNECTIONS,
            NavigationSection.ADMIN_AUDIT,
            NavigationSection.ADMIN_ALERTS,
            NavigationSection.ADMIN_WORKERS,
            NavigationSection.ADMIN_CONFIGURATION,
            NavigationSection.ADMIN_EXPORTS,
        }
        if is_administrative and section not in self.administrative_sections:
            raise PermissionError("This administrative page is not authorised.")
        self.navigation = section
        self.navigation_changed.emit(section.value)

    def set_connection_state(self, state: ConnectivityState) -> None:
        """Publish an explicit colour-independent connectivity label."""
        self.connection_state = state
        self.connection_changed.emit(state.value)

    def load_conversations(self) -> None:
        """Load bounded summaries through the asynchronous backend boundary."""
        self.page_state_changed.emit(NavigationSection.CHATS.value, "loading")

        async def load() -> object:
            return list(await self._backend.load_conversations())

        self._runner.submit(
            load, self._conversations_loaded, self._page_failure("chats")
        )

    def filter_conversations(self, query: str) -> None:
        """Apply local title/preview filtering without storage or network work."""
        value = query.strip().casefold()
        self.filtered_conversations = [
            item
            for item in self.conversations
            if not value
            or value in item.title.casefold()
            or value in item.preview.casefold()
        ]
        self.conversations_changed.emit()

    def select_conversation(self, conversation_id: UUID) -> None:
        """Load one conversation's messages and encrypted draft through services."""
        self.active_conversation_id = conversation_id
        self.reply_to = self.edit_target = None
        self.attachments = ()
        self.page_state_changed.emit("chat", "loading")

        async def load() -> object:
            messages = list(await self._backend.load_messages(conversation_id))
            draft = await self._backend.load_draft(conversation_id)
            return messages, draft

        self._runner.submit(load, self._conversation_loaded, self._page_failure("chat"))

    def update_draft(self, text: str) -> None:
        """Preserve the active draft through the encrypted storage service."""
        self.draft = text
        self.draft_changed.emit(text)
        conversation_id = self.active_conversation_id
        if conversation_id is None:
            return

        async def save() -> object:
            await self._backend.save_draft(conversation_id, text)
            return None

        self._runner.submit(save, lambda _result: None, self._draft_failure)

    def set_reply(self, message_id: UUID | None) -> None:
        """Select or clear the current reply target."""
        self.reply_to = message_id
        self.edit_target = None
        self.draft_changed.emit(self.draft)

    def set_edit(self, message_id: UUID | None) -> None:
        """Select an editable own message and restore its text to the composer."""
        self.edit_target = message_id
        self.reply_to = None
        if message_id is not None:
            message = next(
                (item for item in self.messages if item.message_id == message_id), None
            )
            if message is not None:
                self.draft = message.text
        self.draft_changed.emit(self.draft)

    def set_attachments(self, paths: tuple[Path, ...]) -> None:
        """Store validated file selections without sending automatically."""
        if any(not path.is_file() for path in paths):
            raise ValueError("Only existing files can be attached.")
        self.attachments = paths
        self.draft_changed.emit(self.draft)

    def send_message(self, text: str) -> UUID | None:
        """Insert a pending item and submit it without fabricating acknowledgement."""
        conversation_id = self.active_conversation_id
        clean_text = text.strip()
        if conversation_id is None or (not clean_text and not self.attachments):
            return None
        message_id = self.edit_target or uuid4()
        pending = MessageListItem(
            message_id,
            conversation_id,
            "You",
            clean_text,
            datetime.now(UTC),
            UiMessageState.PENDING,
            is_own=True,
            edited=self.edit_target is not None,
            reply_preview="Reply" if self.reply_to else None,
            attachment_name=self.attachments[0].name if self.attachments else None,
        )
        if self.edit_target is None:
            self.messages.append(pending)
        else:
            self.messages = [
                pending if item.message_id == self.edit_target else item
                for item in self.messages
            ]
        reply_to, edit_target, attachments = (
            self.reply_to,
            self.edit_target,
            self.attachments,
        )
        self.draft = ""
        self.reply_to = self.edit_target = None
        self.attachments = ()
        self.messages_changed.emit()
        self.draft_changed.emit("")

        async def send() -> object:
            await self._backend.send_message(
                conversation_id,
                message_id,
                clean_text,
                reply_to,
                edit_target,
                attachments,
            )
            return message_id

        self._runner.submit(
            send, self._message_stored, self._message_failed(message_id)
        )
        return message_id

    def delete_message(self, message_id: UUID) -> None:
        """Request server deletion and show a placeholder only after success."""

        async def delete() -> object:
            await self._backend.perform_action("messages", f"delete:{message_id}")
            return message_id

        def deleted(result: object) -> None:
            deleted_id = UUID(str(result))
            self.messages = [
                (
                    replace(item, state=UiMessageState.DELETED, text="Message deleted")
                    if item.message_id == deleted_id
                    else item
                )
                for item in self.messages
            ]
            self.messages_changed.emit()

        self._runner.submit(delete, deleted, self._message_failed(message_id))

    def retry_message(self, message_id: UUID) -> None:
        """Request retry through the durable queue interface."""

        async def retry() -> object:
            await self._backend.perform_action("messages", f"retry:{message_id}")
            return message_id

        def retrying(result: object) -> None:
            retried_id = UUID(str(result))
            self.messages = [
                (
                    replace(item, state=UiMessageState.PENDING)
                    if item.message_id == retried_id
                    else item
                )
                for item in self.messages
            ]
            self.messages_changed.emit()

        self._runner.submit(retry, retrying, self._message_failed(message_id))

    def search(self, query: str) -> bool:
        """Search locally cached authorised content for a meaningful query."""
        query = query.strip()
        if len(query) < 2:
            self.search_results = []
            self.search_changed.emit()
            return False
        self.page_state_changed.emit("search", "loading")

        async def run() -> object:
            return list(await self._backend.search(query))

        self._runner.submit(run, self._search_loaded, self._page_failure("search"))
        return True

    def load_transfers(self) -> None:
        """Load resumable transfer projections without touching local paths."""
        self.page_state_changed.emit("transfers", "loading")

        async def load() -> object:
            return list(await self._backend.load_transfers())

        self._runner.submit(
            load, self._transfers_loaded, self._page_failure("transfers")
        )

    def save_settings(self, values: dict[str, object]) -> None:
        """Persist validated settings and immediately apply presentation choices."""
        theme_value = values.get("theme")
        if isinstance(theme_value, str):
            self.theme = ThemeName(theme_value)
            self.theme_changed.emit(self.theme.value)
        scale = values.get("font_scale")
        if isinstance(scale, int | float):
            if not 0.75 <= float(scale) <= 2.0:
                raise ValueError("Font scale must be between 75% and 200%.")
            self.font_scale = float(scale)

        async def save() -> object:
            await self._backend.save_settings(values)
            return None

        self._runner.submit(
            save,
            lambda _result: self.toast_requested.emit("Settings saved."),
            self._page_failure("settings"),
        )

    def clear_cache(self, *, clear_all: bool = False) -> None:
        """Request confirmed cache clearing through the storage service."""

        async def clear() -> object:
            await self._backend.clear_cache(clear_all)
            return None

        self._runner.submit(
            clear,
            lambda _result: self.toast_requested.emit("Local data cleared."),
            self._page_failure("settings"),
        )

    def load_sessions(self) -> None:
        """Load the authenticated user's active session list."""

        async def load() -> object:
            return list(await self._backend.load_sessions())

        self._runner.submit(load, self._sessions_loaded, self._page_failure("sessions"))

    def revoke_session(self, session_id: UUID) -> None:
        """Revoke a non-current session after confirmation in the view."""

        async def revoke() -> object:
            await self._backend.revoke_session(session_id)
            return session_id

        self._runner.submit(
            revoke, self._session_revoked, self._page_failure("sessions")
        )

    def run_page_action(self, section: NavigationSection, action: str) -> None:
        """Run diagnostics or authorised administration actions through services."""
        self.page_state_changed.emit(section.value, "loading")

        async def run() -> object:
            return await self._backend.perform_action(section.value, action)

        self._runner.submit(
            run, self._action_completed(section), self._page_failure(section.value)
        )

    def logout(self) -> None:
        """Dispose authenticated state before returning to login."""

        async def perform() -> object:
            await self._backend.logout()
            return None

        self._runner.submit(
            perform, self._logout_complete, self._page_failure("logout")
        )

    def _conversations_loaded(self, result: object) -> None:
        self.conversations = list(cast(list[ConversationListItem], result))
        self.filtered_conversations = list(self.conversations)
        self.conversations_changed.emit()
        self.page_state_changed.emit("chats", "ready" if result else "empty")

    def _conversation_loaded(self, result: object) -> None:
        messages, draft = cast(tuple[list[MessageListItem], str], result)
        self.messages = list(messages)
        self.draft = str(draft)
        self.messages_changed.emit()
        self.draft_changed.emit(self.draft)
        self.page_state_changed.emit("chat", "ready" if messages else "empty")

    def _message_stored(self, result: object) -> None:
        message_id = UUID(str(result))
        self.messages = [
            (
                replace(item, state=UiMessageState.STORED)
                if item.message_id == message_id
                else item
            )
            for item in self.messages
        ]
        self.messages_changed.emit()

    def _message_failed(self, message_id: UUID):  # type: ignore[no-untyped-def]
        def failed(message: str) -> None:
            self.messages = [
                (
                    replace(item, state=UiMessageState.FAILED)
                    if item.message_id == message_id
                    else item
                )
                for item in self.messages
            ]
            self.messages_changed.emit()
            self.toast_requested.emit(message)

        return failed

    def _search_loaded(self, result: object) -> None:
        self.search_results = list(cast(list[SearchListItem], result))
        self.search_changed.emit()
        self.page_state_changed.emit("search", "ready" if result else "empty")

    def _transfers_loaded(self, result: object) -> None:
        self.transfers = list(cast(list[TransferListItem], result))
        self.transfers_changed.emit()
        self.page_state_changed.emit("transfers", "ready" if result else "empty")

    def _sessions_loaded(self, result: object) -> None:
        self.sessions = list(cast(list[SessionListItem], result))
        self.sessions_changed.emit()
        self.page_state_changed.emit("sessions", "ready" if result else "empty")

    def _session_revoked(self, result: object) -> None:
        session_id = UUID(str(result))
        self.sessions = [
            item for item in self.sessions if item.session_id != session_id
        ]
        self.sessions_changed.emit()
        self.toast_requested.emit("Session revoked.")

    def _action_completed(self, section: NavigationSection):  # type: ignore[no-untyped-def]
        def complete(result: object) -> None:
            self.page_state_changed.emit(section.value, str(result))

        return complete

    def _page_failure(self, page: str):  # type: ignore[no-untyped-def]
        def failed(message: str) -> None:
            self.page_state_changed.emit(page, f"error:{message}")

        return failed

    def _draft_failure(self, message: str) -> None:
        self.toast_requested.emit(f"Draft could not be saved: {message}")

    def _logout_complete(self, result: object) -> None:
        del result
        self.messages = []
        self.conversations = []
        self.filtered_conversations = []
        self.search_results = []
        self.sessions = []
        self.draft = ""
        self.active_conversation_id = None
        self.logged_out.emit()
