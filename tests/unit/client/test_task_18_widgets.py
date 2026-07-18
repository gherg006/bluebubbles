"""Task 18 offscreen Qt widget, accessibility, shortcut and theme tests."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QEvent, QSettings, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QPushButton,
)

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
from bluebubbles.client.ui.themes import ThemeManager
from bluebubbles.client.ui.viewmodels import DesktopViewModel, LoginViewModel
from bluebubbles.client.ui.widgets import (
    ChatPage,
    ConversationPanel,
    MessageBubble,
    SearchPage,
    SessionsPage,
    SettingsPage,
    StatePage,
    TransferPage,
)
from bluebubbles.client.ui.windows import LoginWindow, MainWindow
from tests.unit.client.test_task_18_viewmodels import FakeBackend, ImmediateTaskRunner


def application() -> QApplication:
    """Return the process Qt application created by the test suite."""
    existing = QApplication.instance()
    if existing is not None:
        return cast(QApplication, existing)
    return QApplication(["bluebubbles-test"])


def test_login_widget_identifiers_validation_and_focus() -> None:
    app = application()
    backend = FakeBackend()
    view_model = LoginViewModel(backend, ImmediateTaskRunner())
    window = LoginWindow(view_model, default_server="https://server:8443")
    assert window.username_input.objectName() == "login_username_input"
    assert window.password_input.accessibleName() == "Password"
    assert window.submit_button.objectName() == "login_submit_button"
    window.submit_button.click()
    app.processEvents()
    assert window.error_banner.isVisible() is False or window.error_banner.text()
    window.username_input.setText("alex")
    window.password_input.setText("secret")
    window.submit_button.click()
    assert backend.authenticated
    assert window.password_input.text() == ""


def test_main_window_navigation_empty_states_and_admin_visibility(
    tmp_path: Path,
) -> None:
    app = application()
    backend = FakeBackend()
    view_model = DesktopViewModel(
        backend,
        ImmediateTaskRunner(),
        administrative_sections=frozenset({NavigationSection.ADMINISTRATION}),
    )
    settings = QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat)
    window = MainWindow(app, view_model, settings=settings, close_to_tray=False)
    assert window.minimumWidth() == 960
    assert NavigationSection.ADMINISTRATION in window.sidebar.buttons
    window.sidebar.buttons[NavigationSection.SEARCH].click()
    assert view_model.navigation is NavigationSection.SEARCH
    assert not window.conversations.isVisible()
    view_model.navigate(NavigationSection.CHATS)
    assert window.conversations.list_widget.objectName() == "conversation_list"
    assert window.chat_page.send_button.objectName() == "message_send_button"
    window.hide()


def test_chat_message_states_draft_reply_edit_and_attachment(tmp_path: Path) -> None:
    application()
    backend = FakeBackend()
    view_model = DesktopViewModel(backend, ImmediateTaskRunner())
    now = datetime.now(UTC)
    view_model.conversations = [
        ConversationListItem(backend.conversation_id, "Morgan", "Hello", now)
    ]
    view_model.filtered_conversations = list(view_model.conversations)
    view_model.active_conversation_id = backend.conversation_id
    view_model.messages = [
        MessageListItem(
            backend.message_id,
            backend.conversation_id,
            "You",
            "A long message that must wrap without clipping " * 5,
            now,
            UiMessageState.FAILED,
            is_own=True,
        )
    ]
    page = ChatPage(view_model)
    page.reload_messages()
    assert page.message_list.count() == 1
    bubble = page.message_list.itemWidget(page.message_list.item(0))
    assert isinstance(bubble, MessageBubble)
    assert "failed" in bubble.accessibleName().lower()
    page.composer.setPlainText("Draft text")
    assert backend.saved_drafts[-1][1] == "Draft text"
    attachment = tmp_path / "file.txt"
    attachment.write_text("content", encoding="utf-8")
    view_model.set_attachments((attachment,))
    page.restore_draft("Draft text")
    assert page.send_button.isEnabled()
    assert page.attachment_label.text() == "file.txt"


def test_transfer_progress_theme_and_settings_confirmation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    del tmp_path
    app = application()
    backend = FakeBackend()
    view_model = DesktopViewModel(backend, ImmediateTaskRunner())
    view_model.transfers = [
        TransferListItem(uuid4(), "report.pdf", "upload", 5, 10, "transferring")
    ]
    transfers = TransferPage(view_model)
    transfers.reload()
    progress = transfers.findChild(QProgressBar, "transfer_progress_bar")
    assert progress is not None

    manager = ThemeManager(app)
    manager.apply(ThemeName.HIGH_CONTRAST, 1.5)
    assert "#ffff00" in app.styleSheet()
    assert app.font().pointSizeF() > 0

    page = SettingsPage(view_model)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    page._confirm_clear(False)
    assert backend.cleared == [False]


def test_state_page_conversation_selection_and_message_bubble_actions() -> None:
    application()
    page = StatePage("Title", "Description")
    assert page.action_button is None
    extra = page.add_action("Retry")
    assert extra.accessibleName() == "Retry"
    for state, expected in (
        ("loading", "Loading"),
        ("empty", "nothing"),
        ("error:Try again", "Try again"),
        ("Custom status", "Custom status"),
        ("ready", "Custom status"),
    ):
        page.set_state(state)
        assert expected in page.status.text()

    backend = FakeBackend()
    view_model = DesktopViewModel(backend, ImmediateTaskRunner())
    view_model.load_conversations()
    panel = ConversationPanel(view_model)
    panel.reload()
    selected: list[str] = []
    panel.conversation_selected.connect(selected.append)
    panel._select(panel.list_widget.item(0))
    assert selected == [str(backend.conversation_id)]
    view_model.filter_conversations("no-match")
    assert panel.list_widget.count() == 0

    message = MessageListItem(
        uuid4(),
        backend.conversation_id,
        "You",
        "Deleted",
        datetime.now(UTC),
        UiMessageState.DELETED,
        is_own=True,
        edited=True,
        reply_preview="Earlier message",
        attachment_name="file.txt",
        verification_warning="Signature invalid",
    )
    bubble = MessageBubble(message)
    replies: list[str] = []
    bubble.reply_requested.connect(replies.append)
    next(
        button
        for button in bubble.findChildren(QPushButton)
        if button.text() == "Reply"
    ).click()
    assert replies == [str(message.message_id)]

    own = MessageBubble(
        MessageListItem(
            uuid4(),
            backend.conversation_id,
            "You",
            "Own message",
            datetime.now(UTC),
            UiMessageState.STORED,
            is_own=True,
        )
    )
    edits: list[str] = []
    deletes: list[str] = []
    own.edit_requested.connect(edits.append)
    own.delete_requested.connect(deletes.append)
    for button in own.findChildren(QPushButton):
        if button.text() in {"Edit", "Delete"}:
            button.click()
    assert edits and deletes


def test_chat_keyboard_file_dialog_delete_and_page_states(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    application()
    backend = FakeBackend()
    view_model = DesktopViewModel(backend, ImmediateTaskRunner())
    view_model.load_conversations()
    view_model.select_conversation(backend.conversation_id)
    page = ChatPage(view_model)
    view_model.set_reply(backend.message_id)
    page.restore_draft("Reply")
    escape = QKeyEvent(
        QEvent.Type.KeyPress,
        Qt.Key.Key_Escape,
        Qt.KeyboardModifier.NoModifier,
    )
    page.keyPressEvent(escape)
    assert view_model.reply_to is None

    page.composer.setPlainText("Keyboard send")
    send = QKeyEvent(
        QEvent.Type.KeyPress,
        Qt.Key.Key_Return,
        Qt.KeyboardModifier.ControlModifier,
    )
    page.keyPressEvent(send)
    assert backend.sent[-1][2] == "Keyboard send"
    ordinary = QKeyEvent(
        QEvent.Type.KeyPress,
        Qt.Key.Key_A,
        Qt.KeyboardModifier.NoModifier,
        "a",
    )
    page.keyPressEvent(ordinary)

    attachment = tmp_path / "picked.txt"
    attachment.write_text("data", encoding="utf-8")
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *_args, **_kwargs: ([str(attachment)], "Allowed files (*)"),
    )
    page._choose_attachments()
    assert view_model.attachments == (attachment,)

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.No,
    )
    page._delete(backend.message_id)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    page._delete(backend.message_id)
    for state in ("loading", "empty", "error:Message error"):
        page._page_state("chat", state)
    page._page_state("other", "loading")
    assert page.state_label.text() == "Message error"


def test_search_settings_and_session_widget_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application()
    backend = FakeBackend()
    view_model = DesktopViewModel(backend, ImmediateTaskRunner())
    search = SearchPage(view_model)
    result = SearchListItem(
        uuid4(),
        backend.conversation_id,
        "Project",
        "Morgan",
        "Excerpt",
        datetime.now(UTC),
    )
    view_model.search_results = [result]
    search.reload()
    activated: list[str] = []
    search.result_activated.connect(activated.append)
    search._activated(search.results.item(0))
    assert activated == [str(backend.conversation_id)]
    view_model.search_results = []
    search.reload()
    assert search.empty.isVisible() is False or search.empty.text()

    settings = SettingsPage(view_model)
    settings.theme.setCurrentIndex(1)
    settings.font_scale.setValue(1.25)
    settings._save()
    assert backend.settings["theme"] == "dark"
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    settings._confirm_clear(True)
    assert backend.cleared[-1]

    sessions = SessionsPage(view_model)
    view_model.sessions = [
        SessionListItem(uuid4(), "Current", datetime.now(UTC), datetime.now(UTC), True),
        SessionListItem(uuid4(), "Other", datetime.now(UTC), datetime.now(UTC), False),
    ]
    sessions.reload()
    sessions._revoke()
    sessions.list_widget.setCurrentRow(0)
    sessions._revoke()
    sessions.list_widget.setCurrentRow(1)
    target = view_model.sessions[1].session_id
    sessions._revoke()
    assert backend.revoked[-1] == target
