# Offline queue and synchronisation

Task 17 turns Task 16's protected retry records and opaque cursors into an
explicit offline subsystem. The server remains authoritative: queued protected
writes cannot replay until protocol, current-user, policy, membership and public
key scopes have synchronised successfully.

## Queue model and persistence

`OfflineAction` supports the required pending, ready, processing, retry-wait,
blocked, completed, permanently-failed and cancelled states. Transitions are
validated; terminal actions cannot silently return to processing. Each new action
receives a stable action identity, idempotency key and profile-local monotonic
sequence. Dependencies are explicit and cycles are rejected.

Migration 002 extends the existing encrypted `offline_actions` table with user,
scope, sequence, update, dependency and acknowledgement metadata. Task 17 actions
bind local AES-256-GCM authentication data to user, action, type, sequence and
payload format. Legacy Task 16 sequence-zero records retain their original AAD so
upgrades do not destroy pending work.

`OfflineQueueService` owns the one-processor lock, startup recovery of interrupted
processing, due-time checks, serial ordering, dependency blocking, bounded
jittered backoff, manual retry, cancellation, safe summaries and result
persistence. `OfflineActionExecutor` dispatches only a fixed validated action enum
through injected handlers. Retryability comes from `OfflineActionExecutionResult`,
never from matching error-message text.

## Synchronisation and conflicts

`SynchronisationService` runs essential scopes before general data, checkpoints a
scope only after its gateway reports a committed page, isolates non-critical scope
failures, blocks queue replay after security-scope failure and falls back to full
resynchronisation when an incremental event cursor has expired. Full refreshes use
the Task 16 cache boundary, which preserves drafts, queued work, prepared transfers
and user preferences.

The WebSocket client exposes post-authentication and post-event callbacks so a
caller can run reconnect synchronisation and durably checkpoint the newest applied
event. The callback occurs only after validated event dispatch.

SQLite conflict and tombstone repositories retain safe metadata without message or
draft content. `ConflictResolver` automatically accepts only deterministic
equivalence cases; membership, permission, deletion and policy conflicts block the
action, key/protocol conflicts require rebuild, and ambiguous content conflicts
remain for user input.

## Presentation and recovery boundary

Queue summaries expose action type, status, attempts, safe error code and scope,
not decrypted payloads. Failed and blocked records remain until explicit user or
policy action. The connectivity controller publishes tested starting, connecting,
connected, synchronising, offline, degraded, reauthentication-required and
shutting-down states through one transition authority.

`tests/unit/client/test_task_17_offline_queue.py` covers encryption, wrong-key
rejection, ordering, dependencies, retry, permanent failure, cancellation, future
due times, processor exclusion and terminal states. The synchronisation target
covers security ordering, cursor expiry, degraded isolation, queue gating,
conflicts, tombstones and connectivity transitions.
