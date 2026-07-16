# Domain models and error handling

BlueBubbles keeps three model families deliberately separate:

- `bluebubbles.shared.models` contains strict REST and WebSocket contracts used
  by both programs.
- `bluebubbles.server.domain` contains infrastructure-independent server
  entities and rules. Server message and attachment models store ciphertext,
  signatures, encrypted recipient keys, hashes, and opaque storage references;
  they cannot represent message or attachment plaintext.
- `bluebubbles.client.domain` contains Windows-client state. Authorised
  plaintext is restricted to explicitly named in-memory types such as
  `DecryptedMessageContent` and local search results. Locally persisted content
  is represented separately as encrypted cache data.

Domain objects do not query databases, access files, call network services, or
render interface components. Later repository stages map these entities to
PostgreSQL on Debian and encrypted SQLite/cache records on Windows.

## Entity rules

Persistent server entities derive from `BaseEntity`, which supplies UUID
identity, aware UTC timestamps, soft deletion, and an incrementing optimistic
version. State-changing methods reject invalid transitions before a repository
can persist them. Examples include group ownership transfer, delivery status,
upload completion, session invalidation, audit-chain verification, outbox
publication, and client file-transfer progress.

Audit events and outbox events contain safe metadata only. Audit hashes are
calculated from deterministic UTF-8 JSON so a later integrity service can
verify the chain consistently on Windows development machines and Debian
servers.

## Error contract

`bluebubbles.shared.errors.ErrorCode` is the only public error-code catalogue.
Every code has stable HTTP, retry, severity, title, help-code, and default
message metadata. REST failures use `ApiErrorResponse`; WebSocket failures use
`WebSocketErrorEventData`. Neither contract can serialise Python exceptions or
technical tracebacks.

Expected failures derive from `BlueBubblesError`. Its context sanitiser removes
password, token, secret, private-key, plaintext, ciphertext, and database URL
fields before context can reach a logging boundary. Infrastructure adapters
must translate library exceptions to the appropriate typed application error.
Unexpected exceptions remain distinct and must be translated only at a process
or request boundary to `INTERNAL_SERVER_ERROR` with a correlation identifier.

Retries require an explicitly idempotent `RetryContext` and a named bounded
`RetryPolicy`. Retry-after values are capped by that policy. The circuit breaker
counts only `DependencyError` failures, fails quickly while open, and probes in
the half-open state after its configured duration.

The Windows client maps stable codes through `ErrorMessageCatalog`. Unknown
future codes receive generic wording while retaining the code and correlation
identifier for diagnostics; raw exception text is never displayed.

## Compatibility rules

- Import shared contracts from either program, but never import client modules
  from the server or server modules from the client.
- Use timezone-aware UTC `datetime` values for entity and error timestamps.
- Use `bytes` for binary security fields internally; Base64 belongs only at
  protocol boundaries.
- Keep user-facing filenames separate from opaque server storage references.
- Do not add plaintext fields to server message, attachment, audit, outbox, or
  error models.

