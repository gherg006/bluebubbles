# Server and client decommissioning

Decommissioning is a controlled security and retention event. Removing executable
files is separate from destroying messages, attachments, audit records, backups,
configuration, certificates, or secrets. Obtain the data owner, security owner and
backup owner approvals before starting, and record exact host/version/retention
decisions in the audit/change system.

## Preserve-first server removal

1. Enter maintenance mode and notify users.
2. Verify the complete audit chain and record its final hash.
3. Create a coordinated backup, restore it into an isolated host, and run the smoke
   and audit checks. A backup command alone is insufficient.
4. Record database revision, release hash, attachment count, backup locations,
   retention expiry, legal holds and approved destruction date.
5. Revoke client sessions and directory/service-account access.
6. Stop and disable the application and backup timer:

```sh
sudo systemctl disable --now bluebubbles.service bluebubbles-backup.timer
sudo systemctl status bluebubbles.service bluebubbles-backup.timer --no-pager
```

7. Remove the Nginx enabled-site link only after confirming the exact target, test
   Nginx, then remove the BlueBubbles firewall rules by their displayed rule number.
8. Archive the release manifest, checksums, configuration schema, audit evidence,
   licence notices, and this decommission record with the retained backup.

Do not remove `/var/lib/bluebubbles`, `/var/backups/bluebubbles`, the PostgreSQL
database, `/etc/bluebubbles`, certificates, or secrets during this preserve-first
procedure. Do not reuse the hostname/IP until DNS, certificates and clients have
been checked for stale trust.

## Windows client removal

Revoke the device/session first, confirm queued work is no longer required, use the
registered uninstaller, and verify the application binary is gone. Local encrypted
profiles and OS-protected private keys are user data: retain or destroy them only
under the approved endpoint-retention process. Removing ProgramData configuration
must not remove a user's private keys.

## Irreversible data destruction

> **Destructive operation warning:** there is deliberately no copy-and-paste data
> deletion command here. Database, storage, backup and secret destruction is
> irreversible and may breach retention or legal-hold duties.

After the recorded retention period, two authorised people must independently
verify the exact database, attachment root, backup sets, configuration, certificate
and secret targets. Use organisation-approved PostgreSQL, filesystem/media and
secret-destruction procedures, never broad recursive paths or administrator
databases. Record completion and validate that restored copies, replicas, snapshots,
off-site backups, monitoring and password-manager entries received the same
approved disposition.
