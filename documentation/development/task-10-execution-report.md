# Task 10 execution report

## Completion boundary

Task 10 implements authenticated user profiles and search, directional contacts,
and versioned public identity-key registration, retrieval, rotation, and revocation.
It integrates these operations with the Task 09 session boundary and the Task 07
Unit of Work. Private-key storage, message encryption, general client transport,
WebSocket publication workers, and GUI presentation remain out of scope.

## Delivered changes

- Safe user profile/search DTO conversion and self-owned profile updates.
- Department-aware stable cursor search and enabled-user concealment.
- Complete directional contact lifecycle, nickname persistence, favourites, and
  blocking.
- Independent X25519 and Ed25519 public-key revisions with strict Base64 length,
  algorithm, fingerprint, monotonic-version, conflict, expiry, and revocation rules.
- Immutable key audit metadata plus durable `KEY_CHANGED` outbox events.
- Thin authenticated user, contact, and key routes.
- Alembic revision `0003_contact_nicknames`, focused tests, and architecture notes.

## Compatibility and security decisions

The pre-existing key table already separated key purpose and version, so no key
schema rewrite was required. The repository now demotes an old primary before
staging a replacement and retains historical revisions. The server accepts exactly
32 public bytes and never receives a private key. Fingerprints bind algorithm,
purpose, version, and key bytes through a documented canonical encoding.

Contact nicknames required one nullable bounded column. Existing relationships
remain valid and acquire no synthetic nickname during upgrade.

## Verification evidence

The repository-owned quality runner completed successfully on 17 July 2026:

| Exit check | Result |
|---|---|
| Black formatting | Passed; 225 Python files unchanged |
| Ruff linting | Passed; no issues |
| Strict mypy | Passed for 225 source, test, script, and migration files |
| Automated tests | 203 passed, 3 skipped; 206 collected |
| Branch-aware coverage | 91.23%, above the required 90% |
| Development server executable configuration | Passed |
| Alembic head | `0004_group_moderator` |
| Git whitespace validation | Passed |

The three skips are the opt-in real PostgreSQL repository, Unit-of-Work, and
server-lifecycle workflows. They require an already migrated dedicated database
through `BLUEBUBBLES_TEST_DATABASE_URL`; no administrator database or SQLite
substitute is used. The two warnings are upstream pyasn1 deprecations raised while
ldap3 imports and do not affect these services.
