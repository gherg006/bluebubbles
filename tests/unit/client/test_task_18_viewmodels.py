"""Task 18 ViewModel validation, optimistic state and service isolation tests."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from bluebubbles.client.ui.backend import CallbackUiBackend, UnavailableUiBackend
from bluebubbles.client.ui.models import (
    ConversationListItem,
    ConversationSort,
    MessageListItem,
    NavigationSection,
    SearchListItem,
    SessionListItem,
    ThemeName,
    UiMessageState,
)
from bluebubbles.client.ui.viewmodels import DesktopViewModel, LoginViewModel


class ImmediateTaskRunner:
    """Run ViewModel coroutines immediately for deterministic tests."""

    def submit(
        self,
        operation: Callable[[], Coroutine[Any, Any, object]],
        success: Callable[[object], None],
        failure: Callable[[str], None],
    ) -> None:
        try:
            result = asyncio.run(operation())
        except Exception as error:
            failure(str(error))
        else:
            success(result)


class FakeBackend(UnavailableUiBackend):
    """Capture presentation requests at the service boundary."""

    def __init__(self) -> None:
        self.authenticated = False
        self.fail_send = False
        self.saved_drafts: list[tuple[UUID, str]] = []
        self.sent: list[tuple[UUID, UUID, str]] = []
        self.settings: dict[str, object] = {}
        self.cleared: list[bool] = []
        self.revoked: list[UUID] = []
        self.conversation_id = uuid4()
        self.message_id = uuid4()

    async def authenticate(self, server: str, username: str, password: str) -> None:
        assert server.startswith("https://") and username == "alex" and password
        self.authenticated = True

    async def load_conversations(self) -> Sequence[ConversationListItem]:
        now = datetime.now(UTC)
        return (
            ConversationListItem(
                self.conversation_id, "Project Team", "Updated plan", now, 2, True
            ),
            ConversationListItem(uuid4(), "Morgan", "Hello", now),
        )

    async def load_messages(self, conversation_id: UUID) -> Sequence[MessageListItem]:
        return (
            MessageListItem(
                self.message_id,
                conversation_id,
                "Morgan",
                "Existing message",
                datetime.now(UTC),
                UiMessageState.READ,
            ),
        )

    async def load_draft(self, conversation_id: UUID) -> str:
        assert conversation_id == self.conversation_id
        return "Restored draft"

    async def save_draft(self, conversation_id: UUID, text: str) -> None:
        self.saved_drafts.append((conversation_id, text))

    async def send_message(
        self,
        conversation_id: UUID,
        message_id: UUID,
        text: str,
        reply_to: UUID | None,
        edit_target: UUID | None,
        attachments: tuple[Path, ...],
    ) -> None:
        del reply_to, edit_target, attachments
        self.sent.append((conversation_id, message_id, text))
        if self.fail_send:
            raise RuntimeError("Server unavailable; the message remains queued.")

    async def search(self, query: str) -> Sequence[SearchListItem]:
        return (
            SearchListItem(
                self.message_id,
                self.conversation_id,
                "Project Team",
                "Morgan",
                f"Match for {query}",
                datetime.now(UTC),
            ),
        )

    async def save_settings(self, values: dict[str, object]) -> None:
        self.settings = values

    async def clear_cache(self, clear_all: bool) -> None:
        self.cleared.append(clear_all)

    async def load_sessions(self) -> Sequence[SessionListItem]:
        return (
            SessionListItem(
                uuid4(), "Office PC", datetime.now(UTC), datetime.now(UTC), True
            ),
            SessionListItem(
                uuid4(), "Laptop", datetime.now(UTC), datetime.now(UTC), False
            ),
        )

    async def revoke_session(self, session_id: UUID) -> None:
        self.revoked.append(session_id)


def test_login_validation_busy_and_success() -> None:
    backend = FakeBackend()
    view_model = LoginViewModel(backend, ImmediateTaskRunner())
    assert not view_model.submit("", "", "")
    assert "server" in view_model.error_message.lower()
    assert view_model.submit("https://server:8443", "alex", "secret")
    assert backend.authenticated
    assert not view_model.busy
    assert view_model.error_message == ""


def test_navigation_filter_and_administration_visibility() -> None:
    backend = FakeBackend()
    view_model = DesktopViewModel(backend, ImmediateTaskRunner())
    view_model.load_conversations()
    view_model.filter_conversations("project")
    assert [item.title for item in view_model.filtered_conversations] == [
        "Project Team"
    ]
    view_model.navigate(NavigationSection.SEARCH)
    assert view_model.navigation is NavigationSection.SEARCH
    with pytest.raises(PermissionError):
        view_model.navigate(NavigationSection.ADMINISTRATION)

    authorised = DesktopViewModel(
        backend,
        ImmediateTaskRunner(),
        administrative_sections=frozenset({NavigationSection.ADMINISTRATION}),
    )
    authorised.navigate(NavigationSection.ADMINISTRATION)


def test_conversation_sort_modes_direction_and_filter_are_deterministic() -> None:
    backend = FakeBackend()
    view_model = DesktopViewModel(backend, ImmediateTaskRunner())
    now = datetime.now(UTC)
    earlier = now - timedelta(days=365)
    view_model.conversations = [
        ConversationListItem(
            uuid4(),
            "Zoe Adams",
            "alpha",
            earlier,
            unread_count=0,
            message_frequency=9,
            date_added_at=now,
        ),
        ConversationListItem(
            uuid4(),
            "Alex Young",
            "beta",
            now,
            unread_count=4,
            message_frequency=1,
            date_added_at=earlier,
        ),
        ConversationListItem(uuid4(), "Morgan", "gamma", now, unread_count=2),
    ]

    expectations = {
        ConversationSort.MOST_RECENT: "Morgan",
        ConversationSort.FORENAME: "Alex Young",
        ConversationSort.SURNAME: "Zoe Adams",
        ConversationSort.FREQUENCY: "Zoe Adams",
        ConversationSort.DATE_ADDED: "Zoe Adams",
        ConversationSort.NEW_MESSAGES: "Alex Young",
    }
    for ordering, expected_first in expectations.items():
        view_model.set_conversation_sort(ordering)
        assert view_model.filtered_conversations[0].title == expected_first

    view_model.toggle_conversation_sort_direction()
    assert view_model.filtered_conversations[0].title == "Zoe Adams"
    view_model.filter_conversations("GAMMA")
    assert [item.title for item in view_model.filtered_conversations] == ["Morgan"]
    view_model.filter_conversations("no match")
    assert view_model.filtered_conversations == []
    view_model.conversations.append(
        ConversationListItem(uuid4(), "", "blank title", earlier)
    )
    view_model.filter_conversations("")
    view_model.set_conversation_sort(ConversationSort.SURNAME)
    assert view_model.filtered_conversations[0].title == ""


def test_draft_reply_edit_pending_stored_and_failed_message(tmp_path: Path) -> None:
    backend = FakeBackend()
    view_model = DesktopViewModel(backend, ImmediateTaskRunner())
    view_model.load_conversations()
    view_model.select_conversation(backend.conversation_id)
    assert view_model.draft == "Restored draft"
    view_model.update_draft("New draft")
    assert backend.saved_drafts[-1] == (backend.conversation_id, "New draft")

    attachment = tmp_path / "document.txt"
    attachment.write_text("content", encoding="utf-8")
    view_model.set_reply(backend.message_id)
    view_model.set_attachments((attachment,))
    sent_id = view_model.send_message("Reply text")
    assert sent_id is not None
    assert view_model.messages[-1].state is UiMessageState.STORED
    assert backend.sent[-1][2] == "Reply text"

    backend.fail_send = True
    failed_id = view_model.send_message("Will queue")
    failed = next(item for item in view_model.messages if item.message_id == failed_id)
    assert failed.state is UiMessageState.FAILED

    view_model.set_edit(backend.message_id)
    assert view_model.draft == "Existing message"


def test_search_settings_cache_and_session_flows() -> None:
    backend = FakeBackend()
    view_model = DesktopViewModel(backend, ImmediateTaskRunner())
    assert not view_model.search("x")
    assert view_model.search("plan")
    assert view_model.search_results[0].excerpt == "Match for plan"

    view_model.save_settings({"theme": ThemeName.DARK.value, "font_scale": 1.5})
    assert view_model.theme is ThemeName.DARK
    assert view_model.font_scale == 1.5
    assert backend.settings["theme"] == "dark"
    with pytest.raises(ValueError):
        view_model.save_settings({"font_scale": 3.0})

    view_model.clear_cache(clear_all=False)
    assert backend.cleared == [False]
    view_model.load_sessions()
    target = next(item for item in view_model.sessions if not item.current)
    view_model.revoke_session(target.session_id)
    assert backend.revoked == [target.session_id]
    assert all(item.session_id != target.session_id for item in view_model.sessions)


@pytest.mark.asyncio
async def test_unavailable_backend_returns_safe_empty_and_error_states() -> None:
    backend = UnavailableUiBackend()
    with pytest.raises(RuntimeError, match="networking service"):
        await backend.authenticate("server", "user", "password")
    assert await backend.load_conversations() == ()
    assert await backend.load_messages(uuid4()) == ()
    with pytest.raises(RuntimeError, match="sign in"):
        await backend.send_message(uuid4(), uuid4(), "text", None, None, ())
    await backend.save_draft(uuid4(), "draft")
    assert await backend.load_draft(uuid4()) == ""
    assert await backend.search("query") == ()
    assert await backend.load_transfers() == ()
    assert await backend.load_sessions() == ()
    with pytest.raises(RuntimeError, match="offline"):
        await backend.revoke_session(uuid4())
    await backend.save_settings({})
    with pytest.raises(RuntimeError, match="profile"):
        await backend.clear_cache(False)
    assert "unavailable" in await backend.perform_action("page", "refresh")
    await backend.logout()


@pytest.mark.asyncio
async def test_callback_backend_delegates_every_composed_operation() -> None:
    calls: list[str] = []
    conversation_id, message_id = uuid4(), uuid4()

    async def authenticate(server: str, username: str, password: str) -> None:
        calls.append(f"auth:{server}:{username}:{password}")

    async def conversations() -> Sequence[ConversationListItem]:
        calls.append("conversations")
        return ()

    async def messages(selected: UUID) -> Sequence[MessageListItem]:
        calls.append(f"messages:{selected}")
        return ()

    async def send(
        selected: UUID,
        selected_message: UUID,
        text: str,
        reply: UUID | None,
        edit: UUID | None,
        attachments: tuple[Path, ...],
    ) -> None:
        del reply, edit, attachments
        calls.append(f"send:{selected}:{selected_message}:{text}")

    async def save_draft(selected: UUID, text: str) -> None:
        calls.append(f"draft:{selected}:{text}")

    async def load_draft(selected: UUID) -> str:
        calls.append(f"load-draft:{selected}")
        return "draft"

    async def search(query: str) -> Sequence[SearchListItem]:
        calls.append(f"search:{query}")
        return ()

    async def save_settings(values: dict[str, object]) -> None:
        calls.append(f"settings:{len(values)}")

    async def clear(clear_all: bool) -> None:
        calls.append(f"clear:{clear_all}")

    async def logout() -> None:
        calls.append("logout")

    backend = CallbackUiBackend(
        authenticate=authenticate,
        load_conversations=conversations,
        load_messages=messages,
        send_message=send,
        save_draft=save_draft,
        load_draft=load_draft,
        search=search,
        save_settings=save_settings,
        clear_cache=clear,
        logout=logout,
    )
    await backend.authenticate("server", "user", "password")
    await backend.load_conversations()
    await backend.load_messages(conversation_id)
    await backend.send_message(conversation_id, message_id, "hello", None, None, ())
    await backend.save_draft(conversation_id, "draft")
    assert await backend.load_draft(conversation_id) == "draft"
    await backend.search("term")
    await backend.save_settings({"theme": "dark"})
    await backend.clear_cache(True)
    await backend.logout()
    assert len(calls) == 10


def test_viewmodel_error_recovery_delete_retry_transfer_action_and_logout() -> None:
    backend = FakeBackend()
    view_model = DesktopViewModel(backend, ImmediateTaskRunner())
    errors: list[tuple[str, str]] = []
    view_model.page_state_changed.connect(
        lambda page, state: errors.append((page, state))
    )
    view_model.update_draft("No active conversation")
    assert view_model.send_message("No active conversation") is None
    with pytest.raises(ValueError, match="existing files"):
        view_model.set_attachments((Path("missing.file"),))

    view_model.load_conversations()
    view_model.select_conversation(backend.conversation_id)
    view_model.delete_message(backend.message_id)
    deleted = next(
        item for item in view_model.messages if item.message_id == backend.message_id
    )
    assert deleted.state is UiMessageState.DELETED
    view_model.retry_message(backend.message_id)
    retried = next(
        item for item in view_model.messages if item.message_id == backend.message_id
    )
    assert retried.state is UiMessageState.PENDING
    view_model.load_transfers()
    view_model.run_page_action(NavigationSection.DIAGNOSTICS, "refresh")
    logged_out: list[bool] = []
    view_model.logged_out.connect(lambda: logged_out.append(True))
    view_model.logout()
    assert logged_out == [True]
    assert view_model.messages == []
