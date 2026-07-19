# PySide6 desktop interface

Task 18 replaces the placeholder client window with a PySide6 presentation layer
under `client/ui`. Views depend on Qt ViewModels only. ViewModels depend on the
`UiBackend` service boundary and never execute HTTP, SQLite, cryptography or
session logic. `CallbackUiBackend` composes the existing async application services
without allowing widgets to import them, while `UnavailableUiBackend` provides
clear offline/unconfigured states for independent UI startup and testing.

## Windows and navigation

The client starts at an accessible login window with server, username and password
validation, password clearing, inline errors and duplicate-submit prevention.
Successful backend authentication replaces it with a resizable shell based on the
approved wireframe: a branded top bar with explicit Exit, Help and current-page
navigation; a large blue chat workspace on the left; and a narrow searchable user
list on the right. The navigation menu retains every non-chat and authorised
administrative page without consuming permanent horizontal space. Geometry,
maximised state and navigation are restored only onto a valid screen.

The user list supports Most Recent, Alphabetical (Forename), Alphabetical
(Surname), Frequency, Date Added and New Messages orderings, plus an explicit
ascending/descending toggle. Filtering and ordering are local deterministic
projections: they never trigger storage or network work. Empty lists, single-word
names, missing date-added metadata and stable tie-breaks are tested.

The shell includes chats, contacts, groups, transfers, search, announcements,
settings, sessions and diagnostics. Authorised administration exposes dashboard,
users, connections, audit, alerts, workers, configuration and exports; pages and
buttons absent from the supplied permission set are not constructed. Page actions
run through the backend and every major page has loading, empty and error states.

## Messaging behavior

The chat page renders a bounded newest page of plain-text, wrapping message
bubbles. It displays sender, timestamp, edited marker, attachment summary,
verification warning and colour-independent pending/stored/delivered/read/failed/
deleted labels. Pending sends are inserted immediately but become stored only
after backend acknowledgement; failures remain visible with retry. Reply, edit,
confirmed deletion, encrypted draft preservation, file selection and keyboard send
are functional ViewModel operations. Selecting a file never sends it automatically.

Search is limited to locally authorised cached content. Transfers use accessible
progress bars and exact service progress. Settings provide light, dark and high
contrast themes, 75–200% font scaling, notification controls and confirmed
replaceable/all-local-data clearing. Session revocation and destructive message or
cache actions require confirmation.

## Responsiveness and desktop integration

`BackgroundTaskRunner` executes async service work in Qt's thread pool with a
worker-owned event loop and marshals results through Qt signals. Resize and theme
operations remain presentation-only. Important controls have stable object names
and accessible names. Ctrl-number navigation, Ctrl+F, Ctrl+Enter and Escape are
implemented. The system tray exposes open, connection, unread, pause
notifications, logout and exit actions. Notifications honour enabled, paused and
preview privacy state.

`tests/unit/client/test_task_18_viewmodels.py` verifies validation, navigation,
filtering/sorting, drafts, optimistic pending/stored/failed state, reply/edit,
attachment selection, search, settings, cache confirmation and sessions. Offscreen
widget tests verify stable identifiers, layout ordering, all sort controls,
accessibility text, page navigation, message wrapping, transfer progress, themes
and confirmations. Live screen-reader,
multi-monitor scaling and Windows notification appearance remain manual platform
acceptance checks rather than claims made by headless tests.
