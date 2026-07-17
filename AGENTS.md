# BlueBubbles agent guide

Use this file as the shortest route into the repository. Read
`documentation/INDEX.md` before scanning the tree or opening the embedded complete
specification. The current completed implementation stage is Task 07, Unit of Work;
later service, lifecycle, networking, client-storage, and GUI stages remain out of
scope until their numbered task is requested.

## Fast context route

1. Read the requested `specification/NN-*.md` task's completion boundary and
   task-specific sections. Project-wide text is repeated inside task files.
2. Read the matching `documentation/development/task-NN-execution-report.md` and
   the focused topic document linked from `documentation/INDEX.md`.
3. Inspect only the packages named in the repository map below.
4. Run `python scripts/development/run_quality_checks.py` before declaring a stage
   complete. Python 3.13 and the locked development dependencies are required.

## Repository map

| Location | Owns |
|---|---|
| `src/bluebubbles/shared` | Wire-safe DTOs, protocol/version rules, configuration base types, security envelopes, errors, logging |
| `src/bluebubbles/server/domain` | Infrastructure-neutral server entities and invariants |
| `src/bluebubbles/server/database/models` | SQLAlchemy persistence representation only |
| `src/bluebubbles/server/database` | Metadata, migrations, session helpers, Unit of Work |
| `src/bluebubbles/server/repositories/interfaces` | Application-facing persistence protocols |
| `src/bluebubbles/server/repositories/mapping` | Pure ORM/domain conversion |
| `src/bluebubbles/server/repositories/sqlalchemy` | PostgreSQL repository adapters; never commit or close sessions |
| `src/bluebubbles/client/domain` | Client-only local entities; no ORM or GUI |
| `config` | Layered example/default YAML; secrets stay outside Git |
| `migrations` | Alembic environment and immutable numbered revisions |
| `tests/unit` | Deterministic component and contract tests |
| `tests/integration` | Rendered migration and opt-in real PostgreSQL workflows |
| `documentation` | Focused architecture notes, task evidence, and the full index |

## Non-negotiable boundaries

- Dependency direction is presentation -> services -> protocols -> adapters.
- The client and GUI never access PostgreSQL. Repositories never commit, roll back,
  close sessions, encrypt, authorize, or emit UI.
- A `UnitOfWorkFactory` call creates one fresh session and one complete repository
  bundle. Services commit explicitly; an unfinished or failed context rolls back.
- ORM models, domain models, and Pydantic DTOs are distinct representations.
- Message/file plaintext and private keys never enter server persistence, logs,
  errors, tests, or fixtures.
- Preserve unrelated worktree changes. Do not add placeholders, TODO methods, weak
  substitutes for PostgreSQL behavior, or later-stage skeletons.

## Verification and environment limits

The normal quality runner checks Black, Ruff, strict mypy, pytest, and branch-aware
coverage (minimum 90%). Real PostgreSQL tests require an already migrated dedicated
database named by `BLUEBUBBLES_TEST_DATABASE_URL`; without it they intentionally
skip. Never point destructive or test workflows at an administrator's database.
