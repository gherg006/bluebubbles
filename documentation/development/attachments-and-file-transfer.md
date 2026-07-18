# Attachments and file transfer

Task 15 adds resumable transfer of client-encrypted attachments. The client is
the only component that handles plaintext file content or attachment file keys.
The server authorises the operation, stores opaque ciphertext chunks and
recipient envelopes, and exposes only the requesting user's envelope during
download.

## Wire and cryptographic boundary

An upload is prepared outside the GUI thread using bounded chunks. Each file has
a fresh 256-bit master key and each chunk is authenticated independently with
AES-256-GCM. The chunk context binds the protocol and attachment context, while
encrypted metadata binds the final plaintext checksum and declared layout. The
plaintext checksum remains inside encrypted client-readable metadata. The
server may retain ciphertext and ciphertext checksums but never plaintext
bodies, plaintext checksums or file keys.

Initialisation validates protocol version, filename, declared sizes, supported
algorithms, active conversation membership, upload permission, configured
limits and exact recipient coverage. A client-selected attachment UUID is the
stable identity used by retry and message linking. Responses and events expose
only safe metadata and the authenticated recipient's key envelope.

## Server upload lifecycle

`POST /api/v1/attachments/uploads` creates a recoverable upload session after
authorisation. Chunk bodies are submitted to
`PUT /api/v1/attachments/uploads/{upload_id}/chunks/{chunk_index}`. The storage
adapter writes each chunk atomically under UUID-derived paths; submitted display
filenames are never physical paths. Repeating an index with the same checksum is
idempotent, while conflicting bytes are rejected. The status route returns the
confirmed and missing indexes so a restarted client sends only missing chunks.

Completion independently checks session ownership, expiry, count, total size,
per-chunk evidence and the full encrypted checksum. Final storage publication,
attachment metadata, recipient keys, audit metadata and the completion event are
coordinated so ordinary database transactions never own filesystem handles and
no committed attachment is reported before its ciphertext is durable. Incomplete
sessions, cancelled uploads, failed finalisation and orphaned completed
attachments are cleaned through bounded lifecycle-owned work.

Message submission remains the linking transaction. Every referenced attachment
must be complete, unlinked, uploaded by the sender, in the same conversation and
still permitted by active membership. Failed message submission leaves the
completed upload available for idempotent retry until orphan expiry.

## Download and deletion

Metadata and chunk downloads require an enabled authenticated user, download
permission, a current authorised conversation view, a visible linked message and
a recipient envelope. Chunk responses are streamed and never decrypted by the
server. The client writes encrypted temporary material first, verifies the
manifest and uploader signature, authenticates every chunk, validates the final
plaintext checksum and only then atomically publishes the selected destination.
Cancellation or verification failure removes partial plaintext output.

Deletion is soft in PostgreSQL and coordinated with encrypted file retention.
Storage references remain opaque, path traversal is rejected at the storage
boundary, and cleanup failures are safe to retry.

## Client transfer ownership

The client file-transfer service owns preparation, resumable upload/download
coordination and immutable progress snapshots. Prepared uploads retain only
bounded chunk metadata and encrypted temporary paths; each ciphertext body is
loaded and revalidated immediately before transmission. Downloads authenticate
every ordered chunk, decrypt into a partial file, verify the encrypted metadata
and final plaintext checksum, resolve filename collisions, and publish with an
atomic rename. Cancellation and integrity failure remove partial plaintext.
Transfer recovery state is encrypted by the Task 16 local-storage subsystem so
interruption or process restart does not silently lose session identity, paths,
confirmed chunk indexes, expiry, or the client-only file key.

The transfer ViewModel consumes service snapshots and commands; it never opens
files, performs cryptography or sends HTTP directly. This keeps the later GUI
stage independent from storage, networking and encryption implementations.

## Verification map

`tests/unit/server/test_task_15_attachments.py` covers authorisation, recipient
coverage, session recovery, chunk bounds and idempotency, checksum validation,
atomic completion, concealed downloads, message linking and cleanup behavior.
`tests/unit/client/test_task_15_attachments.py` and
`test_task_15_transfer_workflows.py` cover validation, bounded preparation,
resumable upload, cancellation, collision-safe download, final verification and
partial-output cleanup. Existing Task 12 cryptographic tests continue to cover
bounded-memory chunk encryption and authentication failures.
