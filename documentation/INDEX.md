# BlueBubbles repository index

This is the canonical navigation page for developers and AI coding agents. It
summarises where each implemented concern lives so a task can load focused context
instead of the complete repository or repeated master specification.

## Start here by task

| Need | Read first | Primary code |
|---|---|---|
| Tooling, package layout, quality gates | `development/repository-and-tooling.md` | `pyproject.toml`, `scripts/development` |
| Shared DTO/protocol/version contracts | `development/shared-contracts.md` | `src/bluebubbles/shared` |
| Server/client configuration | `development/configuration.md` | `src/bluebubbles/*/configuration`, `config` |
| Domain entities and typed errors | `development/domain-models-and-errors.md` | `src/bluebubbles/server/domain`, `src/bluebubbles/client/domain`, `src/bluebubbles/shared/errors` |
| PostgreSQL schema and upgrades | `development/database-schema-and-migrations.md` | `src/bluebubbles/server/database/models`, `migrations` |
| Repository contracts/adapters | `development/repository-infrastructure.md` | `src/bluebubbles/server/repositories` |
| Transaction ownership | `development/unit-of-work.md` | `src/bluebubbles/server/database/session.py`, `unit_of_work.py` |
| Server lifecycle and health | `development/server-lifecycle-and-health.md` | `src/bluebubbles/server/application.py`, `container.py`, `database/engine.py`, `redis.py`, `monitoring` |
| Authentication, sessions, and permissions | `development/authentication-and-sessions.md` | `src/bluebubbles/server/authentication`, `server/services`, `server/routes/authentication.py`, `client/security`, `client/services` |
| Users, contacts, and public keys | `development/users-contacts-and-public-keys.md` | `server/services/users.py`, `contacts.py`, `keys.py`, matching routes and repositories |
| Conversations and groups | `development/conversations-and-groups.md` | `server/services/conversations.py`, `groups.py`, matching routes and conversation repository |

Each finished stage also has a `development/task-NN-execution-report.md` containing
its exact completion boundary, compatibility decisions, verification evidence, and
environment-bound limitations. Task specifications remain authoritative in
`specification`; open only the requested numbered task unless a cited predecessor
contract must be checked.

## Runtime entry points

| Entry point | Purpose |
|---|---|
| `bluebubbles.server.main:main` | Validate configuration or run the FastAPI server |
| `bluebubbles.server.application:create_application` | Construct the server app and lifespan-owned container |
| `bluebubbles.client.main:main` | Start the independently configured PySide6 client |
| `bluebubbles.client.application:create_application` | Construct the current client application boundary |
| `alembic.ini` / `migrations/env.py` | Render or apply PostgreSQL migrations |

## Persistence lookup

| Concern | Interface | SQLAlchemy adapter / implementation |
|---|---|---|
| Users | `repositories/interfaces/users.py` | `repositories/sqlalchemy/users.py` |
| Sessions | `repositories/interfaces/sessions.py` | `repositories/sqlalchemy/sessions.py` |
| Contacts | `repositories/interfaces/contacts.py` | `repositories/sqlalchemy/contacts.py` |
| Public keys | `repositories/interfaces/keys.py` | `repositories/sqlalchemy/keys.py` |
| Conversations/groups | `repositories/interfaces/conversations.py` | `repositories/sqlalchemy/conversations.py` |
| Encrypted messages | `repositories/interfaces/messages.py` | `repositories/sqlalchemy/messages.py` |
| Encrypted attachments | `repositories/interfaces/attachments.py` | `repositories/sqlalchemy/attachments.py` |
| Immutable audit chain | `repositories/interfaces/audit.py` | `repositories/sqlalchemy/audit.py` |
| Announcements | `repositories/interfaces/announcements.py` | `repositories/sqlalchemy/announcements.py` |
| Admin jobs | `repositories/interfaces/administration.py` | `repositories/sqlalchemy/administration.py` |
| Configuration history | `repositories/interfaces/configuration.py` | `repositories/sqlalchemy/configuration.py` |
| Durable events | `repositories/interfaces/outbox.py` | `repositories/sqlalchemy/outbox.py` |
| Shared transaction | n/a | `database/unit_of_work.py` |

Domain/ORM conversion for users, sessions, conversations, messages, attachments,
and audit events is isolated under `repositories/mapping`. Query objects, cursor
pages, cursor encoding, and stored chunk metadata are in `repositories/types.py`.

## Tests by risk

| Risk | Evidence |
|---|---|
| Architecture/import and plaintext boundaries | `tests/unit/shared/test_architecture.py`, `test_security_contracts.py` |
| Configuration precedence and safety | `tests/unit/server/test_configuration.py`, `tests/unit/client/test_configuration.py` |
| Domain invariants and error mapping | `tests/unit/server/test_domain.py`, `tests/unit/client/test_domain.py`, `tests/unit/shared/test_errors_and_pagination.py` |
| Schema, seeds, migrations | `tests/unit/server/test_database_schema.py`, `tests/integration/test_database_migration.py` |
| Repository mapping and behavior | `tests/unit/server/test_repository_*.py`, `tests/integration/test_repository_postgresql.py` |
| Transaction lifecycle and isolation | `tests/unit/server/test_unit_of_work.py`, `tests/integration/test_unit_of_work_postgresql.py` |
| Startup rollback, dependency health, and readiness | `tests/unit/server/test_lifecycle.py`, `test_application.py`, `tests/integration/test_server_lifecycle_postgresql.py` |
| Authentication, token rotation, LDAP safety, permissions, and client secret handling | `tests/unit/server/test_authentication.py`, `test_authentication_services.py`, `tests/unit/client/test_authentication_services.py` |
| User/contact/key lifecycle and authenticated routes | `tests/unit/server/test_user_contact_key_services.py`, `test_task_10_11_routes.py` |
| Direct/group creation, membership hierarchy, ownership, and archiving | `tests/unit/server/test_conversation_group_services.py`, `test_task_10_11_routes.py` |
| Executable foundation workflow | `tests/integration/test_foundation_workflow.py` |

## Generated and local-only paths

Do not use `build`, `dist`, `.coverage`, caches, virtual environments, or local
environment files as source. They are generated evidence or machine-local state.
`pyproject.toml` defines direct dependencies and tools; `pylock.toml` locks the
resolved development graph.
