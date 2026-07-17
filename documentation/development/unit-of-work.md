# Unit of Work

Task 07 owns the transaction boundary above the Task 06 repositories. The
implementation is in `server/database/unit_of_work.py`; generic session construction
and safe scoped cleanup are in `server/database/session.py`.

## Ownership model

`UnitOfWorkFactory` receives an application-owned `async_sessionmaker` and a
`RepositoryFactory`. Each call creates a new `AsyncSession`, passes that exact
session to all twelve SQLAlchemy adapters, and returns one `UnitOfWork` that owns
session completion and closure. `ServerRepositories` is an immutable typed bundle;
the Unit of Work exposes both the bundle and named repository attributes.

Repositories may stage and flush changes so database constraints fail inside the
active transaction. They never commit, roll back, or close. Application services
must use the following explicit pattern:

```python
async with unit_of_work_factory() as unit_of_work:
    await unit_of_work.users.create(user)
    await unit_of_work.audit.append(event)
    await unit_of_work.outbox.add(outbox_event)
    await unit_of_work.commit()
```

Commit should be the final operation in the context. A normal exit without commit
rolls back, as does an exceptional exit. Exit always closes the session. Repeated
same-result completion is idempotent, while commit-after-rollback,
rollback-after-commit, flush-after-completion, re-entry, and use after closure raise
`UnitOfWorkStateError`.

## Failure behavior

Commit integrity failures become a redacted `ConflictError`; other SQLAlchemy
adapter failures become a redacted `RepositoryError`. The original SQL, parameters,
credentials, encrypted values, and driver detail are never copied into public error
metadata. A failed commit attempts rollback and marks the transaction rolled back.
If both a context body and cleanup fail, the body exception remains authoritative.

`session_scope()` is available for focused infrastructure operations that do not
need repositories. It never auto-commits and always rolls back and closes. Business
work should prefer `UnitOfWorkFactory` so all participants share one transaction.

## Compatibility notes

The repository bundle includes every Task 06 interface plus Task 09's focused
authentication metadata adapter: users, sessions, authentication credentials,
login attempts and role permissions, contacts,
public keys, conversations, messages, attachments, audit, announcements,
administration, configuration, and outbox. The message and attachment adapters now
accept the interface-level `Sequence` inputs, so their concrete method signatures
are substitutable for their protocols. No database engine or server-lifecycle
manager is introduced here; those belong to the next numbered stage.

Real PostgreSQL behavior is opt-in through `BLUEBUBBLES_TEST_DATABASE_URL`. The
integration test creates a user within a Unit of Work, observes it through the
shared repository session, exits without commit, and confirms a fresh Unit of Work
cannot see the rolled-back record.
