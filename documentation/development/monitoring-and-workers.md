# Monitoring and workers

Task 20 extends the timeout-bounded health aggregator with database, Redis,
directory, storage, TLS certificate, outbox backlog, worker, WebSocket and backup
status checks. Public health remains minimal. Permission-protected detailed health
includes safe component latency/state plus derived authentication, messaging,
presence, attachment and administration capability states.

`monitoring.backup_status_path` may identify a protected JSON status file written
by the deployment's backup process. It must contain an aware `completed_at` plus
true `successful` and `checksum_valid` values. `backup_maximum_age_hours` controls
staleness. BlueBubbles validates backup evidence; it does not pretend to perform
or restore deployment backups.

The worker manager owns a fixed registry and starts/stops it with application
lifespan. The critical outbox publisher, expired-session cleanup and audit-chain
verification workers run serialised batches and retain only safe failure codes.
Manual execution is permission checked, restricted to registered/manual-safe
workers, protected against overlap and recorded in worker history plus audit.
Critical workers cannot be paused.

The dashboard combines dependency health, connection count and content-free disk
metrics. Diagnostics run only named checks under timeouts. Maintenance is an
audited state machine; read-only and offline states reject normal write requests
while health, authentication and administration recovery endpoints remain
available.

Tests in `tests/unit/server/test_task_20_monitoring_workers.py` cover every added
health checker, capability aggregation, recurring lifecycle, cancellation,
failure state, manual execution, metrics, dashboard, diagnostics and maintenance.
