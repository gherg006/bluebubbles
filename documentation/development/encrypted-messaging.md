# Encrypted messaging

Task 13 adds the complete server application path for encrypted messages plus the
client send/receive coordinator. The server models, services, routes, repositories,
audit records and outbox events contain ciphertext and public metadata only.

## Server workflow

`POST /api/v1/messages` authenticates the caller, requires the send-message
permission, validates protocol and request size, locks the conversation, requires
active membership, and compares the supplied recipient set with every active
member. Reply targets must exist in the same conversation. The client-generated
message UUID is the durable idempotency key: an identical retry returns the
existing acknowledgement; conflicting reuse returns a conflict.

One Unit of Work stores the encrypted message and recipient envelopes, creates
per-user `stored` delivery rows, advances conversation activity, appends a
plaintext-free audit-chain event, adds a recipient-addressed outbox event, and
commits. Nothing is published before the commit.

History is available through
`GET /api/v1/conversations/{conversation_id}/messages`. Membership start time
limits group history and every response contains only the requesting user's key
envelope plus the digest that binds the complete envelope set. Pagination uses
the existing server-controlled timestamp/UUID cursor.

Edits use a fresh encrypted payload, recipient set, signature and optimistic
version, preserve an encrypted prior version, and are limited to the sender,
text-bearing messages, active membership and the configured edit window. Deletion
is soft, versioned and auditable. Delivery and read acknowledgements are accepted
only from intended recipients. Deleted ciphertext is not returned by the normal
active-message repository path.

## Client workflow

The client encryption service constructs signed requests without exposing
plaintext to networking or storage services. `ClientMessagingService` queues the
ciphertext request before REST submission, preserves its UUID across bounded
retries, caches the encrypted response, verifies/decrypts incoming events, ignores
duplicate message IDs, and acknowledges delivery only after successful processing.
Permanent application errors are not converted into network retries.

## Schema and compatibility

Migration `0005_text_with_attachment` extends the existing message-type check for
encrypted text messages that reference attachments. Existing message/outbox
tables, indexes, recipient uniqueness, encrypted version history and repository
transaction ownership remain unchanged. Message binary fields continue to use
PostgreSQL `BYTEA`; AES-GCM tags use the library's combined ciphertext form.

## Verification map

`tests/unit/server/test_task_13_messaging.py` covers successful atomic sends,
idempotent retry, conflicts, permissions, membership and recipient coverage,
protocol rejection, history filtering, edit concurrency and ownership, deletion,
delivery/read state and concealed unrelated resources.
`tests/unit/client/test_task_13_client_messaging.py` covers ciphertext queueing,
stable retry IDs, successful cache updates, incoming deduplication and delivery
acknowledgements.

