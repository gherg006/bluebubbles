# Administration operational runbooks

Preserve timestamps, correlation IDs and audit event IDs throughout. Never copy
passwords, tokens, private keys, message plaintext or attachment plaintext into
tickets, logs or exports.

## User cannot log in

- **Symptoms:** Valid user cannot create a session.
- **Likely causes:** Disabled/locked account, directory failure, clock skew or invalid credentials.
- **Impact:** One user or the directory-backed population cannot authenticate.
- **Checks:** User state, login-attempt category, directory health, server time and session health.
- **Safe recovery steps:** Correct account state with a reason; unlock via approved identity policy; restore directory connectivity; ask the user to retry without collecting their password.
- **When to escalate:** Multiple users fail, directory TLS fails, or identity state is unclear.
- **Evidence to preserve:** Correlation ID, username, time window, account state and alert/audit IDs.
- **Relevant error codes:** `INVALID_CREDENTIALS`, `ACCOUNT_LOCKED`, `ACCOUNT_DISABLED`, `DIRECTORY_UNAVAILABLE`.
- **Relevant logs:** Authentication and directory health records with the correlation ID.
- **Relevant dashboard pages:** Users, Sessions, Detailed health, Security alerts.

## User lost device

- **Symptoms:** A device is missing or suspected compromised.
- **Likely causes:** Loss, theft or unauthorised access.
- **Impact:** Active session and locally stored encrypted material may be exposed.
- **Checks:** User sessions, active connections, device name, last activity and audit history.
- **Safe recovery steps:** Revoke the device session with a reason, verify commit, disconnect its connection, and follow organisational endpoint/key-recovery policy.
- **When to escalate:** Primary cryptographic device was lost or suspicious activity exists.
- **Evidence to preserve:** Session/device IDs, revocation audit ID, times and observed activity metadata.
- **Relevant error codes:** `SESSION_REVOKED`, `SESSION_COMPROMISED`.
- **Relevant logs:** Session revocation and WebSocket disconnect events.
- **Relevant dashboard pages:** Users, Sessions, Connections, Audit.

## User role incorrect

- **Symptoms:** Missing controls or excessive access.
- **Likely causes:** Wrong fixed role or directory group mapping.
- **Impact:** Work blocked or privilege exposure.
- **Checks:** Current role, capability response, directory groups/mapping and role-change audit.
- **Safe recovery steps:** Confirm approval, apply the least-privileged fixed role with a reason, then have the user refresh their session.
- **When to escalate:** Administrator/SuperAdministrator assignment or mapping conflict is involved.
- **Evidence to preserve:** Old/new role, approver, reason, audit ID and directory group snapshot.
- **Relevant error codes:** `INSUFFICIENT_PERMISSIONS`, `PERMISSION_DENIED`, `LAST_SUPERADMIN`.
- **Relevant logs:** Role synchronisation and administrative role-change records.
- **Relevant dashboard pages:** Users, Configuration history, Audit.

## Redis unavailable

- **Symptoms:** Presence/realtime capability degraded; Redis health unhealthy.
- **Likely causes:** Service outage, network path, authentication or capacity.
- **Impact:** Presence/rate-limit coordination may degrade; durable database work remains authoritative.
- **Checks:** Redis component health, capability health and Redis service/network status.
- **Safe recovery steps:** Restore the configured Redis service/network, validate credentials from protected configuration, then confirm health recovery.
- **When to escalate:** Repeated outage, data eviction pressure or suspected credential compromise.
- **Evidence to preserve:** Health transitions, outage window, infrastructure events and alert IDs.
- **Relevant error codes:** `REDIS_UNAVAILABLE`, `SERVICE_UNAVAILABLE`.
- **Relevant logs:** Redis lifecycle and health records.
- **Relevant dashboard pages:** Dashboard, Detailed health, Security alerts.

## Active Directory unavailable

- **Symptoms:** Directory health unhealthy and directory users cannot log in.
- **Likely causes:** LDAPS/network/DNS failure, certificate expiry or service-account issue.
- **Impact:** New directory authentications and synchronisation fail.
- **Checks:** Directory and TLS health, DNS/connectivity, certificate chain and bind-account state.
- **Safe recovery steps:** Restore LDAPS and trusted certificates or approved bind credentials; do not enable insecure LDAP; verify with diagnostics.
- **When to escalate:** Certificate trust or directory security team intervention is needed.
- **Evidence to preserve:** Safe failure category, timestamps, certificate metadata and alert ID.
- **Relevant error codes:** `DIRECTORY_UNAVAILABLE`, `INVALID_CREDENTIALS`.
- **Relevant logs:** Directory health/authentication records without credentials.
- **Relevant dashboard pages:** Detailed health, Diagnostics, Security alerts.

## Attachment storage full

- **Symptoms:** Storage critical and uploads fail.
- **Likely causes:** Capacity exhaustion, abandoned temporary files or quota issue.
- **Impact:** New attachment uploads unavailable; existing encrypted files should remain readable.
- **Checks:** Storage percentage, configured roots, active uploads and cleanup worker status.
- **Safe recovery steps:** Expand capacity or run the approved orphan cleanup; verify references before removal; confirm health and upload recovery.
- **When to escalate:** Referenced ciphertext is at risk or capacity cannot be restored safely.
- **Evidence to preserve:** Capacity measurements, cleanup job/audit IDs and affected upload IDs.
- **Relevant error codes:** `STORAGE_UNAVAILABLE`, `ATTACHMENT_TOO_LARGE`.
- **Relevant logs:** Storage health, upload and cleanup worker records.
- **Relevant dashboard pages:** Dashboard, Detailed health, Workers.

## Database unavailable

- **Symptoms:** Readiness and most capabilities unavailable.
- **Likely causes:** PostgreSQL outage, pool exhaustion, network failure or schema mismatch.
- **Impact:** Authoritative reads/writes, authentication and audit persistence stop.
- **Checks:** Database health, PostgreSQL service, connection capacity and Alembic revision.
- **Safe recovery steps:** Stop unsafe retries, restore the dedicated database service, verify exact migration head, then restart normally.
- **When to escalate:** Corruption, failed migration, restore requirement or unknown target database.
- **Evidence to preserve:** Revision, outage window, database diagnostics and infrastructure events.
- **Relevant error codes:** `DATABASE_UNAVAILABLE`, `SERVICE_UNAVAILABLE`.
- **Relevant logs:** Database startup, pool and migration verification records.
- **Relevant dashboard pages:** Detailed health, Diagnostics, Maintenance.

## Outbox backlog

- **Symptoms:** Outbox degraded/unhealthy; realtime delivery delayed.
- **Likely causes:** Worker failure, WebSocket publication failure or poison event.
- **Impact:** Committed messages remain durable but delivery is delayed.
- **Checks:** Backlog count, oldest age, worker state/failures and WebSocket health.
- **Safe recovery steps:** Correct the dependency, manually run the outbox worker with a reason, and confirm backlog drains; do not delete unpublished rows.
- **When to escalate:** Backlog grows, poison isolation repeats or delivery ordering is uncertain.
- **Evidence to preserve:** Counts/ages, worker execution IDs, failure codes and audit IDs.
- **Relevant error codes:** `WORKER_FAILED`, `SERVICE_UNAVAILABLE`.
- **Relevant logs:** Outbox worker, publication and connection records.
- **Relevant dashboard pages:** Dashboard, Workers, Detailed health, Audit.

## Audit verification failed

- **Symptoms:** Verification result invalid or audit worker repeatedly fails.
- **Likely causes:** Modification, deletion, reordering, incomplete migration or chain-state corruption.
- **Impact:** Audit evidence integrity cannot be trusted after the last verified point.
- **Checks:** Failure code/sequence, recent then full verification, database access history and backups.
- **Safe recovery steps:** Enter read-only maintenance, preserve the database and logs, restrict access and investigate from a forensic copy; never rewrite hashes to hide failure.
- **When to escalate:** Immediately to security and database owners.
- **Evidence to preserve:** Database snapshot, chain head, failure sequence, verification output and access logs.
- **Relevant error codes:** `AUDIT_INTEGRITY_FAILED`, `DATABASE_UNAVAILABLE`.
- **Relevant logs:** Audit verification worker and database administrative access.
- **Relevant dashboard pages:** Audit verification, Security alerts, Workers, Maintenance.

## Certificate nearing expiry

- **Symptoms:** TLS health degraded with expiry warning.
- **Likely causes:** Renewal not scheduled or replacement not deployed.
- **Impact:** Clients may soon reject HTTPS/WebSocket connections.
- **Checks:** Subject/expiry/fingerprint, trusted chain, configured paths and client trust policy.
- **Safe recovery steps:** Obtain an approved certificate, verify chain/key permissions, deploy through normal configuration and restart, then confirm fingerprint/health.
- **When to escalate:** Private-key exposure, chain mismatch or renewal authority failure.
- **Evidence to preserve:** Old/new fingerprints, validity dates, change approval and restart audit.
- **Relevant error codes:** `CRYPTOGRAPHIC_VERIFICATION_FAILED`, `CONFIGURATION_INVALID`.
- **Relevant logs:** TLS health and server startup records.
- **Relevant dashboard pages:** Detailed health, Configuration, Security alerts.

## Worker repeatedly failing

- **Symptoms:** Worker failure count crosses threshold.
- **Likely causes:** Dependency outage, invalid durable item or storage/database failure.
- **Impact:** The worker's cleanup, verification or delivery function is delayed.
- **Checks:** Safe failure code, last run times, dependencies and execution history.
- **Safe recovery steps:** Fix the dependency, run once manually if allowed, observe one successful cycle; do not pause critical workers.
- **When to escalate:** Critical worker, repeated poison item or audit verification failure.
- **Evidence to preserve:** Execution IDs, counts, failure codes, dependency health and audit records.
- **Relevant error codes:** `WORKER_FAILED`, `SERVICE_UNAVAILABLE`.
- **Relevant logs:** Worker manager and component-specific worker records.
- **Relevant dashboard pages:** Workers, Detailed health, Security alerts.

## Backup failed

- **Symptoms:** Backup health failed, invalid or stale.
- **Likely causes:** Backup script failure, checksum failure, protected status file missing/invalid or schedule delay.
- **Impact:** Recovery-point objective is not met.
- **Checks:** Status-file ownership/content, backup system logs, checksum and last successful restore test.
- **Safe recovery steps:** Correct the external backup job, create a new encrypted backup, verify checksum and perform the approved restore test; never point tests at production.
- **When to escalate:** No valid backup, checksum mismatch or suspected data loss.
- **Evidence to preserve:** Backup ID/time, checksum result, status file and restore-test record.
- **Relevant error codes:** `STORAGE_UNAVAILABLE`, `SERVICE_UNAVAILABLE`.
- **Relevant logs:** External backup logs and backup health transitions.
- **Relevant dashboard pages:** Dashboard, Detailed health, Security alerts.

## Configuration rollback

- **Symptoms:** Approved update degrades service or cannot reload.
- **Likely causes:** Incorrect allowlisted value or incompatible operational assumption.
- **Impact:** One or more capabilities degrade.
- **Checks:** Configuration history/revision, changed keys, health before/after and restart requirement.
- **Safe recovery steps:** Submit a new revision restoring prior public values with a reason; never edit history or insert secrets; restart only when indicated.
- **When to escalate:** Database/TLS/authentication configuration or rollback conflict.
- **Evidence to preserve:** Old/new/recovery revisions, approvals, health snapshots and audit IDs.
- **Relevant error codes:** `CONFIGURATION_CONFLICT`, `CONFIGURATION_INVALID`.
- **Relevant logs:** Configuration validation/reload and startup records.
- **Relevant dashboard pages:** Configuration history, Detailed health, Audit.

## Emergency administrator recovery

- **Symptoms:** No authorised administrator can access recovery controls.
- **Likely causes:** Account loss, directory outage, role error or session revocation.
- **Impact:** Administrative response is blocked.
- **Checks:** Enabled Administrator/SuperAdministrator counts, directory health, role history and bootstrap history.
- **Safe recovery steps:** Use the locally controlled host and approved change process; restore directory access where possible; use `bluebubbles-create-admin` only when no enabled initial Administrator exists; rotate any exposed credentials afterward.
- **When to escalate:** Always involve the system owner and security owner; database intervention requires the database owner.
- **Evidence to preserve:** Approvals, operator identity, console time, created user ID and resulting audit event.
- **Relevant error codes:** `LAST_SUPERADMIN`, `PERMISSION_DENIED`, `DIRECTORY_UNAVAILABLE`.
- **Relevant logs:** Bootstrap command outcome, authentication, role and audit records.
- **Relevant dashboard pages:** Users, Audit, Security alerts, Detailed health.
