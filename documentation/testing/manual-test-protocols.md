# Manual, usability, accessibility, and infrastructure test protocols

Use synthetic accounts and files only. Record test ID, requirement, date/time,
tester, environment versions, preconditions, exact input, steps, expected result,
actual result, status, evidence filename, defect ID, and retest result. Screenshots
must hide passwords/tokens/keys and show enough context. Logs must identify the
environment and timestamp while excluding secrets and plaintext.

## Usability observation

Recruit, where possible, a typical employee, confident user, less confident user,
helpdesk administrator, and accessibility-focused tester. Do not assist unless the
protocol permits it. For each task record completion without help, elapsed time,
incorrect actions, hesitation, errors, comments, proposed change, and priority.

Employee tasks: log in; find/add contact; create direct conversation; send/reply/
edit/delete; create group; transfer attachment; find old message; mute/pin; resolve
failed send; run diagnostics; manage/revoke session; log out. Administrator tasks:
search/disable/enable user; review role warning; revoke session/disconnect; query
audit; acknowledge alert; run worker; review configuration; publish announcement;
create export; enter/leave maintenance.

## Accessibility protocol

Repeat core journeys keyboard-only. Verify initial focus, logical tab order, focus
trap and restoration, first-invalid-field focus, composer/navigation shortcuts, and
no focus loss after refresh. With an available screen reader, verify labels, roles,
state, errors, progress, sender/timestamp/delivery reading, and destructive
confirmations. Repeat at 100%, 125%, and 150% text scale in light, dark, and high
contrast. Inspect clipping, wrapping, row/table readability, dialogs, composer,
tooltips, and focus indicators. Review in greyscale so online/offline, unread,
failure, health, severity, and selection remain understandable without colour.

## Clean infrastructure protocol

Follow `operations/deployment-and-installation.md` on a clean Debian 13 VM exactly.
Treat every undocumented prerequisite as a defect. Record package/Python/PostgreSQL/
Redis/Nginx versions, service user and filesystem permissions, mount identity,
systemd hardening output, migration revision, TLS chain/protocol results, health,
and authenticated smoke results.

From a separate LAN host scan all TCP ports. Expected: 443, optionally management-
restricted 22 and redirect-only 80. PostgreSQL 5432, Redis 6379, FastAPI 8000, and
development ports must be closed. Test trusted, wrong-host, expired, unknown-CA,
missing-intermediate, and pin-mismatch certificates; WSS succeeds only for trusted
TLS and there is no bypass.

On clean Windows 10 and 11 VMs without Python, install the Inno package, verify
shortcuts/resources/version/profile path/Credential Manager, launch and connect,
upgrade over representative encrypted state, confirm drafts/settings/offline queue/
transfers survive, repair if supported, uninstall while retaining profile by
default, then separately verify explicit profile removal using disposable data.

## Backup, upgrade, and rollback protocol

Create representative users, conversations, ciphertext messages/envelopes,
attachments, audit events, outbox records, configuration versions, and announcements.
Run coordinated backup; verify non-zero failure behavior, checksums, permissions,
status, alerting, previous-good preservation, and retention. Restore to a new clean
VM using the matching application/revision; invalidate sessions; verify audit,
objects, historical client decryption, workers/outbox, and smoke workflow.

Install Version A, create profile/server state, take verified backup, upgrade to B,
migrate, and verify every old/new workflow. Simulate failed health. Rehearse code-
only rollback only with compatible schema; otherwise restore database, attachments,
configuration, and release. Record any data-loss window. Never perform these tests
against production.

## Performance and reliability protocol

Record client/server CPU, RAM, storage, OS, network speed/latency, application,
PostgreSQL/Redis versions, and dataset. Measure cold/warm login, direct/group send,
outbox/WebSocket delivery, conversation pages at 1k/10k/100k messages, search,
dashboard, reconnect sync, 2/10/25/50/100-member groups, attachment chunk sizes and
throughput/memory, important `EXPLAIN ANALYZE` plans, and GUI freezes. Use repeated
runs and median/p95; do not cherry-pick.

In isolation restart PostgreSQL, Redis, Nginx, FastAPI, attachment mount, and
directory service. Simulate crash before/after commit and publication, interrupted
upload/download/sync, nearly-full server/client volumes, expiry boundaries, clock
movement, poison worker items, duplicate delivery, and long offline periods. Verify
health, clear user state, deterministic retry, no corruption/duplicate, preserved
drafts, and complete cleanup.
