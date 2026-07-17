# Server lifecycle and health

Task 08 turns the configuration, migration verifier, repositories, and Unit of Work
from Tasks 03–07 into lifecycle-owned server infrastructure. The FastAPI application
is still an application factory: constructing it creates lazy clients and pools but
opens no PostgreSQL or Redis connection. FastAPI lifespan is the only production
startup and shutdown owner.

## Construction and ownership

`build_server_container()` validates settings and constructs one application-scoped
`DatabaseManager`, `RedisManager`, `StorageHealthCheck`, `HealthAggregator`, and
`UnitOfWorkFactory`. The factory receives `DatabaseManager.create_session`, so a
request cannot create a session before database startup and schema verification.
Each Unit of Work continues to create and own one fresh session and repository
bundle; no long-lived service retains a request session.

The bootstrap module also exposes focused `verify_migration_state()` and
`verify_storage_paths()` diagnostics plus `run_startup_checks()` for callers that
need the same production checks without duplicating manager logic.

The container starts components in this order:

```text
PostgreSQL connectivity and Alembic revision
Redis connectivity or configured degraded fallback
Encrypted-file storage paths, write/fsync probe, and capacity reserve
Future injected WebSocket/worker lifecycle components
```

The future-component seam accepts only real injected lifecycle objects. Task 08 does
not create placeholder WebSocket managers or workers. Business services likewise do
not receive the whole container; `ServerServices` currently groups only the health
aggregator and can be extended through explicit construction in its owning stage.

## Startup and shutdown guarantees

`ServerContainer.start()` is lock-protected and idempotent after success. It records
each stage before starting it. A failed or cancelled stage therefore participates in
reverse-order rollback alongside every earlier stage. PostgreSQL failure or a schema
revision mismatch prevents readiness. Redis failure prevents startup only when
`redis.fallback_enabled` is false; otherwise durable PostgreSQL operations remain
available and aggregate health is degraded.
Readiness probes retry a degraded Redis connection within their bounded timeout, so
successful recovery returns the transient capability to healthy without a restart.

`stop()` is safe before startup, after partial startup, after successful startup,
and when called repeatedly. It marks the server unready first, attempts every
cleanup stage in reverse order, and records only the failure category when one
cleanup fails. One cleanup error cannot strand the remaining pools or clients.
Database pool and Redis-client cleanup are idempotent.

The database manager configures the documented pool size, overflow, connection and
statement timeouts, recycling, and pre-ping behavior. Startup runs `SELECT 1` and the
read-only Alembic head verifier. Adapter failures become credential-free
`DatabaseUnavailableError` values; revision mismatches preserve only revision IDs.
The Redis manager applies connection/operation timeouts, owns connection closure,
translates library errors, and builds colon-separated keys rooted in the configured
namespace.

## Storage readiness

Storage startup requires three absolute, distinct paths. Missing directories are
created only when configured. UNC/network paths are rejected unless network storage
is explicitly allowed, and POSIX world-writable paths are rejected. Every path must
support an exclusive write, flush, fsync, and cleanup probe. The attachment root
must retain both configured free-byte and free-percentage reserves. Health checks
repeat the write and capacity verification without returning paths or free-space
topology to unauthenticated callers.

No attachment `FileStorage` implementation is introduced here; chunk paths, atomic
file assembly, and attachment operations belong to the attachment stage. The Task
08 check is solely the lifecycle/readiness owner for configured storage.

## Health contracts and HTTP behavior

`HealthAggregator` runs PostgreSQL, Redis, and storage checks concurrently under a
bounded timeout. Unexpected check failures and timeouts become a generic unhealthy
component without exception text. Healthy database or Redis checks at or above the
configured latency warning threshold become degraded. Aggregate precedence is
unhealthy, degraded, then healthy.

The application exposes:

- `GET /health/live`: lightweight process liveness, always HTTP 200 while FastAPI can
  answer.
- `GET /health/ready`: minimal aggregate dependency state. Unhealthy returns HTTP
  503; healthy and deliberately degraded Redis fallback return HTTP 200.

Both public responses contain only state and a UTC timestamp. Component names,
latency, application/protocol versions, addresses, paths, exception text, and usage
data are excluded. `ServerContainer.get_health()` produces the separate detailed
DTO for the future authenticated administrator route. Task 08 deliberately does not
publish that DTO because Task 09 owns authenticated users and permission checks;
publishing it without that boundary would violate the specification.

## Configuration and migration effects

Task 08 uses the existing database, Redis, storage, monitoring, application, and
protocol settings without adding configuration keys. It adds no schema or Alembic
revision. The application does not auto-migrate; the database must already be at
`0002_refresh_reuse`. `validate-config` remains an I/O-free configuration check,
while `run` now correctly refuses to become operational without its critical
PostgreSQL and storage dependencies.

## Verification strategy

Deterministic tests replace lifecycle components through constructor injection and
cover ordered startup, duplicate startup, partial rollback, cleanup continuation,
repeated shutdown, database failure redaction, migration mismatch cleanup, Redis
healthy/degraded/required modes, namespace safety, storage path/write/capacity
checks, health timeouts and latency degradation, and live/ready HTTP status and
information boundaries.

`tests/integration/test_server_lifecycle_postgresql.py` is an opt-in real workflow.
With `BLUEBUBBLES_TEST_DATABASE_URL` naming an already migrated dedicated database,
it starts the production container, verifies the schema, creates and closes a real
session, observes Redis fallback plus healthy storage, and shuts down. It skips when
that deliberately explicit database is unavailable; SQLite is not a PostgreSQL
lifecycle substitute.
