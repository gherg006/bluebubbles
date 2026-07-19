# Version 1.0 acceptance and traceability matrix

Status meanings: `PASS-AUTO` means the cited deterministic behavior passed;
`PARTIAL` means component evidence passed but required live/manual evidence did not
run; `NOT RUN` means the required environment or human participant was unavailable.
No `PARTIAL` or `NOT RUN` row may be represented as final release acceptance.

## Functional acceptance

| ID | Requirement and implementation | Verification | Status |
|---|---|---|---|
| AUTH-01 | Authenticate through provider, session and tokens | `test_authentication_services.py`, `test_authentication.py` | PASS-AUTO |
| AUTH-02 | Logout invalidates session | `test_authentication_services.py`, `test_task_10_11_routes.py` | PASS-AUTO |
| CONTACT-01 | Find and add contact | `test_user_contact_key_services.py`, `test_task_10_11_routes.py` | PASS-AUTO |
| CONV-01 | Canonical direct conversation without duplicate | `test_conversation_group_services.py`, PostgreSQL adapter test pending | PARTIAL |
| GROUP-01 | Group has owner and active membership | `test_conversation_group_services.py` | PASS-AUTO |
| GROUP-02 | Ownership transfers atomically and safely | `test_conversation_group_services.py` | PASS-AUTO |
| MSG-01 | Direct encrypted message send/receive | server/client Task 13 tests; real two-client journey unavailable | PARTIAL |
| MSG-02 | Group encrypted message recipient set | Task 12/13 crypto and messaging tests; live group unavailable | PARTIAL |
| MSG-03 | Message edit/version conflict | `test_task_13_messaging.py` | PASS-AUTO |
| MSG-04 | Soft deletion/version conflict | `test_task_13_messaging.py` | PASS-AUTO |
| MSG-05 | Delivery/read state update | `test_task_13_messaging.py` | PASS-AUTO |
| ATTACH-01 | Encrypted attachment transfer/checksum | Task 15 client/server/storage tests; live network unavailable | PARTIAL |
| OFFLINE-01 | Queued message replays once after reconnect | Task 17 offline/synchronisation tests | PASS-AUTO |
| SEARCH-01 | Private cached message search | Task 16 search/storage tests | PASS-AUTO |
| ADMIN-01 | Administrator disables user and sessions | Task 19 administration tests | PASS-AUTO |
| AUDIT-01 | Administrative action appends audit event | Task 19 administration/repository tests | PASS-AUTO |
| MONITOR-01 | Dependency failure changes dashboard health | Task 20 monitoring/worker tests | PASS-AUTO |

## Security acceptance

| ID | Requirement | Verification | Status |
|---|---|---|---|
| SEC-01 | Message plaintext absent from server contracts/logging | `test_security_contracts.py`, Task 13 tests | PASS-AUTO |
| SEC-02 | Attachment plaintext absent from server storage/contracts | Task 15 storage/attachment tests | PASS-AUTO |
| SEC-03 | Private key never enters server/network DTO | architecture/security contract and key-route tests | PASS-AUTO |
| SEC-04 | Wrong recipient cannot decrypt | Task 12 message crypto | PASS-AUTO |
| SEC-05 | Modified message/signature/tag fails | Task 12 message crypto/property tests | PASS-AUTO |
| SEC-06 | Revoked/rotated session rejected | authentication/session tests | PASS-AUTO |
| SEC-07 | Employee denied administration | Task 19 administration/routes | PASS-AUTO |
| SEC-08 | Traversal, absolute, Windows and outside-root paths rejected | Task 15 storage and Task 21/22 generated path tests | PASS-AUTO |
| SEC-09 | Diagnostic package excludes secrets/plaintext | Task 20 diagnostics plus Task 22 secret scan | PASS-AUTO |
| SEC-10 | Audit tampering detected | Task 19 audit verification tests | PASS-AUTO |
| SEC-11 | Certificate/hostname/trust failure blocks production | config/pinning tests pass; real TLS matrix unavailable | PARTIAL |
| SEC-12 | Removed group member has no future envelope/access | group/messaging tests; live WebSocket journey unavailable | PARTIAL |

The 2026-07-18 workstation and Debian-set dependency audits found
`DEF-DEP-001` (20 advisory records across six packages). Fixed pins were installed
and all tests rerun. Final `dependency-audit-2026-07-18.json` and
`server-dependency-audit-2026-07-18.json` contain no known vulnerabilities. This is
point-in-time evidence, not a permanent guarantee.

## Reliability acceptance

| ID | Requirement | Verification | Status |
|---|---|---|---|
| REL-01 | Restart preserves draft/profile | Task 16 storage lifecycle and Task 18 ViewModel tests | PASS-AUTO |
| REL-02 | Crash/retry after server commit creates no duplicate | Task 13 idempotency and Task 17 replay tests | PASS-AUTO |
| REL-03 | Server restart preserves messages | durable model/transaction tests pass; real restart unavailable | PARTIAL |
| REL-04 | Interrupted upload resumes | Task 15 transfer workflow | PASS-AUTO |
| REL-05 | Interrupted download resumes | Task 15 transfer workflow | PASS-AUTO |
| REL-06 | Redis loss/restart preserves authoritative data | fallback tests pass; real Redis restart unavailable | PARTIAL |
| REL-07 | Expired/gapped event cursor triggers safe resync | Task 14/17 networking/synchronisation | PASS-AUTO |
| REL-08 | Migration preserves data | rendered/fresh migration tests pass; real migrated PostgreSQL skipped | PARTIAL |
| REL-09 | Coordinated backup restores cleanly | implementation/static tests only; clean restore unavailable | NOT RUN |
| REL-10 | Graceful shutdown completes | lifecycle/worker cleanup pass; real systemd shutdown unavailable | PARTIAL |

## Accessibility acceptance

Task 18 widget tests verify accessible names, keyboard-oriented controls, high
contrast, theme switching, font scaling logic, focusable navigation/dialogs, and
non-colour labels. Human keyboard/screen-reader/layout inspection remains required.

| IDs | Automated evidence | Required remaining evidence | Status |
|---|---|---|---|
| ACC-01..03 | login/navigation/composer controls and shortcuts | complete keyboard-only journey | PARTIAL |
| ACC-04 | accessible names asserted on icon/action controls | screen-reader announcement review | PARTIAL |
| ACC-05 | theme focus styling | visible focus inspection at every screen | PARTIAL |
| ACC-06 | high-contrast theme model/widget tests | full-screen contrast inspection | PARTIAL |
| ACC-07 | 100/125/150% scaling logic | clipping/wrapping inspection at 150% | PARTIAL |
| ACC-08 | ViewModel error state | focus movement and announcement inspection | PARTIAL |
| ACC-09 | textual state labels in widgets | greyscale journey review | PARTIAL |
| ACC-10 | dialog/widget construction | focus trap/restore with keyboard and screen reader | PARTIAL |

## Performance acceptance

The local evidence records Windows 11, Python 3.13.5, 20 logical CPUs, synthetic
data, and no external services. AES-GCM message encryption, canonical serialization,
10,000-word tokenization, FastAPI construction, 16 MiB throughput, and traced
allocation passed their component thresholds. They do not measure LAN/database/
WebSocket or GUI journeys.

| IDs | Evidence | Status |
|---|---|---|
| PERF-01..04 | no directory/database/LAN recipient setup | NOT RUN |
| PERF-05 | 10,000-word tokenization 2.8739 ms; full indexed search not measured | PARTIAL |
| PERF-06 | 16 MiB crypto buffer 2741.56 MiB/s; network/disk transfer not measured | PARTIAL |
| PERF-07 | 16 MiB traced peak 16 MiB; full transfer pipeline not measured | PARTIAL |
| PERF-08..10 | no live dashboard, reconnect dataset, or human GUI freeze capture | NOT RUN |

## Operational acceptance

| ID | Requirement | Evidence | Status |
|---|---|---|---|
| OPS-01 | Clean Debian install | guide/scripts ready; Debian/WSL/Docker unavailable | NOT RUN |
| OPS-02 | Starts on boot | systemd unit statically verified | NOT RUN |
| OPS-03 | Only intended ports exposed | Nginx/firewall templates verified; LAN scan unavailable | NOT RUN |
| OPS-04 | Accurate public health | application/monitoring tests pass; deployed proxy unavailable | PARTIAL |
| OPS-05 | Backup succeeds | planner/manifest/status tests; PostgreSQL backup unavailable | NOT RUN |
| OPS-06 | Restore succeeds | runbook only; clean restore host unavailable | NOT RUN |
| OPS-07 | Upgrade succeeds | guarded script/static checks; two installed releases unavailable | NOT RUN |
| OPS-08 | Rollback succeeds | guarded script/runbook; compatible live stack unavailable | NOT RUN |
| OPS-09 | Certificate warning/failure | TLS health/config tests; real certificate matrix unavailable | PARTIAL |
| OPS-10 | Emergency administrator recovery | bootstrap/administration tests and runbook | PARTIAL |

## Automated subsystem traceability

| Subsystem | Primary implementation | Primary evidence |
|---|---|---|
| Configuration/limits | client/server configuration packages | configuration tests plus 117 generated boundary cases |
| Domain/errors | client/server domain, shared errors | domain, error mapping, recovery tests |
| PostgreSQL/transactions | database, repositories, migrations, UoW | schema/mapping/adapters; three guarded real-DB tests |
| Authentication/sessions/permissions | authentication and server services | authentication, session, permission, route tests |
| Users/contacts/keys | services/routes/repositories | Task 10/11 tests |
| Conversations/groups/messages | services/routes/repositories | conversation/group and Task 13 tests |
| Cryptography | client security/shared envelopes | Task 12/15 and property tests |
| Attachments/storage | client/server attachment services/storage | Task 15 storage and transfer tests |
| WebSocket/outbox | networking/websocket/workers | Task 14 and Task 20 tests |
| Local cache/search | client storage/search | Task 16 tests |
| Offline/sync/conflicts | client offline queue/synchronisation | Task 17 tests |
| GUI/ViewModels/accessibility | client UI | Task 18 task/ViewModel/widget tests |
| Administration/audit/alerts | Task 19 services/routes/repositories | Task 19 tests |
| Monitoring/workers/maintenance | Task 20 services/workers | Task 20 tests |
| Deployment/packaging/backup | deployment packages/templates/scripts | Task 21 tests, verified archive, packaged-client smoke |
| Static/dependencies/secrets | tooling and lock | Black, Ruff, mypy, secret scan, pip-audit |
