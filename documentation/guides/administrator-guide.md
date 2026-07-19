# Administrator guide

This guide covers application administration. System installation and startup are
in `complete-startup-guide.md`; incident commands are in
`../operations/administration-runbooks.md`; backup/restore/upgrade procedures are in
`../operations/backup-restore-upgrade.md`.

## Roles and separation of duty

- Employee: normal messaging/contact/profile capabilities.
- Helpdesk: limited user/session support without unrestricted roles or audit change.
- HR: approved identity-related administration only.
- Administrator: operational configuration, monitoring and normal administration.
- SuperAdministrator: protected highest-risk actions and bootstrap recovery.

Server services enforce capabilities. Hiding a page is not authorisation. Maintain
at least two tested SuperAdministrators, require reasons for privileged changes,
review role warnings, and never grant PostgreSQL/Redis/system access merely because
someone has an application role.

## Daily checks

1. Confirm public liveness/readiness through Nginx.
2. Review dependency/storage/backup/audit/worker health and critical alerts.
3. Confirm the last coordinated backup is recent and checksum-valid.
4. Review failed logins, token reuse, disabled users, audit failures, storage
   pressure, outbox failures, and directory-sync exceptions.
5. Acknowledge an alert only with an investigation note; acknowledgement does not
   correct the cause.

## User and session workflow

Search by safe identity fields. Before disable/role change, verify the target UUID,
current state, requested reason, approver, and impact. Disabling a user must revoke
sessions and prevent refresh. Session revocation must disconnect associated live
connections. Re-enable only after the cause and access policy are resolved.

Directory attributes remain directory-owned. Correct them in Active Directory and
run/await sync. Do not create shadow identities to work around directory failure.

## Audit and security workflow

Query by bounded time, actor, action, target and correlation ID. Verify recent chain
health daily and full-chain health after restore, migration, suspected tamper, or
before release. Runtime database credentials must fail audit `UPDATE` and `DELETE`.
Any chain mismatch is a critical incident: preserve evidence, restrict privileged
changes, verify backups, and do not repair rows in place.

Exports and diagnostics are generated as bounded jobs, stored temporarily, and
authorised at creation and download. They exclude passwords, tokens, private keys,
message/file plaintext, raw bind credentials, and unrestricted environment dumps.

## Configuration and maintenance

Validate proposed fields and expected configuration version. Record the reason,
previous safe value, new safe value, actor, and whether restart is required. Secret
rotation happens through protected files, not the configuration API. Enter
maintenance before controlled migrations or restore; ordinary writes should fail
clearly while health, logout, and maintenance control remain available.

## Backup, restore and upgrade

A green backup command is not proof. Every release requires a clean isolated
restore, audit verification, attachment sample verification, and full smoke test.
Before upgrade: verify release checksum/compatibility, successful recent backup,
migration plan, downtime communication, health rollback point, and schema rollback
limits. Application rollback is unsafe after incompatible migrations unless the
documented database recovery plan is executed.

## Emergency recovery

If all application administrators are inaccessible, use the interactive
`bluebubbles-create-admin` command from the Debian service environment. Protect
terminal access, create one temporary uniquely named identity, verify the bootstrap
audit event, restore normal administrators, revoke the emergency session, and
disable/remove the temporary access according to policy. Never edit role rows or
password hashes manually.

## Release restriction

The current build is not an accepted release candidate because the packaged client
backend is unbound and clean infrastructure/restore/usability evidence is missing.
Administrators must use the release status document, not artifact existence, as the
deployment authority.
