# Task 15 execution report

## Completion boundary

Task 15 implements authorised, resumable transfer of client-encrypted
attachments: shared contracts, signed manifests and recipient envelopes, local
filesystem storage, server service and routes, cleanup ownership, client
preparation/upload/download coordination, transfer state presentation, tests and
focused documentation. It does not implement general GUI windows or later
administration stages.

## Compatibility and security decisions

- The client remains the only plaintext/file-key boundary; server persistence,
  logs, errors, audit metadata and fixtures contain ciphertext metadata only.
- Existing attachment DTO/domain/ORM separation and Unit of Work ownership are
  extended instead of replaced.
- UUID-derived directories and atomic chunk writes prevent user filenames from
  becoming storage paths.
- Chunk retry is checksum-idempotent; conflict, expiry and incomplete completion
  are explicit safe failures.
- Message submission remains responsible for validating and linking completed
  uploads in its transaction.
- Downloads return one authorised recipient envelope and publish plaintext only
  after signature, tag and complete-file verification.
- Prepared transfer state contains encrypted material and becomes durable through
  the Task 16 client-storage repository.

## Verification evidence

Focused test targets:

- `tests/unit/server/test_task_15_attachments.py`
- `tests/unit/client/test_task_15_attachments.py`
- `tests/unit/client/test_task_12_crypto.py`

Final Black, Ruff, strict mypy, pytest and branch-aware coverage evidence is
pending completion of the combined Task 15 and Task 16 implementation. The
mandatory command is `python scripts/development/run_quality_checks.py`; this
report must be updated with observed results before the stage is declared
complete.

## Environment-bound limitation

Real PostgreSQL migration and repository checks require an already migrated,
dedicated database named by `BLUEBUBBLES_TEST_DATABASE_URL`. They must skip when
that safe external dependency is absent. Offline migration rendering, metadata
checks and temporary-filesystem transfer tests remain mandatory.

