# Documentation coverage map

This map proves equivalent coverage for the Task 23 required document set. Focused
notes remain authoritative for implementation details; consolidated guides provide
the human route through them.

| Required coverage | Authoritative document(s) |
|---|---|
| README | `../README.md` |
| Architecture | `architecture/system-architecture.md` |
| Security | `security/security-and-cryptography.md`, `SECURITY.md` |
| Cryptography | `security/security-and-cryptography.md`, `development/client-cryptographic-prototype.md` |
| Database | `development/database-schema-and-migrations.md` |
| API | `reference/api-and-websocket-reference.md` |
| WebSocket | generated API reference and `development/websocket-and-outbox-delivery.md` |
| Client | `guides/user-guide.md`, `development/pyside6-interface.md` |
| Administration | `guides/administrator-guide.md`, `operations/administration-runbooks.md` |
| Installation | `guides/complete-startup-guide.md` |
| Configuration | `reference/configuration-reference.md`, `development/configuration.md` |
| Active Directory | `guides/active-directory.md` |
| Backup and restore | `operations/backup-restore-upgrade.md` |
| Upgrade and rollback | `operations/backup-restore-upgrade.md` |
| Operations | `operations/deployment-and-installation.md`, administration runbooks |
| Decommissioning | `operations/decommissioning.md` |
| Testing | `testing/testing-strategy.md`, `testing/acceptance-matrix.md` |
| Known limitations | `release/known-limitations-and-evaluation.md` |
| User guide | `guides/user-guide.md` |
| Administrator guide | `guides/administrator-guide.md` |
| Developer guide | `guides/developer-guide.md` |
| Algorithms and pseudocode | `architecture/algorithms-and-pseudocode.md` |
| NEA evidence | `nea-evidence-index.md` |
| Release status/notes/checklist | `release/` |

Generated references are recreated by
`python scripts/documentation/generate_reference.py`. Documentation link and
implementation-marker tests prevent stale route names, missing required manuals,
incorrect WebSocket paths and silent removal of the release-blocker warning.
