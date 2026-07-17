# WebSocket and outbox delivery

Task 14 provides authenticated low-latency notification without making WebSockets
the source of truth. REST/PostgreSQL remains authoritative for message submission
and missed-event recovery.

## Connection protocol

The canonical endpoint is `/api/v1/ws`; `/ws` remains accepted for configuration
compatibility. The server accepts the upgrade but requires an `AUTHENTICATE` event
within the configured timeout. The access token is sent in event data, never in a
URL, and is validated against the live server session. Oversized frames close with
1009, authentication/policy failures with 1008, server shutdown with 1001, and a
heartbeat timeout closes the connection. The client sends its last processed
event ID during authentication so later synchronisation can use it.

Each connection owns a send lock. The manager indexes connections by connection,
user and session under an async registry lock, copies targets before network I/O,
and unregisters failed sockets. Session revocation disconnects matching sockets
after the database revocation commits. Dispatch validates the versioned envelope
and event DTO, applies a per-connection sliding-window rate limit, invokes only
registered client-origin handlers, and returns a structured acknowledgement or
safe `ERROR` event. User identity in typing, presence, delivery and read events is
derived from the authenticated connection.

The desktop client permits one connection attempt at a time, authenticates before
marking itself connected, serialises sends, emits heartbeats, validates/deduplicates
incoming events, ignores acknowledgement frames, and reconnects with bounded
exponential backoff. Manual logout cancels receive, heartbeat and reconnect tasks.

## Durable publication

Business transactions insert one outbox row containing ciphertext, recipient IDs,
the canonical recipient-envelope digest and recipient-key map. The lifecycle-owned
worker releases stale claims, claims bounded batches with PostgreSQL
`FOR UPDATE SKIP LOCKED`, and commits the claim before publication. The publisher
builds a separate event per user and inserts only that user's encrypted key.
Offline recipients count as a successful publication to the real-time layer
because they recover through REST synchronisation.

Successful publication marks the row published. Failure increments attempts,
stores only the safe code `publication_failed`, schedules exponential retry capped
by configuration, logs the failure category, and continues with later events so
one poison item cannot block the batch. Business records are never rolled back for
post-commit socket failure. Nested outbox payloads reject fields named like
plaintext, passwords or private keys.

The Version 1 runtime uses the local publisher because the product currently runs
as one FastAPI server process. The interface keeps publication separate from
connection management so a Redis-backed multi-process adapter can be enabled when
multi-server deployment becomes an implemented product mode.

## Lifecycle and settings

Database, Redis and storage start before the WebSocket registry and outbox worker.
Shutdown reverses that order: the worker stops, connected clients receive a
going-away close, then infrastructure is disposed. Worker settings control
interval, batch size, retry base/cap and stale-lock timeout. Network settings
control authentication, heartbeat, missed-heartbeat and frame-size bounds.

## Verification map

`tests/unit/server/test_task_14_websocket_outbox.py` covers connection indexes,
failed-socket cleanup, session disconnect, recipient key filtering, offline users,
dispatcher validation/rate limiting/errors, transient handlers, live FastAPI
WebSocket authentication, poison-event isolation, lifecycle behavior and nested
sensitive-field rejection. `tests/unit/client/test_task_14_networking.py` covers
token-safe authentication, send/receive, event deduplication, disconnection and
connection failure behavior.

