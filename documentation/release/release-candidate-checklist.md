# Release-candidate checklist

This checklist is a promotion gate, not a statement that a release exists. Every
row requires retained evidence and every critical row must pass. The automated
assessment is run with `python -m scripts.release.assess_candidate`.

| Gate | Required evidence | Current status |
|---|---|---|
| Source version and clean tree | reviewed commit/tag; empty porcelain status | BLOCKED - working changes are not committed |
| Full quality suite | Black, Ruff, strict mypy, pytest and >=90% branch coverage | PASS - 489 passed, 3 guarded skips, 90.18% |
| Dependency safety | current workstation and exact server-set audit JSON | 2026-07-18 clean; 2026-07-19 refresh blocked by external-inventory privacy policy |
| Server archive | reproducible archive, external manifest and SHA-256 sidecar | PASS - rebuilt twice; final hash is retained outside the archive in its sidecar |
| Debian installation | clean Debian 13 Trixie transcript and package inventory | NOT RUN |
| Database lifecycle | migrate, restart, backup, clean-host restore, rollback | NOT RUN on PostgreSQL |
| Redis and LDAP | live failure/recovery and selected-provider journeys | NOT RUN |
| Reverse proxy and TLS | valid, expired, wrong-host, untrusted and rotation tests | NOT RUN |
| Client production composition | real HTTP/WebSocket/storage/crypto/offline backend | BLOCKED by `RC-CLIENT-001` |
| Windows installer | versioned Setup executable, checksum, install/uninstall | BLOCKED by `RC-INSTALLER-001` |
| Two-client journeys | login through administration, offline and attachment paths | NOT RUN |
| Accessibility/usability | keyboard, screen reader, scaling and participant record | NOT RUN |
| Documentation | installation, operation, user, admin, developer and reference set | COMPLETE subject to final link/test pass |
| Defects | zero open critical/high defects approved for candidate | BLOCKED |
| Promotion decision | machine-readable assessment says `eligible: true` | BLOCKED |

## Clean-environment execution order

1. Freeze the reviewed revision and prove the tree is clean.
2. Run the complete quality and secret checks from the locked environment.
3. Audit the full lock and exact Debian runtime dependency set.
4. Build the reproducible server archive twice and compare SHA-256 values.
5. Install on a fresh Debian 13 Trixie host by following the complete startup guide.
6. Apply migrations with the restricted migration role and start systemd services.
7. Validate Nginx, firewall exposure, trusted-proxy handling, TLS and health.
8. Build the Windows bundle and Setup executable from the frozen revision.
9. Install on a clean Windows 11 machine with no developer tools present.
10. Run login, logout, contacts, direct/group messages, edit/delete/read receipts.
11. Run upload/download, interruption/resume, tamper and out-of-bounds tests.
12. Run offline queue, reconnect, restart, duplicate-delivery and event-gap tests.
13. Run employee/administrator permissions, audit, alert and recovery journeys.
14. Stop/restart Redis, PostgreSQL, Nginx and the application in controlled tests.
15. Back up live test data and restore onto a second clean Debian host.
16. Upgrade from the previous compatible version and exercise rollback.
17. Complete the manual accessibility, usability and performance protocols.
18. Close and retest every defect, updating the acceptance matrix without inference.
19. Run the automated candidate assessment with all final artifact paths.
20. Only when it returns `ELIGIBLE`, sign/tag and publish the candidate.
