# Task 16 execution report

## Completion boundary

Task 16 implements per-user local SQLite persistence with encrypted sensitive
columns, protected key ownership, client migrations, repository boundaries,
draft and message caches, durable offline work, transfer recovery, bounded cache
maintenance, private hashed search, profile locking, restart recovery, clearing,
tests and focused documentation. PostgreSQL remains authoritative and GUI stages
remain out of scope.

## Compatibility and security decisions

- Standard-library SQLite plus application-level AES-256-GCM is the documented
  Python 3.13-compatible fallback; no unreliable SQLCipher dependency is claimed.
- A random local master key is protected by Windows Credential Manager and never
  stored with the database.
- Stable profile UUIDs and contained path construction isolate users on shared
  Windows devices; an exclusive profile lock rejects concurrent writers.
- Sensitive repository fields use purpose-separated keys, fresh nonces and
  record-bound AAD. Plaintext messages, drafts, offline payloads and search words
  are absent from SQLite and logs.
- HMAC-SHA-256 search tokens provide deterministic exact-token matching without
  pretending to offer server-wide or attachment-content search.
- Durable retry records preserve the Task 13 message UUID and per-conversation
  ordering; permanent failures remain recoverable instead of disappearing.
- Cache eviction applies only to replaceable data. Clearing local data removes
  keys and managed files without claiming guaranteed physical overwrite.

## Verification evidence

Focused test targets:

- `tests/unit/client/test_task_16_local_storage.py`
- `tests/unit/client/test_task_16_search.py`
- `tests/unit/client/test_task_13_client_messaging.py`

Final Black, Ruff, strict mypy, pytest and branch-aware coverage evidence is
pending completion of the combined Task 15 and Task 16 implementation. The
mandatory command is `python scripts/development/run_quality_checks.py`; this
report must be updated with observed results before the stage is declared
complete.

## Platform and recovery limitations

The production credential adapter requires the current Windows user's Credential
Manager. Tests use an injected secure-store boundary and temporary profiles.
Standard SQLite does not transparently encrypt structural metadata, so every
sensitive value is encrypted at the application boundary. Search covers only
authorised content present in the local cache, and physical secure erasure on
SSDs is not claimed.

