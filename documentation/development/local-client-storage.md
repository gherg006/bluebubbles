# Local client storage

Task 16 replaces process-only client caches with a user-specific, encrypted local
SQLite subsystem. PostgreSQL remains the server authority. Local storage exists
to render cached conversations quickly, preserve drafts and retryable work,
recover transfers, cache versioned public keys and provide search over content
the authenticated user has already decrypted.

## Profile and key boundary

Every BlueBubbles user receives a separate UUID-named profile below the validated
client profile root. An exclusive profile lock prevents concurrent processes from
opening the same cache. Database names, cache paths and recovery paths are built
from trusted identifiers and are checked to remain below that profile root.

A fresh 256-bit local master key is held in Windows Credential Manager and is not
stored beside SQLite. Version 1 uses standard SQLite with application-level
AES-256-GCM encryption for sensitive columns because this is the dependable
Python 3.13 fallback allowed by the specification. HKDF purpose separation keeps
message cache, drafts, offline actions, transfer state, settings and search keys
independent. Each encrypted record uses fresh nonce material and AAD containing
its profile, table purpose and stable record identity.

The credential store may contain session secrets and the local database key. It
does not contain passwords, message history, attachment plaintext or private
identity keys. Private keys remain in their dedicated encrypted key store.

## Database and migrations

The local database manager serialises SQLite access away from the GUI thread,
owns connection open/close, enables foreign keys and safe journalling, verifies
integrity and applies numbered client migrations transactionally. Migration
failure preserves the original cache and reports a recoverable local-storage
error; the implementation never deletes the database merely because its schema
changed.

The schema stores only useful client projections: cached users, conversations,
members, encrypted message display payloads, public keys, drafts, encrypted
offline actions, transfer recovery, hashed search documents and tokens, settings,
synchronisation cursors and cache accounting. Repository methods own SQL and
accept domain or storage value objects. ViewModels and network clients never
execute SQLite statements.

Transactions group related local changes, including a message with its
conversation summary, edits/deletes with search-token replacement, an offline
action with pending message state, completed transfers with recovery-state
removal, and complete synchronisation pages.

## Cache, drafts and offline work

Decrypted message display content and draft text are encrypted before insertion.
Ciphertext received from the server may also be cached for reprocessing. Cache
accounting enforces configured size limits with bounded least-recently-used
eviction while respecting pinned or active records. Replaceable cached data can
be rebuilt from the server; drafts, queued actions and incomplete transfers are
not silently discarded.

The durable offline queue stores the already encrypted network request together
with its original message UUID, ordering metadata, attempt count, next retry and
safe error code. Temporary failures receive bounded backoff; permanent
permission or validation failures remain visible for user recovery. Processing
preserves per-conversation order and server idempotency. Task 13's messaging
service consumes the repository protocol, so plaintext never enters retry
storage.

Transfer recovery stores encrypted temporary paths, confirmed chunk indexes,
session identity and expiry. Completed plaintext downloads remain only in the
user-selected destination; BlueBubbles does not duplicate them into its cache.

## Private local search

Search text is normalised with Unicode normalisation and case folding. Exact word
tokens are HMAC-SHA-256 values produced with a profile-specific, purpose-derived
search key. SQLite stores deterministic digests and encrypted display documents,
not plaintext words. Candidate messages are decrypted only after token matching
so phrase checks and excerpts remain a client presentation concern.

Index updates are transactional with message cache edits and deletes. Key change,
conversation invalidation or explicit cache clearing removes affected tokens. A
rebuild clears replaceable tokens and regenerates them from authorised encrypted
cache records; it cannot search messages that were never downloaded or were
evicted.

## Startup, maintenance and clearing

After authentication the storage coordinator obtains the profile key, acquires
the lock, opens and verifies SQLite, migrates it, loads settings, incomplete
transfers and offline actions, and then permits synchronisation. Logout clears
tokens and in-memory secrets while retaining the encrypted cache by default,
unless managed policy requires profile removal. Shutdown stops storage users,
closes SQLite and releases the profile lock in order.

Maintenance reports usage, enforces limits and cleans expired replaceable data.
Selective clearing is transactionally scoped. Clear-all closes resources,
deletes credential entries and local encryption keys, and removes managed profile
data while leaving the server account untouched. The product does not claim
physical secure erasure on SSDs; destroying the encryption key is the primary
protection for remnants.

## Verification map

`tests/unit/client/test_task_16_local_storage.py` covers profile isolation and
locking, initial and upgrade migrations, integrity failure, encrypted repository
round trips, drafts, durable queue restart, transfer recovery, cache accounting
and clearing. `tests/unit/client/test_task_16_search.py` covers Unicode
normalisation, deterministic purpose-keyed HMAC tokens, multi-token and filtered
search, edit/delete replacement, rebuilding and plaintext-absence checks.
Security coverage also checks wrong-key rejection, credential deletion, path
containment and log/SQLite plaintext absence.

