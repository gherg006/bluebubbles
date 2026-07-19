"""Login and authenticated three-column desktop windows."""

from __future__ import annotations

from uuid import UUID

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from bluebubbles.client.domain.synchronisation import ConnectivityState
from bluebubbles.client.ui.models import NavigationSection, ThemeName
from bluebubbles.client.ui.system_integration import SystemTrayManager
from bluebubbles.client.ui.themes import ThemeManager
from bluebubbles.client.ui.viewmodels import DesktopViewModel, LoginViewModel
from bluebubbles.client.ui.widgets import (
    ChatPage,
    ConversationPanel,
    SearchPage,
    SessionsPage,
    SettingsPage,
    StatePage,
    TransferPage,
)


class LoginWindow(QMainWindow):
    """Collect server credentials with inline validation and a busy state."""

    def __init__(
        self,
        view_model: LoginViewModel,
        *,
        application_name: str = "BlueBubbles",
        default_server: str = "",
    ) -> None:
        super().__init__()
        self._view_model = view_model
        self.setWindowTitle(application_name)
        self.setMinimumSize(440, 500)
        self.resize(480, 560)
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(48, 40, 48, 40)
        title = QLabel(application_name)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Secure messaging on your organisation's network")
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.server_input = QLineEdit(default_server)
        self.server_input.setObjectName("login_server_input")
        self.server_input.setAccessibleName("Server address")
        self.server_input.setPlaceholderText("https://server.example:8443")
        self.username_input = QLineEdit()
        self.username_input.setObjectName("login_username_input")
        self.username_input.setAccessibleName("Username")
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit()
        self.password_input.setObjectName("login_password_input")
        self.password_input.setAccessibleName("Password")
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.error_banner = QLabel("")
        self.error_banner.setObjectName("error_banner")
        self.error_banner.setWordWrap(True)
        self.error_banner.setVisible(False)
        self.submit_button = QPushButton("Sign in")
        self.submit_button.setObjectName("login_submit_button")
        self.submit_button.setAccessibleName("Sign in")
        self.submit_button.setProperty("primary", True)
        self.offline_help = QLabel(
            "Already used this device? Cached data remains encrypted and offline "
            "access "
            "depends on your organisation's policy."
        )
        self.offline_help.setWordWrap(True)
        for widget in (
            title,
            subtitle,
            self.server_input,
            self.username_input,
            self.password_input,
            self.error_banner,
            self.submit_button,
            self.offline_help,
        ):
            layout.addWidget(widget)
        layout.addStretch()
        self.setCentralWidget(central)
        self.setTabOrder(self.server_input, self.username_input)
        self.setTabOrder(self.username_input, self.password_input)
        self.setTabOrder(self.password_input, self.submit_button)
        self.submit_button.clicked.connect(self._submit)
        self.password_input.returnPressed.connect(self._submit)
        view_model.state_changed.connect(self._refresh_state)

    def _submit(self) -> None:
        password = self.password_input.text()
        self._view_model.submit(
            self.server_input.text(), self.username_input.text(), password
        )
        self.password_input.clear()

    def _refresh_state(self) -> None:
        self.submit_button.setEnabled(not self._view_model.busy)
        self.submit_button.setText(
            "Signing in…" if self._view_model.busy else "Sign in"
        )
        self.server_input.setEnabled(not self._view_model.busy)
        self.username_input.setEnabled(not self._view_model.busy)
        self.password_input.setEnabled(not self._view_model.busy)
        self.error_banner.setText(self._view_model.error_message)
        self.error_banner.setVisible(bool(self._view_model.error_message))
        if self._view_model.error_message:
            self.error_banner.setFocus()


class NavigationHeader(QFrame):
    """Expose branded top-level navigation matching the supplied wireframe."""

    section_selected = Signal(str)
    exit_requested = Signal()
    help_requested = Signal()

    _ORDINARY = (
        (NavigationSection.CHATS, "Chats", "Ctrl+1"),
        (NavigationSection.CONTACTS, "Contacts", "Ctrl+2"),
        (NavigationSection.GROUPS, "Groups", "Ctrl+3"),
        (NavigationSection.TRANSFERS, "Transfers", "Ctrl+4"),
        (NavigationSection.SEARCH, "Search", "Ctrl+5"),
        (NavigationSection.ANNOUNCEMENTS, "Announcements", "Ctrl+6"),
        (NavigationSection.SETTINGS, "Settings", "Ctrl+,"),
        (NavigationSection.SESSIONS, "Sessions", "Ctrl+7"),
        (NavigationSection.DIAGNOSTICS, "Diagnostics", "Ctrl+8"),
    )

    def __init__(self, view_model: DesktopViewModel) -> None:
        super().__init__()
        self.setObjectName("navigation_header")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        self.brand = QLabel("[logo] BlueBubbles")
        self.brand.setObjectName("application_brand")
        self.brand.setAccessibleName("BlueBubbles home")
        layout.addWidget(self.brand)
        layout.addStretch()

        self.exit_button = QPushButton("Exit")
        self.exit_button.setObjectName("exit_button")
        self.exit_button.setAccessibleName("Exit BlueBubbles")
        self.help_button = QPushButton("Help")
        self.help_button.setObjectName("help_button")
        self.help_button.setAccessibleName("Open help")
        self.navigation_button = QPushButton("Chat user")
        self.navigation_button.setObjectName("navigation_menu_button")
        self.navigation_button.setAccessibleName("Open navigation menu")
        self.navigation_menu = QMenu(self.navigation_button)
        self.navigation_button.setMenu(self.navigation_menu)
        self.navigation_actions: dict[NavigationSection, QAction] = {}
        for section, label, shortcut in self._ORDINARY:
            self._add_action(section, label, shortcut)
        if NavigationSection.ADMINISTRATION in view_model.administrative_sections:
            self._add_action(
                NavigationSection.ADMINISTRATION,
                "Administration",
                "Ctrl+9",
            )
        self.navigation_menu.addSeparator()
        logout = self.navigation_menu.addAction("Log out")
        logout.triggered.connect(view_model.logout)
        layout.addWidget(self.exit_button)
        layout.addWidget(self.help_button)
        layout.addWidget(self.navigation_button)
        self.exit_button.clicked.connect(self.exit_requested.emit)
        self.help_button.clicked.connect(self.help_requested.emit)
        self.select(NavigationSection.CHATS)

    def select(self, section: NavigationSection) -> None:
        """Synchronise the menu and its compact current-section label."""
        action = self.navigation_actions.get(section)
        if action is None:
            return
        for candidate in self.navigation_actions.values():
            candidate.setChecked(candidate is action)
        self.navigation_button.setText(action.text())

    def set_chat_context(self, title: str) -> None:
        """Expose the selected user in the reference-layout chat control."""
        self.navigation_button.setText(f"Chat {title}")

    def _add_action(
        self,
        section: NavigationSection,
        label: str,
        shortcut: str,
    ) -> None:
        action = QAction(label, self)
        action.setCheckable(True)
        action.setShortcut(QKeySequence(shortcut))
        action.setToolTip(f"{label} ({shortcut})")
        action.triggered.connect(
            lambda _checked=False, value=section: self.section_selected.emit(
                value.value
            )
        )
        self.navigation_actions[section] = action
        self.addAction(action)
        self.navigation_menu.addAction(action)


class MainWindow(QMainWindow):
    """Coordinate the authenticated three-column shell and presentation state."""

    return_to_login = Signal()

    def __init__(
        self,
        application: QApplication,
        view_model: DesktopViewModel,
        *,
        application_name: str = "BlueBubbles",
        settings: QSettings | None = None,
        close_to_tray: bool = True,
    ) -> None:
        super().__init__()
        self._application = application
        self._view_model = view_model
        self._settings = settings or QSettings("BlueBubbles", "BlueBubbles")
        self._close_to_tray = close_to_tray
        self.setWindowTitle(application_name)
        self.setMinimumSize(900, 560)
        self.resize(1280, 800)
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        self.header_bar = NavigationHeader(view_model)
        self.connection_banner = QLabel("Starting…")
        self.connection_banner.setObjectName("connection_banner")
        self.connection_banner.setAccessibleName("Connection status")
        body = QHBoxLayout()
        self.conversations = ConversationPanel(view_model)
        self.conversations.setMinimumWidth(260)
        self.conversations.setMaximumWidth(340)
        self.content = QStackedWidget()
        body.addWidget(self.content, 4)
        body.addWidget(self.conversations, 1)
        root_layout.addWidget(self.header_bar)
        root_layout.addWidget(self.connection_banner)
        root_layout.addLayout(body, 1)
        self.setCentralWidget(root)
        self._pages: dict[NavigationSection, QWidget] = {}
        self.chat_page = ChatPage(view_model)
        self._add_page(NavigationSection.CHATS, self.chat_page)
        self._add_state_page(
            NavigationSection.CONTACTS,
            "Contacts",
            "Select a cached contact to view their authorised profile.",
            "Refresh contacts",
        )
        contacts = self._pages[NavigationSection.CONTACTS]
        assert isinstance(contacts, StatePage)
        contacts.add_action("Start direct conversation").clicked.connect(
            lambda: view_model.run_page_action(
                NavigationSection.CONTACTS, "start_conversation"
            )
        )
        self._add_state_page(
            NavigationSection.GROUPS,
            "Groups",
            "Groups and current membership will appear here.",
            "Refresh groups",
        )
        groups = self._pages[NavigationSection.GROUPS]
        assert isinstance(groups, StatePage)
        groups.add_action("Create group").clicked.connect(
            lambda: view_model.run_page_action(NavigationSection.GROUPS, "create")
        )
        self._add_page(NavigationSection.TRANSFERS, TransferPage(view_model))
        search = SearchPage(view_model)
        search.result_activated.connect(self._open_search_result)
        self._add_page(NavigationSection.SEARCH, search)
        self._add_state_page(
            NavigationSection.ANNOUNCEMENTS,
            "Announcements",
            "Organisation announcements will appear here.",
            "Refresh announcements",
        )
        announcements = self._pages[NavigationSection.ANNOUNCEMENTS]
        assert isinstance(announcements, StatePage)
        announcements.add_action("Acknowledge selected announcement").clicked.connect(
            lambda: view_model.run_page_action(
                NavigationSection.ANNOUNCEMENTS, "acknowledge_selected"
            )
        )
        self._add_page(NavigationSection.SETTINGS, SettingsPage(view_model))
        self._add_page(NavigationSection.SESSIONS, SessionsPage(view_model))
        self._add_state_page(
            NavigationSection.DIAGNOSTICS,
            "Diagnostics",
            "Run privacy-safe connectivity and local storage checks.",
            "Run diagnostics",
        )
        self._build_administration_pages()
        self.header_bar.section_selected.connect(self._navigate_value)
        self.header_bar.exit_requested.connect(self._exit_application)
        self.header_bar.help_requested.connect(self._show_help)
        self.conversations.conversation_selected.connect(self._select_conversation)
        view_model.navigation_changed.connect(self._navigation_changed)
        view_model.connection_changed.connect(self._connection_changed)
        view_model.page_state_changed.connect(self._page_state_changed)
        view_model.theme_changed.connect(self._theme_changed)
        view_model.toast_requested.connect(self.statusBar().showMessage)
        view_model.logged_out.connect(self._logout_complete)
        self.theme_manager = ThemeManager(application)
        self.theme_manager.apply(view_model.theme, view_model.font_scale)
        self.tray = SystemTrayManager(application, self, logout=view_model.logout)
        self._install_actions()
        self._restore_window_state()
        view_model.set_connection_state(ConnectivityState.CONNECTING)
        view_model.load_conversations()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """Persist valid geometry and optionally hide to the configured tray."""
        self._save_window_state()
        if self._close_to_tray and self.tray.tray.isVisible():
            self.hide()
            event.ignore()
            return
        event.accept()

    def _add_page(self, section: NavigationSection, page: QWidget) -> None:
        self._pages[section] = page
        self.content.addWidget(page)

    def _add_state_page(
        self,
        section: NavigationSection,
        title: str,
        description: str,
        action_label: str,
    ) -> None:
        page = StatePage(title, description, action_label=action_label)
        assert page.action_button is not None
        page.action_button.clicked.connect(
            lambda _checked=False, value=section: self._view_model.run_page_action(
                value, "refresh"
            )
        )
        self._add_page(section, page)

    def _build_administration_pages(self) -> None:
        admin_pages = (
            (NavigationSection.ADMINISTRATION, "Administration dashboard"),
            (NavigationSection.ADMIN_USERS, "User administration"),
            (NavigationSection.ADMIN_CONNECTIONS, "Active connections"),
            (NavigationSection.ADMIN_AUDIT, "Audit events and integrity"),
            (NavigationSection.ADMIN_ALERTS, "Security alerts"),
            (NavigationSection.ADMIN_WORKERS, "Worker status"),
            (NavigationSection.ADMIN_CONFIGURATION, "Configuration"),
            (NavigationSection.ADMIN_EXPORTS, "Exports"),
        )
        for section, title in admin_pages:
            if section not in self._view_model.administrative_sections:
                continue
            self._add_state_page(
                section,
                title,
                "Authorised metadata is loaded without message or attachment "
                "plaintext.",
                "Refresh",
            )
        hub = self._pages.get(NavigationSection.ADMINISTRATION)
        if isinstance(hub, StatePage):
            for section, title in admin_pages[1:]:
                if section not in self._pages:
                    continue
                hub.add_action(f"Open {title}").clicked.connect(
                    lambda _checked=False, value=section: self._view_model.navigate(
                        value
                    )
                )

    def _install_actions(self) -> None:
        focus_search = QAction("Focus search", self)
        focus_search.setShortcut(QKeySequence("Ctrl+F"))
        focus_search.triggered.connect(self._focus_search)
        self.addAction(focus_search)

    def _navigate_value(self, value: str) -> None:
        try:
            self._view_model.navigate(NavigationSection(value))
        except PermissionError as error:
            self.statusBar().showMessage(str(error), 5000)

    def _navigation_changed(self, value: str) -> None:
        section = NavigationSection(value)
        page = self._pages.get(section)
        if page is None:
            return
        self.content.setCurrentWidget(page)
        self.header_bar.select(section)
        self.conversations.setVisible(section is NavigationSection.CHATS)
        if section is NavigationSection.TRANSFERS:
            self._view_model.load_transfers()
        elif section is NavigationSection.SESSIONS:
            self._view_model.load_sessions()

    def _select_conversation(self, value: str) -> None:
        conversation_id = UUID(value)
        conversation = next(
            (
                item
                for item in self._view_model.conversations
                if item.conversation_id == conversation_id
            ),
            None,
        )
        self.chat_page.header.setText(
            conversation.title if conversation else "Conversation"
        )
        self.header_bar.set_chat_context(conversation.title if conversation else "user")
        self._view_model.select_conversation(conversation_id)

    def _show_help(self) -> None:
        QMessageBox.information(
            self,
            "BlueBubbles help",
            "Choose a user on the right, type a message at the bottom, and use "
            "the Chat menu for contacts, groups, transfers, settings and support.",
        )

    def _exit_application(self) -> None:
        self._close_to_tray = False
        self.close()
        self._application.quit()

    def _open_search_result(self, value: str) -> None:
        self._view_model.navigate(NavigationSection.CHATS)
        self._select_conversation(value)

    def _connection_changed(self, value: str) -> None:
        labels = {
            "connected": "Connected",
            "synchronising": "Synchronising — cached data remains available",
            "offline": "Offline — messages will wait for connection",
            "degraded": "Connected with limited services",
            "reauthentication_required": "Sign in again to continue",
            "connecting": "Connecting…",
            "starting": "Starting…",
            "shutting_down": "Shutting down…",
        }
        self.connection_banner.setText(
            labels.get(value, value.replace("_", " ").title())
        )
        self.connection_banner.setVisible(value != ConnectivityState.CONNECTED.value)
        self.tray.update_connection(value)

    def _page_state_changed(self, page: str, state: str) -> None:
        try:
            section = NavigationSection(page)
        except ValueError:
            return
        widget = self._pages.get(section)
        if isinstance(widget, StatePage):
            widget.set_state(state)

    def _theme_changed(self, value: str) -> None:
        self.theme_manager.apply(ThemeName(value), self._view_model.font_scale)

    def _focus_search(self) -> None:
        if self._view_model.navigation is NavigationSection.CHATS:
            self.conversations.filter_input.setFocus()
        else:
            self._view_model.navigate(NavigationSection.SEARCH)

    def _logout_complete(self) -> None:
        self.hide()
        self.return_to_login.emit()

    def _save_window_state(self) -> None:
        self._settings.setValue("window/geometry", self.saveGeometry())
        self._settings.setValue("window/maximised", self.isMaximized())
        self._settings.setValue("window/navigation", self._view_model.navigation.value)

    def _restore_window_state(self) -> None:
        geometry = self._settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        visible = any(
            screen.availableGeometry().intersects(self.frameGeometry())
            for screen in self._application.screens()
        )
        primary = self._application.primaryScreen()
        if not visible and primary is not None:
            self.move(primary.availableGeometry().topLeft())
        if bool(self._settings.value("window/maximised", False, bool)):
            self.showMaximized()
        saved = str(self._settings.value("window/navigation", "chats"))
        try:
            section = NavigationSection(saved)
            self._view_model.navigate(section)
        except (ValueError, PermissionError):
            self._view_model.navigate(NavigationSection.CHATS)
