# BlueBubbles implementation task specifications

The complete Version 1.0 specification has been split using its own mandatory 24-stage development sequence. Each task file embeds the project-wide architecture and execution rules and then reproduces the complete relevant source parts verbatim. Duplication is deliberate: a task file can be handed to an implementation AI without relying on a summary or silently losing an integration constraint.

The original single-file specification remains unchanged at `complete/bluebubbles-complete-specification.md` for audit and traceability.

## Ordered tasks

1. [Repository and tooling](01-repository-and-tooling.md) — predecessors: none.
2. [Shared contracts](02-shared-contracts.md) — predecessors: 01.
3. [Configuration](03-configuration.md) — predecessors: 01, 02.
4. [Domain models and errors](04-domain-models-and-errors.md) — predecessors: 02, 03.
5. [Database schema and migrations](05-database-schema-and-migrations.md) — predecessors: 03, 04.
6. [Repository infrastructure](06-repository-infrastructure.md) — predecessors: 05.
7. [Unit of Work](07-unit-of-work.md) — predecessors: 06.
8. [Server lifecycle and health](08-server-lifecycle-and-health.md) — predecessors: 03, 07.
9. [Authentication and sessions](09-authentication-and-sessions.md) — predecessors: 08.
10. [Users, contacts and public keys](10-users-contacts-and-public-keys.md) — predecessors: 09.
11. [Conversations and groups](11-conversations-and-groups.md) — predecessors: 10.
12. [Client cryptographic prototype](12-client-cryptographic-prototype.md) — predecessors: 10, 11.
13. [Encrypted messaging](13-encrypted-messaging.md) — predecessors: 11, 12.
14. [WebSocket and outbox delivery](14-websocket-and-outbox-delivery.md) — predecessors: 08, 13.
15. [Attachments](15-attachments.md) — predecessors: 13, 14.
16. [Local client storage](16-local-client-storage.md) — predecessors: 03, 09, 12.
17. [Offline queue and synchronisation](17-offline-queue-and-synchronisation.md) — predecessors: 14, 16.
18. [PySide6 interface](18-pyside6-interface.md) — predecessors: 09, 11, 13, 15, 16, 17.
19. [Administration and audit](19-administration-and-audit.md) — predecessors: 09, 11, 14, 18.
20. [Monitoring and workers](20-monitoring-and-workers.md) — predecessors: 08, 14, 19.
21. [Deployment and packaging](21-deployment-and-packaging.md) — predecessors: 05, 08, 18, 20.
22. [Full testing](22-full-testing.md) — predecessors: 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21.
23. [Documentation](23-documentation.md) — predecessors: 22.
24. [Release candidate](24-release-candidate.md) — predecessors: 21, 22, 23.

## Rules for use

- Give an implementation AI one task file at a time, in numeric order.
- A task is complete only after every requirement and verification gate in that file passes.
- Do not treat duplicated cross-task contracts as permission to skip predecessors or begin later stages.
- The original chapter and part numbering is preserved inside every verbatim extract.
