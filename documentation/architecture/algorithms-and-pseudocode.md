# Algorithms and pseudocode evidence

The source modules named after each algorithm are authoritative. Pseudocode omits
transport syntax but preserves validation, transaction, cryptographic, and failure
ordering.

## Recipient-envelope generation

Implemented by `client/security/message_crypto.py`.

```text
INPUT fresh content key, active recipient public-key versions
REJECT empty or duplicate recipient set
FOR each recipient in canonical recipient-ID order
    validate algorithm and public-key length
    seal content key to that exact public-key version
    append recipient ID, key version and sealed key
RETURN immutable envelope tuple
```

## Canonical message serialisation, encryption, signing and decryption

Implemented by `shared/protocol/serialisation.py` and
`client/security/message_crypto.py`.

```text
NORMALISE timestamps and ordered mappings into canonical JSON bytes
GENERATE random AES-256 content key and unique GCM nonce
ENCRYPT plaintext with canonical authenticated metadata
GENERATE recipient envelopes
SIGN the complete canonical ciphertext envelope with Ed25519
ZERO/DISCARD transient content-key references where supported

ON RECEIVE
    validate protocol and algorithm allowlists
    validate sender key version and recipient envelope uniqueness
    verify Ed25519 signature over canonical bytes
    open only current user's sealed content key
    decrypt and authenticate AES-GCM payload
    reject before display/cache on any failure
```

## Attachment chunk encryption and resume selection

Implemented by `client/security/attachment_crypto.py` and
`client/services/attachments.py`.

```text
HASH plaintext while reading bounded chunks
FOR chunk index from zero to final index
    derive/generate a nonce unique for attachment key and index
    encrypt chunk with manifest identity and index as authenticated context
    persist/send ciphertext, nonce, tag and ciphertext hash
SERVER returns verified missing indexes
REJECT negative, duplicate or out-of-range indexes
UPLOAD only missing indexes
COMPLETE only after every authoritative chunk exists and verifies
```

## Offline queue replay and conflict classification

Implemented by `client/services/offline_queue.py` and
`client/services/synchronisation.py`.

```text
LOAD pending encrypted actions in creation order
FOR each action
    IF dependency is unresolved: mark blocked and continue
    IF membership/tombstone policy forbids action: preserve recovery state
    ELSE submit with stable idempotency UUID
    IF stored or already stored: commit local authoritative result, then delete action
    IF retryable failure: increment attempts and schedule bounded backoff
    IF version conflict: classify, preserve attempted content, require user resolution
ADVANCE sync cursor only after local transaction commits
```

## Audit hash-chain append and verification

Implemented by `server/services/audit.py`.

```text
LOCK/READ current audit tail inside transaction
BUILD safe canonical metadata without plaintext or secrets
COMPUTE entry hash from sequence, timestamp, actor/action metadata and previous hash
INSERT one append-only row and commit

VERIFY expected sequence from first row
FOR each row in sequence
    compare stored previous hash with prior computed hash
    recompute entry hash from canonical fields
    fail and alert on sequence/link/hash mismatch
RETURN valid only after the final row
```

## Cursor pagination and local search tokens

Implemented by `server/repositories/types.py` and `client/services/search.py`.

```text
ENCODE stable sort values and ID into opaque authenticated/validated cursor form
ON page request validate cursor shape and page limit
QUERY strictly after cursor ordering; fetch limit plus one
RETURN bounded items and next cursor only when another row exists

NORMALISE authorised cached plaintext with Unicode-aware token rules
DROP empty/unsupported tokens; deduplicate deterministically
QUERY only the active encrypted profile's local index
RETURN snippets from cached authorised messages, never server-side plaintext search
```

## Required workflow pseudocode

### Authenticate user

```text
validate request and rate limit -> authenticate configured provider -> map/create
enabled identity -> resolve role/permissions -> create hashed-token session + audit +
outbox in one explicit transaction -> return tokens/profile -> client stores tokens
in protected session owner and discards password
```

### Refresh session

```text
hash supplied refresh token -> lock session -> reject missing/expired/revoked/user
disabled -> detect reuse -> revoke family and alert on reuse -> rotate token once ->
commit -> replace client secrets only after success
```

### Send encrypted message

```text
client validates plaintext limit and recipient keys -> encrypt/sign -> persist
ciphertext retry item -> server authenticates, locks membership, validates exact
recipient set and version -> insert idempotently with outbox -> commit -> client
marks stored -> recipient verifies/decrypts -> acknowledge delivery
```

### Decrypt received message

```text
deduplicate event ID -> validate sender/key/algorithms -> verify signature -> find own
envelope -> open key -> verify GCM tag and decrypt -> cache encrypted authoritative
record plus locally protected search material -> acknowledge -> display
```

### Create group and transfer ownership

```text
authenticate creator -> validate unique members and maximum -> transactionally create
conversation, owner membership, member rows, event and outbox -> commit

for transfer: lock group and active memberships -> require current owner and active
target -> demote old owner and promote target atomically -> append event/audit/outbox
-> commit -> ensure exactly one active owner
```

### Prepare attachment and upload missing chunks

```text
validate safe filename/size/type -> stream hash/encrypt bounded chunks -> create
encrypted manifest -> ask server for missing indexes -> validate response -> upload
only missing ciphertext chunks with retries -> complete -> verify authoritative record
```

### Process offline queue and recover event gap

```text
on reconnect authenticate and negotiate protocol -> if event cursor is valid replay
events in order, committing local state before cursor -> if cursor expired/gapped,
perform scope reconciliation with checkpoints and tombstones -> then serially replay
eligible offline actions with stable IDs and conflict preservation
```

### Append and verify audit event

```text
authorise action -> build allowlisted metadata -> append chained event in same
transaction as protected change where required -> later recompute complete chain;
on mismatch make health unhealthy and create/deduplicate critical alert
```

### Apply configuration update

```text
authorise configuration permission -> validate strict known fields and production
safety -> compare expected version -> persist immutable history and audit/outbox ->
commit -> apply only settings marked dynamic; report restart-required settings
```
