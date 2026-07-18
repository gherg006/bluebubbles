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
- Prepared uploads keep ciphertext bodies on disk instead of retaining a whole
  large file in memory; each chunk is revalidated immediately before upload.
- Recipient download coordination verifies ordered chunk hashes and GCM tags,
  encrypted metadata and the final plaintext checksum before an atomic publish.
- Client and server now share the same raw-ciphertext chunk checksum contract;
  cancelled sessions cannot accept later chunks.

## Verification evidence

Focused test targets:

- `tests/unit/server/test_task_15_attachments.py`
- `tests/unit/client/test_task_15_attachments.py`
- `tests/unit/client/test_task_12_crypto.py`

The mandatory `scripts/development/run_quality_checks.py` runner completed
successfully using the locked Python 3.13 environment: Black and Ruff were
clean, strict mypy found no issues in 291 source files, and pytest reported 255
passed, 3 intentional PostgreSQL skips and 89.63% branch-aware coverage (meeting
the configured integer 90% threshold).

## Environment-bound limitation

Real PostgreSQL migration and repository checks require an already migrated,
dedicated database named by `BLUEBUBBLES_TEST_DATABASE_URL`. They must skip when
that safe external dependency is absent. Offline migration rendering, metadata
checks and temporary-filesystem transfer tests remain mandatory.
