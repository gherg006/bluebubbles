# Task 09 execution report

## Completion boundary

Authentication and sessions are implemented on the Task 08 lifecycle and Task 07
transaction boundary. This stage owns identity providers, password verification,
login attempt control, user synchronisation at login, access and refresh tokens,
server sessions, revocation, permission checks, authentication routes, Windows
client secret storage, client login/session services, migration, tests, and focused
documentation. Messaging, general client HTTP transport, WebSockets, workers,
client SQLite, encryption-key movement, and GUI login presentation remain in their
numbered stages.

## Delivered changes

- Provider-neutral credentials and identities with LDAP, optional local, and mock
  adapters; production prohibits local/mock authentication.
- Certificate-validating LDAPS/StartTLS, escaped user filters, separate user binds,
  account-enabled parsing, bounded operations, and topology-free health.
- Argon2id hashing, verification, parameter-change detection, and safe rehash.
- Strict HS256 access tokens plus 256-bit opaque refresh tokens, hashed-only server
  persistence, rotation, versioning, expiry, and immediate reuse detection.
- Durable per-username and per-source failed-login controls and password-free audit
  metadata.
- Atomic login-time directory synchronisation, session creation, successful-attempt
  evidence, audit-chain append, and explicit Unit-of-Work commit.
- Server-side access validation, current permission resolution, logout, logout-all,
  user-owned session visibility and revocation, and post-commit socket notification
  seam.
- Thin FastAPI routes and shared safe error envelopes.
- Windows Credential Manager adapter plus client login/session services that retain
  access tokens only in memory and refresh tokens only in protected storage.
- Alembic revision `0002_refresh_reuse` and updated deployment
  configuration examples.

## Compatibility and security decisions

The initial schema already contained users, credentials, attempts, roles,
permissions, and sessions. One forward nullable column was added because the
existing schema could reject an old refresh value but could not safely distinguish
immediate reuse from arbitrary invalid input. This avoids allowing knowledge of a
session UUID alone to invalidate a victim's session.

Token signing uses only the specification-approved Version 1.0 HS256 profile and
rejects algorithm substitution. Access tokens carry no profile or permission list;
permissions are re-read from the database. Existing local-account roles are
preserved, while directory roles come only from configured group mappings. No raw
token, password, LDAP credential, private key, or message content is persisted or
logged.

## Verification evidence

The repository-owned quality runner completed successfully on 17 July 2026:

| Exit check | Result |
|---|---|
| Black formatting | Passed; 210 Python files unchanged |
| Ruff linting | Passed; no issues |
| Strict mypy | Passed for 210 source, test, script, and migration files |
| Automated tests | 187 passed, 3 skipped; 190 collected |
| Branch-aware coverage | 91.34%, above the required 90% |
| Development server executable configuration | Passed |
| Alembic head | `0002_refresh_reuse` |
| Git whitespace validation | Passed |

The Windows Credential Manager adapter also completed a real temporary
set/get/delete round trip. The credential was deleted in a `finally` cleanup path.
A focused placeholder scan found no TODO, `NotImplemented`, or empty method body in
the Task 09 packages.

## Environment-bound verification

Real PostgreSQL workflows require an already migrated dedicated database named by
`BLUEBUBBLES_TEST_DATABASE_URL`; no administrator database or SQLite substitute is
used. Live LDAP is deliberately not required by automated tests. A deployment must
validate its own directory certificate chain, service-account least privilege,
group mappings, and dedicated test account before production acceptance.

The three skips are the opt-in real PostgreSQL repository, Unit-of-Work, and
server-lifecycle workflows. No implementation defect is known. The ldap3 dependency
emits two upstream pyasn1 deprecation warnings during test collection; they do not
affect authentication behavior or the locked dependency set.
