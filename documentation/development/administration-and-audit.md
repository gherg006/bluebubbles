# Administration and audit

Task 19 adds authenticated administration under `/api/v1/admin`. Every route is a
thin transport boundary over a service. Permissions are fixed `resource.action`
values seeded through migration `0007_admin_monitoring`; the capability response
is a presentation hint and never replaces server-side permission checks.

## Transaction and safety rules

User enablement, role changes, alert transitions, configuration revisions,
announcements and export requests append their audit event in the same Unit of
Work as the state change. Disabling a user and revoking a session commit before
WebSocket disconnection. The last enabled SuperAdministrator and the current
administrator are protected from unsafe disable or demotion operations.

Audit rows are append-only, monotonically sequenced and SHA-256 hash-linked over
canonical JSON including the sequence number. The writer redacts keys associated
with plaintext, passwords, tokens, secrets and private keys. Recent verification
checks a bounded suffix and predecessor; full verification checks the entire
chain. Both verify sequence continuity, links, event hashes and chain-head state.

Security alerts are content-free, deduplicated by stable code and reopen on
recurrence. Acknowledge and resolve transitions require permission; resolution
requires investigation notes. Configuration updates accept only an explicit
secret-free allowlist and use optimistic revision checks.

## Exports and bootstrap

Audit CSV/JSON exports are queued only after the request and audit record commit.
Files are written atomically beneath the configured export root, formula-prefixed
CSV values are escaped, ownership and expiry are checked on every access, and
downloads are audited. The lifecycle-owned export worker stops with the server.

Run `bluebubbles-create-admin` interactively after applying migrations and system
seeds. It confirms intent, hides and confirms the password, creates no default
password, validates LDAP credentials when directory authentication is configured,
assigns the fixed Administrator role and records the creation in the audit chain.
It refuses to create a second enabled initial Administrator.

## Administrative surfaces

The API covers capabilities, dashboard, users, roles, sessions, connections,
audit query/verification/export, alerts, workers, configuration, announcements,
health, maintenance and diagnostics. Task 18's permission-filtered administration
pages consume these capability boundaries; authority remains on the server.

Tests are concentrated in `tests/unit/server/test_task_19_administration.py`, the
SQLAlchemy support tests and migration tests. They cover tamper detection,
redaction, last-SuperAdministrator policy, commit-before-disconnect, alert state,
configuration conflicts, exports, bootstrap creation and every route.
