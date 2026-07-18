"""Reusable accessible Qt widgets for messaging and service-backed pages."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from bluebubbles.client.ui.models import (
    MessageListItem,
    ThemeName,
    UiMessageState,
)
from bluebubbles.client.ui.viewmodels import DesktopViewModel


class StatePage(QWidget):
    """Provide consistent loading, empty, content and recoverable error states."""

    def __init__(
        self,
        title: str,
        description: str,
        *,
        action_label: str | None = None,
    ) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setProperty("heading", True)
        heading.setAccessibleName(f"{title} page")
        self.status = QLabel(description)
        self.status.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(self.status)
        self.action_button: QPushButton | None = None
        if action_label:
            self.action_button = QPushButton(action_label)
            self.action_button.setAccessibleName(action_label)
            layout.addWidget(self.action_button)
        layout.addStretch()

    def add_action(self, label: str) -> QPushButton:
        """Add a labelled action before the page's trailing stretch."""
        button = QPushButton(label)
        button.setAccessibleName(label)
        layout = self.layout()
        assert isinstance(layout, QVBoxLayout)
        layout.insertWidget(layout.count() - 1, button)
        return button

    def set_state(self, state: str) -> None:
        """Present a service result or safe error without closing other pages."""
        if state == "loading":
            self.status.setText("Loading…")
            self.status.setObjectName("")
        elif state == "empty":
            self.status.setText("There is nothing to show yet.")
            self.status.setObjectName("")
        elif state.startswith("error:"):
            self.status.setText(state.removeprefix("error:"))
            self.status.setObjectName("error_banner")
        elif state != "ready":
            self.status.setText(state)
            self.status.setObjectName("")
        self.style().unpolish(self.status)
        self.style().polish(self.status)


class ConversationPanel(QFrame):
    """Display filterable bounded conversation summaries in the middle column."""

    conversation_selected = Signal(str)

    def __init__(self, view_model: DesktopViewModel) -> None:
        super().__init__()
        self._view_model = view_model
        layout = QVBoxLayout(self)
        header = QLabel("Chats")
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Find a conversation")
        self.filter_input.setAccessibleName("Filter conversations")
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("conversation_list")
        self.list_widget.setAccessibleName("Conversation list")
        self.empty_label = QLabel("No conversations yet.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        layout.addWidget(self.filter_input)
        layout.addWidget(self.list_widget, 1)
        layout.addWidget(self.empty_label)
        self.filter_input.textChanged.connect(view_model.filter_conversations)
        self.list_widget.itemActivated.connect(self._select)
        self.list_widget.itemClicked.connect(self._select)
        view_model.conversations_changed.connect(self.reload)

    def reload(self) -> None:
        """Render current filtered summaries without querying storage."""
        self.list_widget.clear()
        for conversation in self._view_model.filtered_conversations:
            unread = (
                f" — {conversation.unread_count} unread"
                if conversation.unread_count
                else ""
            )
            item = QListWidgetItem(
                f"{conversation.title}{unread}\n"
                f"{conversation.preview or 'No messages yet'}"
            )
            item.setData(Qt.ItemDataRole.UserRole, str(conversation.conversation_id))
            item.setToolTip(
                f"{conversation.title}. {conversation.unread_count} unread messages."
            )
            self.list_widget.addItem(item)
        has_items = self.list_widget.count() > 0
        self.list_widget.setVisible(has_items)
        self.empty_label.setVisible(not has_items)

    def _select(self, item: QListWidgetItem) -> None:
        conversation_id = str(item.data(Qt.ItemDataRole.UserRole))
        self.conversation_selected.emit(conversation_id)


class MessageBubble(QFrame):
    """Render one plain-text message with explicit state and accessible actions."""

    reply_requested = Signal(str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    retry_requested = Signal(str)

    def __init__(self, message: MessageListItem) -> None:
        super().__init__()
        self._message = message
        self.setObjectName("message_own" if message.is_own else "message_other")
        layout = QVBoxLayout(self)
        sender = QLabel(message.sender_name)
        text = QLabel(message.text)
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        if message.state is UiMessageState.DELETED:
            text.setProperty("deleted", True)
        if message.reply_preview:
            reply = QLabel(f"Replying to: {message.reply_preview}")
            reply.setWordWrap(True)
            layout.addWidget(reply)
        layout.addWidget(sender)
        layout.addWidget(text)
        if message.attachment_name:
            attachment = QLabel(f"Attachment: {message.attachment_name}")
            attachment.setAccessibleName(f"Attachment {message.attachment_name}")
            layout.addWidget(attachment)
        if message.verification_warning:
            warning = QLabel(f"Verification warning: {message.verification_warning}")
            warning.setObjectName("error_banner")
            warning.setWordWrap(True)
            layout.addWidget(warning)
        suffix = " — edited" if message.edited else ""
        state = QLabel(
            f"{message.sent_at.astimezone().strftime('%H:%M')} — "
            f"{message.state.value.replace('_', ' ')}{suffix}"
        )
        layout.addWidget(state)
        actions = QHBoxLayout()
        reply_button = QPushButton("Reply")
        reply_button.clicked.connect(
            lambda: self.reply_requested.emit(str(message.message_id))
        )
        actions.addWidget(reply_button)
        if message.is_own and message.state not in {
            UiMessageState.DELETED,
            UiMessageState.FAILED,
        }:
            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(
                lambda: self.edit_requested.emit(str(message.message_id))
            )
            delete_button = QPushButton("Delete")
            delete_button.setObjectName("destructive_button")
            delete_button.clicked.connect(
                lambda: self.delete_requested.emit(str(message.message_id))
            )
            actions.addWidget(edit_button)
            actions.addWidget(delete_button)
        if message.state is UiMessageState.FAILED:
            retry_button = QPushButton("Retry")
            retry_button.clicked.connect(
                lambda: self.retry_requested.emit(str(message.message_id))
            )
            actions.addWidget(retry_button)
        actions.addStretch()
        layout.addLayout(actions)
        accessible = (
            f"Message from {message.sender_name}, {message.state.value}. {message.text}"
        )
        self.setAccessibleName(accessible)


class ChatPage(QWidget):
    """Display paged messages, draft-aware composer, reply, edit and attachments."""

    def __init__(self, view_model: DesktopViewModel) -> None:
        super().__init__()
        self._view_model = view_model
        layout = QVBoxLayout(self)
        self.header = QLabel("Select a conversation")
        self.state_label = QLabel("Choose a chat from the conversation list.")
        self.message_list = QListWidget()
        self.message_list.setObjectName("message_list")
        self.message_list.setAccessibleName("Messages")
        self.message_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.mode_label = QLabel("")
        self.mode_label.setVisible(False)
        self.attachment_label = QLabel("")
        self.attachment_label.setVisible(False)
        composer_row = QHBoxLayout()
        self.attachment_button = QPushButton("Attach")
        self.attachment_button.setAccessibleName("Choose attachments")
        self.composer = QTextEdit()
        self.composer.setObjectName("message_composer_input")
        self.composer.setAccessibleName("Message composer")
        self.composer.setPlaceholderText("Write a message")
        self.composer.setMaximumHeight(140)
        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("message_send_button")
        self.send_button.setProperty("primary", True)
        self.send_button.setAccessibleName("Send message")
        composer_row.addWidget(self.attachment_button)
        composer_row.addWidget(self.composer, 1)
        composer_row.addWidget(self.send_button)
        layout.addWidget(self.header)
        layout.addWidget(self.state_label)
        layout.addWidget(self.message_list, 1)
        layout.addWidget(self.mode_label)
        layout.addWidget(self.attachment_label)
        layout.addLayout(composer_row)
        self.composer.textChanged.connect(self._draft_changed)
        self.send_button.clicked.connect(self._send)
        self.attachment_button.clicked.connect(self._choose_attachments)
        view_model.messages_changed.connect(self.reload_messages)
        view_model.draft_changed.connect(self.restore_draft)
        view_model.page_state_changed.connect(self._page_state)
        self._update_send_state()

    def reload_messages(self) -> None:
        """Render only the newest bounded page of message widgets."""
        self.message_list.clear()
        for message in self._view_model.messages[-200:]:
            item = QListWidgetItem()
            bubble = MessageBubble(message)
            bubble.reply_requested.connect(lambda value: self._reply(UUID(value)))
            bubble.edit_requested.connect(lambda value: self._edit(UUID(value)))
            bubble.delete_requested.connect(lambda value: self._delete(UUID(value)))
            bubble.retry_requested.connect(
                lambda value: self._view_model.retry_message(UUID(value))
            )
            item.setSizeHint(bubble.sizeHint())
            self.message_list.addItem(item)
            self.message_list.setItemWidget(item, bubble)
        self.message_list.scrollToBottom()
        self.state_label.setVisible(not self._view_model.messages)
        self._update_send_state()

    def restore_draft(self, text: str) -> None:
        """Restore drafts and edit/reply context without recursive persistence."""
        if self.composer.toPlainText() != text:
            self.composer.blockSignals(True)
            self.composer.setPlainText(text)
            self.composer.blockSignals(False)
        if self._view_model.edit_target:
            mode = "Editing message — press Escape to cancel"
        elif self._view_model.reply_to:
            mode = "Replying to message — press Escape to cancel"
        else:
            mode = ""
        self.mode_label.setText(mode)
        self.mode_label.setVisible(bool(mode))
        attachments = self._view_model.attachments
        self.attachment_label.setText(
            ", ".join(path.name for path in attachments) if attachments else ""
        )
        self.attachment_label.setVisible(bool(attachments))
        self._update_send_state()

    def keyPressEvent(self, event) -> None:  # type: ignore[no-untyped-def]  # noqa: N802
        """Support Escape cancellation and Ctrl+Enter keyboard sending."""
        if event.key() == Qt.Key.Key_Escape:
            self._view_model.set_reply(None)
            self._view_model.set_edit(None)
            event.accept()
            return
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter} and (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self._send()
            event.accept()
            return
        super().keyPressEvent(event)

    def _draft_changed(self) -> None:
        self._view_model.update_draft(self.composer.toPlainText())
        self._update_send_state()

    def _send(self) -> None:
        self._view_model.send_message(self.composer.toPlainText())

    def _reply(self, message_id: UUID) -> None:
        self._view_model.set_reply(message_id)
        self.composer.setFocus()

    def _edit(self, message_id: UUID) -> None:
        self._view_model.set_edit(message_id)
        self.composer.setFocus()

    def _delete(self, message_id: UUID) -> None:
        answer = QMessageBox.question(
            self,
            "Delete message",
            "Delete this message? This action may affect other participants.",
        )
        if answer is QMessageBox.StandardButton.Yes:
            self._view_model.delete_message(message_id)

    def _choose_attachments(self) -> None:
        names, _selected_filter = QFileDialog.getOpenFileNames(
            self,
            "Choose attachments",
            "",
            "Allowed files (*);;Images (*.png *.jpg *.jpeg)",
        )
        if names:
            self._view_model.set_attachments(tuple(Path(name) for name in names))

    def _update_send_state(self) -> None:
        conversation = next(
            (
                item
                for item in self._view_model.conversations
                if item.conversation_id == self._view_model.active_conversation_id
            ),
            None,
        )
        has_content = bool(self.composer.toPlainText().strip()) or bool(
            self._view_model.attachments
        )
        self.send_button.setEnabled(
            has_content and conversation is not None and conversation.composer_enabled
        )

    def _page_state(self, page: str, state: str) -> None:
        if page != "chat":
            return
        if state == "loading":
            self.state_label.setText("Loading messages…")
        elif state == "empty":
            self.state_label.setText("No messages yet. Start the conversation.")
        elif state.startswith("error:"):
            self.state_label.setText(state.removeprefix("error:"))
            self.state_label.setObjectName("error_banner")


class TransferPage(QWidget):
    """Render accurate transfer states and progress values."""

    def __init__(self, view_model: DesktopViewModel) -> None:
        super().__init__()
        self._view_model = view_model
        self._rows_layout = QVBoxLayout(self)
        self._rows_layout.addWidget(QLabel("Transfers"))
        self.empty = QLabel("No transfers yet.")
        self._rows_layout.addWidget(self.empty)
        self._rows_layout.addStretch()
        view_model.transfers_changed.connect(self.reload)

    def reload(self) -> None:
        """Replace transfer rows with current ViewModel projections."""
        while self._rows_layout.count() > 2:
            item = self._rows_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        self.empty.setVisible(not self._view_model.transfers)
        for transfer in self._view_model.transfers:
            row = QWidget()
            row_layout = QVBoxLayout(row)
            row_layout.addWidget(
                QLabel(
                    f"{transfer.file_name} — {transfer.direction} — {transfer.state}"
                )
            )
            progress = QProgressBar()
            progress.setObjectName("transfer_progress_bar")
            progress.setRange(0, 100)
            progress.setValue(transfer.percentage)
            progress.setAccessibleName(
                f"{transfer.file_name} transfer progress {transfer.percentage}%"
            )
            row_layout.addWidget(progress)
            self._rows_layout.insertWidget(self._rows_layout.count() - 1, row)


class SearchPage(QWidget):
    """Search local authorised content and emit navigation targets."""

    result_activated = Signal(str)

    def __init__(self, view_model: DesktopViewModel) -> None:
        super().__init__()
        self._view_model = view_model
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Search cached messages"))
        row = QHBoxLayout()
        self.query = QLineEdit()
        self.query.setAccessibleName("Search query")
        self.button = QPushButton("Search")
        row.addWidget(self.query, 1)
        row.addWidget(self.button)
        self.results = QListWidget()
        self.empty = QLabel("Enter at least two characters.")
        layout.addLayout(row)
        layout.addWidget(self.results, 1)
        layout.addWidget(self.empty)
        self.button.clicked.connect(lambda: view_model.search(self.query.text()))
        self.query.returnPressed.connect(lambda: view_model.search(self.query.text()))
        self.results.itemActivated.connect(self._activated)
        view_model.search_changed.connect(self.reload)

    def reload(self) -> None:
        """Render bounded local search excerpts."""
        self.results.clear()
        for result in self._view_model.search_results:
            item = QListWidgetItem(
                f"{result.conversation_title} — {result.sender_name}\n{result.excerpt}"
            )
            item.setData(Qt.ItemDataRole.UserRole, str(result.conversation_id))
            self.results.addItem(item)
        self.empty.setText(
            "No cached messages matched." if not self._view_model.search_results else ""
        )
        self.empty.setVisible(not self._view_model.search_results)

    def _activated(self, item: QListWidgetItem) -> None:
        self.result_activated.emit(str(item.data(Qt.ItemDataRole.UserRole)))


class SettingsPage(QScrollArea):
    """Edit appearance, notification and storage preferences with confirmation."""

    def __init__(self, view_model: DesktopViewModel) -> None:
        super().__init__()
        self._view_model = view_model
        self.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.addWidget(QLabel("Settings"))
        self.theme = QComboBox()
        self.theme.addItem("Light", ThemeName.LIGHT.value)
        self.theme.addItem("Dark", ThemeName.DARK.value)
        self.theme.addItem("High contrast", ThemeName.HIGH_CONTRAST.value)
        self.theme.setAccessibleName("Theme")
        self.font_scale = QDoubleSpinBox()
        self.font_scale.setRange(0.75, 2.0)
        self.font_scale.setSingleStep(0.05)
        self.font_scale.setValue(1.0)
        self.font_scale.setAccessibleName("Font scale")
        self.notifications = QCheckBox("Enable desktop notifications")
        self.notifications.setChecked(True)
        save = QPushButton("Save settings")
        save.setObjectName("primary_button")
        clear_cache = QPushButton("Clear replaceable cache")
        clear_all = QPushButton("Clear all local data")
        clear_all.setObjectName("destructive_button")
        layout.addWidget(QLabel("Appearance"))
        layout.addWidget(self.theme)
        layout.addWidget(self.font_scale)
        layout.addWidget(QLabel("Notifications and privacy"))
        layout.addWidget(self.notifications)
        layout.addWidget(save)
        layout.addWidget(QLabel("Storage"))
        layout.addWidget(clear_cache)
        layout.addWidget(clear_all)
        layout.addStretch()
        self.setWidget(content)
        save.clicked.connect(self._save)
        clear_cache.clicked.connect(lambda: self._confirm_clear(False))
        clear_all.clicked.connect(lambda: self._confirm_clear(True))

    def _save(self) -> None:
        self._view_model.save_settings(
            {
                "theme": str(self.theme.currentData()),
                "font_scale": self.font_scale.value(),
                "notifications_enabled": self.notifications.isChecked(),
            }
        )

    def _confirm_clear(self, clear_all: bool) -> None:
        message = (
            "Clear all local data, including drafts and pending work?"
            if clear_all
            else "Clear replaceable cached messages and search data?"
        )
        answer = QMessageBox.question(self, "Confirm local data clearing", message)
        if answer is QMessageBox.StandardButton.Yes:
            self._view_model.clear_cache(clear_all=clear_all)


class SessionsPage(QWidget):
    """List sessions and confirm revocation of non-current entries."""

    def __init__(self, view_model: DesktopViewModel) -> None:
        super().__init__()
        self._view_model = view_model
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Sessions"))
        self.list_widget = QListWidget()
        self.list_widget.setAccessibleName("Active sessions")
        refresh = QPushButton("Refresh sessions")
        revoke = QPushButton("Revoke selected session")
        revoke.setObjectName("destructive_button")
        layout.addWidget(self.list_widget, 1)
        layout.addWidget(refresh)
        layout.addWidget(revoke)
        refresh.clicked.connect(view_model.load_sessions)
        revoke.clicked.connect(self._revoke)
        view_model.sessions_changed.connect(self.reload)

    def reload(self) -> None:
        self.list_widget.clear()
        for session in self._view_model.sessions:
            suffix = " — This device" if session.current else ""
            item = QListWidgetItem(f"{session.device_name}{suffix}")
            item.setData(Qt.ItemDataRole.UserRole, str(session.session_id))
            item.setData(int(Qt.ItemDataRole.UserRole) + 1, session.current)
            self.list_widget.addItem(item)

    def _revoke(self) -> None:
        item = self.list_widget.currentItem()
        if item is None or bool(item.data(int(Qt.ItemDataRole.UserRole) + 1)):
            return
        answer = QMessageBox.question(
            self,
            "Revoke session",
            "Revoke this session? The device will be signed out.",
        )
        if answer is QMessageBox.StandardButton.Yes:
            self._view_model.revoke_session(
                UUID(str(item.data(Qt.ItemDataRole.UserRole)))
            )
