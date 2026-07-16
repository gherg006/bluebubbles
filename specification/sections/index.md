# BlueBubbles Specification Sections Index

This directory contains the modularised sections of the BlueBubbles Software Engineering & Architecture Specification.

## Original Specification
The complete, original specification is located at:
`specification/complete/bluebubbles-complete-specification.md`

**Warning:** The complete specification file is extremely large and should not be automatically indexed by coding assistants to avoid context window exhaustion. Please use these smaller, topic-based section files instead.

## Section Files

1. **[01-requirements-and-project-scope.md](01-requirements-and-project-scope.md)**
   - Project purpose, problem definition, stakeholders, functional/non-functional requirements, scope, roles, use cases, success criteria, constraints, limitations, and threat assumptions.
2. **[02-system-architecture.md](02-system-architecture.md)**
   - Overall architecture, layered modular monolith, modules, dependency boundaries, design patterns, class structure, data flows, application structure, and source-code organisation.
3. **[03-configuration-and-lifecycle.md](03-configuration-and-lifecycle.md)**
   - Typed settings, configuration precedence, dependency injection, application startup/shutdown, health lifecycle, environment profiles, error handling, diagnostics, and recovery architecture.
4. **[04-database-and-persistence.md](04-database-and-persistence.md)**
   - PostgreSQL schema, entities, tables, relationships, indexes, constraints, repositories, Unit of Work, migrations, transactional outbox, and persistence contracts.
5. **[05-authentication-authorisation-and-users.md](05-authentication-authorisation-and-users.md)**
   - Authentication, Active Directory, LDAP, local fallback, passwords, tokens, sessions, roles, permissions, users, contacts, account administration, and session revocation.
6. **[06-cryptography-and-key-management.md](06-cryptography-and-key-management.md)**
   - Threat model, AES-GCM, X25519, Ed25519, HKDF, identity keys, content keys, recipient envelopes, signatures, key storage, key rotation, key revocation, canonical serialisation, and cryptographic tests.
7. **[07-conversations-groups-and-messaging.md](07-conversations-groups-and-messaging.md)**
   - Direct conversations, groups, membership, ownership, moderation, messages, replies, editing, deletion, delivery states, read states, and message ordering.
8. **[08-rest-api-websockets-and-networking.md](08-rest-api-websockets-and-networking.md)**
   - REST endpoints, request/response models, error envelopes, pagination, WebSockets, realtime events, presence, typing, connection management, protocol negotiation, and networking.
9. **[09-attachments-and-file-transfer.md](09-attachments-and-file-transfer.md)**
   - Attachment encryption, chunking, upload, download, resume, manifests, checksums, temporary/permanent storage, and transfer recovery.
10. **[10-desktop-client-and-user-interface.md](10-desktop-client-and-user-interface.md)**
    - PySide6, Views, ViewModels, navigation, chat interface, composer, settings, transfers interface, administration interface, accessibility, themes, desktop notifications, and system tray.
11. **[11-local-storage-offline-and-synchronisation.md](11-local-storage-offline-and-synchronisation.md)**
    - Local database, encrypted cache, drafts, search, offline queue, connectivity, reconnection, event replay, synchronisation, conflict resolution, tombstones, and offline attachment recovery.
12. **[12-administration-audit-and-monitoring.md](12-administration-audit-and-monitoring.md)**
    - Administrative roles, dashboard, user controls, session controls, connection controls, audit events, audit hash chain, security alerts, workers, metrics, monitoring, and maintenance mode.
13. **[13-testing-and-quality-assurance.md](13-testing-and-quality-assurance.md)**
    - Unit testing, integration testing, security testing, cryptographic testing, API testing, WebSocket testing, GUI testing, performance testing, accessibility testing, acceptance testing, quality gates, and test evidence.
14. **[14-deployment-backup-and-operations.md](14-deployment-backup-and-operations.md)**
    - Debian deployment, PostgreSQL/Redis installation, Nginx, TLS, systemd, firewall, Windows packaging, installer, upgrade, rollback, backup, restore, operational runbooks, and emergency recovery.
15. **[15-implementation-roadmap.md](15-implementation-roadmap.md)**
    - Development phases, milestones, dependency order, exit gates, definitions of done, risk register, and release candidate process.
16. **[16-final-coding-ai-execution-contract.md](16-final-coding-ai-execution-contract.md)**
    - Mandatory implementation rules, prohibited shortcuts, required outputs, security invariants, database invariants, generation sequence, completion checks, final delivery requirements, and Version 1.0 definition.

## Suggested File Combinations for Implementation Phases

- **Repository Setup:** `01-requirements-and-project-scope.md`, `02-system-architecture.md`, `15-implementation-roadmap.md`
- **Database:** `04-database-and-persistence.md`
- **Authentication:** `05-authentication-authorisation-and-users.md`
- **Cryptography:** `06-cryptography-and-key-management.md`
- **Messaging:** `07-conversations-groups-and-messaging.md`
- **Attachments:** `09-attachments-and-file-transfer.md`
- **Desktop UI:** `10-desktop-client-and-user-interface.md`
- **Offline Synchronisation:** `11-local-storage-offline-and-synchronisation.md`
- **Administration:** `12-administration-audit-and-monitoring.md`
- **Testing:** `13-testing-and-quality-assurance.md`
- **Deployment:** `14-deployment-backup-and-operations.md`
