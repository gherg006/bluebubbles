# Authentication and sessions

Task 09 activates the identity and session schema from Task 05 through explicit
provider, service, repository, API, and client-secret boundaries. The server remains
the authority: a signed access token is accepted only while its database session is
active, its token version matches, and its user remains enabled.

## Provider boundary

`AuthenticationProvider` exchanges a representation-safe `LoginCredentials` value
for a provider-neutral `DirectoryUser`. LDAP objects and submitted passwords never
leave the provider. Three adapters exist:

- `LDAPAuthenticationProvider` uses a least-privileged search bind, library LDAP
  filter escaping, certificate-validating LDAPS or StartTLS, bounded search/bind
  timeouts, Active Directory account-state parsing, and safe failure translation.
- `LocalAuthenticationProvider` is configuration-gated, reads only the local user
  and verifier through a fresh Unit of Work, verifies Argon2id, and upgrades an old
  verifier after a successful login. Production validation prohibits it.
- `MockAuthenticationProvider` provides deterministic users, disabled accounts,
  outage, and delay behavior by constructor injection. Production validation
  prohibits it and bootstrap supplies no synthetic accounts.

At login, usernames are trimmed and case-folded. Configured `DOMAIN\\username` and
UPN suffixes are accepted without altering the password. Directory attributes are
synchronised inside the login transaction. Explicit group-to-role mappings select
the highest Version 1.0 role; unmapped directory users receive `Employee`. Existing
local users retain their stored role.

## Login and attempt control

`LoginAttemptService` checks recent failures before the provider bind and records
password-free result metadata in PostgreSQL. Username and source limits are
independent; temporary lockout and retry intervals are configuration values. A
provider failure records a stable category in its own short transaction. A success
commits the synchronised user, hashed session, successful attempt, and immutable
audit-chain event together.

Responses never distinguish an unknown username from a wrong password. Stable
application errors cover invalid credentials, disabled and locked accounts,
directory unavailability, invalid/expired sessions, permission denial, and detected
refresh reuse. REST handlers return the shared safe error envelope without raw
exception text.

## Access and refresh tokens

`TokenManager` implements the configured Version 1.0 HS256 profile directly from
standard-library primitives. It accepts only HS256 and validates signature, issuer,
audience, type, issued-at, expiry, user UUID, session UUID, token UUID, and positive
token version. The signing secret must contain at least 32 encoded bytes and remains
outside client configuration.

Refresh tokens are 256-bit random opaque values. The raw value is returned once;
PostgreSQL stores only its SHA-256 digest. Refresh locks the session row, checks
active state and absolute expiry, uses constant-time digest comparison, rotates the
token and version atomically, and renews only the short access expiry. Migration
`0002_refresh_reuse` retains the immediately previous digest so its
reuse invalidates and audits the session as compromised; arbitrary mismatched
values are rejected without allowing a session-ID-only denial of service.

Logout, logout-all, device revocation, account disable coordination, and refresh
reuse commit database invalidation before an optional WebSocket notifier runs.
Failure to disconnect a later-stage socket cannot reactivate a session.

## API and permissions

The public API surface is:

```text
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
POST   /api/v1/auth/logout-all
GET    /api/v1/auth/me
GET    /api/v1/auth/sessions
DELETE /api/v1/auth/sessions/{session_id}
```

Only login and refresh are bearer-free. Every other operation resolves the bearer
through `AuthenticationService`, `TokenManager`, the session repository, user
repository, and current role permissions. Routes do not compare role strings.
`PermissionService` re-reads current role grants and centralises application,
conversation-membership, and group-role checks for later business services.

## Client secret ownership

The Windows client stores refresh tokens and session identifiers through the
`SecureStore` protocol. `WindowsCredentialManagerStore` namespaces generic
credentials per application and profile, validates target names and blob size,
preserves exact binary values, translates Windows API failures, and never logs a
secret. No JSON or local database receives token material.

`ClientAuthenticationService` constructs one login request and retains no password.
`ClientSessionService` owns the access token only in memory, retrieves the refresh
token from protected storage, replaces it after every refresh, asks the server to
revoke before logout, and clears protected and in-memory state on logout or a
session-revoked event. General HTTP transport, protocol negotiation UI, local
SQLite, and WebSockets remain in their later stages; the services depend on narrow
injectable API protocols so those stages do not require a rewrite.

## Configuration and deployment

Production uses a protected token-secret file and LDAP bind-password file. LDAPS or
StartTLS certificate validation is mandatory; local and mock providers, TLS-off
server transport, debug mode, example secrets, and unauthenticated Redis are
rejected by production validation. Directory group-role mappings are configuration,
never code.

An installation upgrading from Task 08 must apply Alembic through
`0002_refresh_reuse` before startup. The server verifies the head
and does not auto-migrate.

## Verification

Deterministic tests cover Argon2id verification and rehash, JWT claim and algorithm
validation, opaque refresh hashing, LDAP escaping/binding/account state/outage,
mock and local provider behavior, directory role mapping, login/session transaction
collaboration, access validation, rotation and reuse, revocation notification,
permission and resource checks, all authentication routes, and client protected
secret cleanup. Real PostgreSQL migration and login workflows remain opt-in through
the dedicated `BLUEBUBBLES_TEST_DATABASE_URL`; live Active Directory is never a
normal automated-test dependency.
