# Repository infrastructure

Task 06 implements the server persistence boundary on top of the Task 05
PostgreSQL schema. Application services depend on protocols in
`server/repositories/interfaces`; only adapters in `server/repositories/sqlalchemy`
receive an `AsyncSession`. The next stage may compose all adapters into one Unit of
Work, but repositories in this stage never commit, roll back, close, or retain a
session beyond the caller-provided lifetime.

## Package catalogue

| Package | Responsibility |
|---|---|
| `repositories/interfaces` | Typed, infrastructure-neutral contracts for users, sessions, contacts, keys, conversations, messages, attachments, audit, announcements, administration, configuration, and outbox state |
| `repositories/mapping` | Pure ORM/domain conversion for users, sessions, conversations, encrypted messages, encrypted attachments, and immutable audit events; mappers never query |
| `repositories/sqlalchemy` | Async SQLAlchemy 2.x statements, row locking, optimistic updates, bounded cleanup, and safe error translation |
| `repositories/types.py` | Validated query objects, stable cursor pages, opaque cursor encoding, and complete encrypted chunk metadata |

The repository layer returns domain entities or purpose-specific immutable records.
It never returns an ORM query, ORM row, or SQLAlchemy session to a service.

## Transaction and concurrency contract

- Write methods may flush so named constraints fail inside the active transaction,
  but they never commit. Task 07 owns transaction completion.
- User, conversation, membership, message, and attachment mutations accept expected
  versions where concurrent changes matter. A zero-row optimistic update returns
  `False` for command-style methods or raises a safe `ConflictError` for entity
  replacement methods.
- `for_update=True` is supported on reads used by short critical sections.
  Membership rows are ordered before locking.
- Direct conversations persist a canonical ordered user pair. Group creation
  requires exactly one active owner.
- Audit append locks the singleton `audit_chain_state` row before allocating the
  next sequence. Individual audit events expose no update or delete operation.
- Outbox workers claim due events with `FOR UPDATE SKIP LOCKED`, store a bounded
  worker identifier, and clear locks on success, failure, or expiry recovery.
- Cleanup operations first select a bounded deterministic batch. They do not issue
  unbounded session or outbox deletion.

## Soft deletion and visibility

Ordinary user, conversation, message, and attachment reads exclude rows with a
`deleted_at` value. Historical shared records remain present for referential and
audit integrity. Purpose-specific query objects must explicitly request deleted
message placeholders or archived conversations. Recipient-scoped message and
attachment reads require a matching encrypted recipient-key row; this is data
visibility, not an authorization decision, and services must still enforce policy.

## Mapping and cryptographic compatibility

The schema stores versioned algorithm identifiers while the domain uses enums.
Message content is never decrypted or interpreted by a mapper. The Version 1.0
message table's identifier is also the client idempotency identifier; message create
rejects objects where these UUIDs differ. Binary attachment checksums are encoded as
base64 only at the string schema boundary. Attachment persistence requires an
explicit positive chunk size, and attachment recipient keys require the ephemeral
public key; the adapter never invents cryptographic bytes.

Session adapters store only the supplied one-way refresh-token hash as `BYTEA`.
Raw refresh or access tokens are absent from every repository contract and mapping.
Errors never include SQL text, parameters, encrypted payloads, hashes, or driver
details. Integrity failures become `ConflictError`; other adapter failures become a
redacted `RepositoryError`.

## Cursor pagination

Repository cursors are URL-safe, opaque encodings of deterministic ordering keys:

| Query | Order | Cursor fields |
|---|---|---|
| User search | normalized username ascending, UUID ascending | username, UUID |
| Conversation list | last activity descending, UUID descending | timestamp, UUID |
| Message history | server creation descending, UUID descending | timestamp, UUID |
| Audit events | sequence ascending | sequence number |

Adapters fetch `limit + 1`, return at most the validated limit, and emit a next
cursor only when another row exists. Invalid, ambiguous, oversized, or naive-time
queries fail before database access. Conversation and message page hydration batches
related rows to avoid N+1 loading.

## Verification

The deterministic unit suite exercises all repository adapters with controlled
SQLAlchemy results, including mapper round trips, validation, concurrency outcomes,
soft deletion, recipient scoping, audit immutability, outbox retry state, error
redaction, and resource ownership. Run the standard checks with:

```text
python scripts/development/run_quality_checks.py
```

Real PostgreSQL evidence is opt-in because the test must never create or destroy an
administrator's database. Point `BLUEBUBBLES_TEST_DATABASE_URL` at a dedicated,
already migrated Task 05 test database, then run:

```text
pytest tests/integration/test_repository_postgresql.py
```

The integration workflow inserts and reads a user, verifies the real unique
username constraint, claims an outbox event with PostgreSQL skip-locked semantics,
and rolls both transactions back. Without that explicit variable the test reports a
skip; SQLite is intentionally not substituted because it cannot validate PostgreSQL
partial indexes, row locks, `SKIP LOCKED`, `INET`, or JSONB behavior.
