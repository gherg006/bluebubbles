# Database schema and migrations

Task 05 establishes the PostgreSQL persistence contract. PostgreSQL is authoritative
for durable server state; Redis remains disposable, and encrypted attachment bytes
remain outside the database. The schema contains no plaintext message, draft, token,
password, private-key, or attachment-content columns.

## Schema catalogue

All application entity identifiers use PostgreSQL `UUID`, timestamps use
`TIMESTAMPTZ`, encrypted values use `BYTEA`, and structured safe metadata uses
`JSONB`. Foreign keys default to `RESTRICT` or `SET NULL`; `CASCADE` is limited to
dependent rows without independent meaning. Repositories introduced in Task 06 own
ordinary access; specialised services later own configuration, audit, and jobs.

| Tables | Purpose and principal columns | Integrity, deletion, and retention |
|---|---|---|
| `roles`, `permissions`, `role_permissions` | Fixed role catalogue (`id`, name, description, priority) and composite role grants | Unique names; non-negative role priority; restricted foreign keys; configuration retention |
| `users`, `local_credentials` | User/directory profile and optional Argon2id verifier | Unique normalised username and non-null directory GUID; version check; users soft-delete; credentials cascade only on physical user deletion |
| `sessions`, `login_attempts`, `policy_acknowledgements` | Hashed refresh-token sessions, password-free login evidence, policy receipt | Binary token hashes; ordered expiry; positive token version; acknowledgement composite key; policy-based cleanup |
| `contact_relationships` | Directional favourite, block, and interaction weight | Composite user pair key; self-contact rejection; non-negative weight; dependent lifecycle |
| `user_public_keys` | Versioned public encryption/signing keys and revocation history | Unique user/type/version; one active primary key per type; revoked keys retained |
| `conversations`, `direct_conversation_pairs` | Soft-deletable conversation metadata and canonical direct identity | Valid type/title/version; unique ordered user pair; conversation history retained |
| `conversation_members`, `conversation_events` | Membership periods, group roles, read cursors, and safe structural activity | One active membership; at most one active owner; valid period/role/version; events exclude message bodies |
| `messages`, `message_versions` | Current and historical signed encrypted envelopes | No plaintext column; positive protocol/version/size; soft deletion; cursor-order index; dependent versions cascade only after authorised physical deletion |
| `message_recipient_keys`, `message_deliveries` | Per-recipient content-key envelopes and delivery state | One envelope/delivery per message-recipient; positive key version; read implies delivered; recipient indexes |
| `attachments` | Encrypted file metadata and opaque filesystem reference | Non-negative sizes/counts, positive chunk size/version, one message link; soft deletion and retention cleanup |
| `attachment_recipient_keys`, `attachment_chunks` | Recipient file-key envelopes and durable encrypted chunk metadata | Unique recipient and chunk index; non-negative size/index; dependent rows cascade only with physical attachment deletion |
| `upload_sessions`, `upload_session_chunks` | Recoverable upload progress independent of Redis | One session per attachment; received size bounded by expected size; expiry index; temporary retention |
| `announcements`, `announcement_acknowledgements` | Deliberate organisational plaintext and per-user receipt | Non-empty content, valid priority/version, one acknowledgement per user; withdrawal/expiry retained |
| `audit_events`, `audit_chain_state` | Immutable hash-chain events and single lockable chain head | Sequence primary key; 64-character hashes; update/delete trigger; events retained according to audit policy |
| `security_alerts` | Safe operational security findings and review lifecycle | Valid severity/status; positive occurrences; acknowledgement/resolution timestamp checks |
| `configuration_versions` | Secret-free validated configuration history | Unique version number and previous-version link; append-oriented administrative history |
| `outbox_events` | Transactional, retryable post-commit events | Non-negative attempts, positive protocol, partial unpublished/retry indexes; cleanup only after publication policy |
| `worker_execution_records` | Bounded worker-run summaries | Non-negative counts; worker/time index; operational retention |
| `data_export_jobs` | Controlled export workflow and protected file reference | Status/time index; output bytes remain on protected filesystem; expiry cleanup |
| `data_deletion_requests` | Reviewed retention/deletion workflow | User/reviewer references are preserved or nullified; status/time index; administrative retention |

The ORM definitions in `src/bluebubbles/server/database/models/` are the detailed
column authority. The initial migration creates the same metadata and is verified by
an offline PostgreSQL DDL test, preventing the migration and ORM from drifting.
Task 06 access patterns, locking, pagination, mapping, and real-database verification
are documented in [repository-infrastructure.md](repository-infrastructure.md).

## Constraints and access rules

SQLAlchemy metadata applies deterministic `pk_`, `fk_`, `uq_`, `ck_`, and `ix_`
names. Critical rules are enforced in PostgreSQL: unique user identity, canonical
direct pairs, active membership/owner uniqueness, unique recipient envelopes,
unique chunks, positive sizes and versions, and append-only audit events. The audit
writer must lock `audit_chain_state` before allocating a sequence and hash.

The normal application database role should receive ordinary table permissions, but
only `SELECT` and `INSERT` on `audit_events`; it must not receive audit `UPDATE`,
`DELETE`, or `TRUNCATE`, nor schema modification rights. Deployment creates the
separate application, migration, and backup roles because installation-specific role
names cannot safely be assumed by a portable migration.

## Seed catalogue

Revision `0001_initial_schema` inserts `Employee`, `Helpdesk`, `HR`,
`Administrator`, and `SuperAdministrator`, the complete domain permission catalogue,
and explicit grants. IDs are deterministic UUIDv5 values. The controlled runtime
seed helper inserts missing entries and grants but never overwrites descriptions,
priorities, or administrator changes, and never commits its caller's transaction.
No user, credential, administrator account, or secret is seeded.

## Upgrade and recovery

Configure `BLUEBUBBLES_DATABASE_URL_FILE` to point at the protected migration-role
URL (or use `BLUEBUBBLES_DATABASE_URL` for a short-lived development shell), then run:

```text
alembic upgrade head
```

The application-compatible head is `0002_refresh_reuse`. The second
revision adds the nullable previous-refresh digest used to distinguish immediate
rotated-token reuse from an arbitrary invalid token; it never stores raw token
material. Runtime readiness calls
the read-only revision verifier and refuses normal operation for an unversioned,
older, or unknown-ahead schema. The server does not auto-migrate production.

Before any future destructive revision, take and verify a PostgreSQL backup, record
the affected tables and compatibility window, and test both upgrade and restore. The
initial downgrade removes the complete empty Version 1.0 schema and therefore is
development-only. For any database containing business data, recovery is by verified
restore, not by running that destructive downgrade. A restore must recheck the
Alembic revision, foreign keys, required indexes, audit trigger/chain, outbox state,
attachment references, sessions, users, and message counts.
