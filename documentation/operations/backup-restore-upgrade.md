# Backup, restore, upgrade, rollback, and recovery

BlueBubbles defines an example RPO of 24 hours and RTO of 4 hours for the NEA
environment. Operators must replace these with approved organisational targets.
Redis is transient; authoritative recovery requires PostgreSQL, encrypted
attachments, configuration, required protected secrets, TLS policy, release
metadata, audit history, and backup evidence.

## Coordinated backup

The installed timer runs `scripts/deployment/backup.py` daily. The default unit
stops the application briefly, creates a transactionally consistent custom-format
`pg_dump`, archives attachment and configuration trees, rejects symlinks, streams
SHA-256 verification, writes a manifest, then atomically publishes the protected
Task 20 status record. It always attempts service restart. Any component failure
returns non-zero, records only a safe exception category, and cannot be reported as
a successful verified backup.

Durable backup sets must be copied into an encrypted, access-controlled repository
separate from the server. Backup keys must not be stored unprotected beside data.
Retain at least 14 daily, 8 weekly, and 12 monthly sets unless approved policy
states otherwise. Pruning must never remove the only verified set and must not run
during restore.

Check after every run:

```bash
sudo systemctl status bluebubbles-backup.service
sudo cat /var/lib/bluebubbles/state/backup-status.json
sudo journalctl -u bluebubbles-backup.service --since today
```

## Clean-environment restore

Destructive warning: never restore into a production database while clients or
workers are connected. Record the chosen backup ID, data-loss window, application
version, database revision, attachment snapshot, and operator. Verify every
checksum before continuing.

On a new isolated Debian 13 VM, install the matching application release and
dependencies without starting ordinary access. Restore PostgreSQL into a newly
created database owned by the intended role:

```bash
sudo -u postgres createdb --owner=bluebubbles_app bluebubbles_restore
sudo -u postgres pg_restore --clean --if-exists --no-owner \
  --dbname=bluebubbles_restore <verified-database.dump>
```

Extract attachments and configuration only from the trusted backup into empty
staging directories. Review archive members before extraction; reject absolute
paths, parent traversal, links, and device files. Copy validated content to the
configured paths, restore exact ownership/modes, confirm the mount identity and
free space, and install required secrets through the approved recovery owner.

Start the matching release in maintenance mode. Verify revision, database access,
attachment object count and sample hashes, audit integrity, public-key history,
TLS, directory access, workers, and outbox. Release stale outbox locks only through
the controlled administrative workflow. Invalidate all restored sessions and
require login again. Create a new audit event stating backup ID, restore reason,
operator, validation result, and data-loss window without modifying historical
hashes. Run the complete authenticated smoke test before reopening access.

## Upgrade

Before upgrade, review compatibility and rollback notes, verify current health,
free space, audit chain, attachment mount, and the most recent restore test. Notify
users, record the current symlink and revision, and create a verified coordinated
backup. `upgrade_server.sh` accepts only an absolute archive and a 64-character
lowercase SHA-256, refuses an unverified backup, installs into a new immutable
release directory, validates production configuration, stops gracefully, migrates,
switches the release symlink atomically, starts, and checks bounded liveness and
readiness.

It does not replace the required authenticated smoke test: administrator login,
conversation load, encrypted send/receive, attachment round-trip, health page,
audit verification, worker/outbox health, and logout. Observe logs and metrics for
at least the locally approved interval before declaring success.

## Rollback

`rollback_server.sh` performs application-only rollback. Use it only when schema,
protocol, stored data, and configuration remain backward compatible. It changes the
symlink atomically, reinstalls the previous package into the shared environment,
starts the service, and checks health.

If migration is incompatible, do not run the application-only script. Stop access,
restore the pre-upgrade PostgreSQL dump, restore the matching attachment snapshot
and configuration, activate the previous release, invalidate sessions, verify audit
and data consistency, and run smoke tests in maintenance mode. Communicate that all
post-backup activity may be lost. Record reason, decision time, releases, revision,
backup, attachment snapshot, service-return time, validation, and data-loss window.

## Incident runbook index

Use `administration-runbooks.md` for database, Redis, storage, audit, authentication,
worker, and emergency-maintenance incidents. For certificate renewal, install the
new full chain and protected key, validate `nginx -t`, reload rather than restart,
test chain/hostname/expiry/TLS versions, then update monitoring evidence. For a
backup failure, preserve the previous verified set, inspect the component result,
correct capacity/permission/dependency failure, rerun once, verify checksums, and
clear the alert only after a successful restore-capable set exists.
