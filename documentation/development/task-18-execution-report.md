# Task 18 execution report

## Completion boundary

Task 18 implements the login window, authenticated three-column shell, complete
required page set, conversation filtering, chat bubbles, drafts, pending and failed
states, reply/edit/confirmed delete, attachment selection, transfers, local search,
announcements, settings, sessions, diagnostics, permission-filtered administration,
themes, accessibility metadata, keyboard shortcuts, desktop notifications, system
tray, tests and focused documentation.

## Architecture decisions

- Widgets depend only on ViewModels. `UiBackend` is the composition boundary for
  existing authentication, messaging, storage, search, transfer and administration
  services; `CallbackUiBackend` keeps those integrations explicit and testable.
- All async backend operations run outside the GUI thread. Qt signals marshal only
  result objects or safe error messages back to the presentation thread.
- The UI never invents stored, delivered or read state. A send begins pending and
  changes to stored only after service acknowledgement.
- Administrative pages are constructed only when their named capability is
  supplied. Server-side authorisation remains mandatory.
- Theme, resize, filtering and page switching are presentation-only operations.
  Plaintext is not logged or placed in widget identifiers.

## Verification evidence

Focused targets are `test_task_18_viewmodels.py`, `test_task_18_widgets.py` and
`test_application.py`. Offscreen Qt tests cover login, field identifiers,
navigation, filtering, message state, draft restoration, reply/edit, attachment
selection, transfer progress, search, settings, cache confirmation, session
revocation, permission visibility, themes, wrapping and accessible labels. The
mandatory repository quality runner completed successfully: Black and Ruff were
clean, strict mypy checked 310 source files, pytest reported 289 passed and 3
intentional real-PostgreSQL skips, and branch-aware coverage was 90.10%.

## Manual platform checks

Headless Qt can verify semantics and geometry constraints but cannot prove Windows
screen-reader speech, tray placement, native notification appearance, certificate
dialogs on a real server, or DPI changes across physical monitors. These remain
explicit manual acceptance checks; the implementation does not claim otherwise.
