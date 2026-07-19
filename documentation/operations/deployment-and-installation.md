# Debian server deployment and Windows client installation

This is the supported BlueBubbles Version 1.0 installation procedure. Commands
labelled with angle-bracket values are examples until every value is replaced.
Never paste an angle-bracket placeholder into production. Use a clean Debian 13
host, a static address or DHCP reservation, internal DNS, an approved UTC-capable
time source, and a hostname present in the TLS certificate SAN.

## Server preparation

Minimum practical sizing is 4 CPU cores, 8 GiB RAM, SSD-backed operating system
and PostgreSQL storage, and capacity-planned attachment and backup volumes. Use
separate storage for attachments and durable backups where possible. Backups on
the application server alone are staging, not disaster recovery.

Install the tested prerequisites:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential libpq-dev \
  postgresql postgresql-client redis-server nginx openssl ca-certificates curl \
  ufw
```

Confirm Python is 3.13 or newer without replacing Debian's system Python:

```bash
python3 --version
sudo scripts/deployment/install_server.sh --check
```

Build the server release on a controlled build host, transfer the archive and
manifest through an approved LAN channel, and verify them before extraction:

```bash
python scripts/deployment/build_release.py --created-by <operator-id>
python scripts/deployment/verify_release.py \
  <manifest-path> --artifact-root <archive-directory>
```

After independently comparing the trusted manifest checksum, extract into a new
version directory and run the idempotent base installer:

```bash
sudo scripts/deployment/install_server.sh --apply \
  --release-root /opt/bluebubbles/releases/<version>
```

The installer never invents production secrets and does not start an unconfigured
service. It installs the exact server-only versions in
`deployment/server-requirements.txt`, installs the application without the
Windows-only PySide6 dependency, runs `pip check`, and atomically selects the
release through `/opt/bluebubbles/current`. Dependency acquisition requires the
approved Python package index unless the organisation mirrors these exact packages.

## PostgreSQL and Redis

Create a random database password outside shell history. Create application,
migration, and backup roles according to local policy; the minimal application
database is UTF-8 and owned by `bluebubbles_app`. Restrict PostgreSQL to loopback
with SCRAM-SHA-256 in `pg_hba.conf`. Restrict Redis to `127.0.0.1 ::1`, protected
mode, and a dedicated ACL/password. Neither port 5432 nor 6379 may be reachable
from a client VLAN.

Write full protected connection URLs to:

```text
/etc/bluebubbles/secrets/database_url
/etc/bluebubbles/secrets/redis_url
```

Use owner `root:bluebubbles`, mode `0640`. Store the LDAP bind password and a
random 64-byte token secret in the corresponding files named by
`deployment/templates/environment`. Never put their values in YAML.

## Configuration, storage, and migration

Copy `config/server/base.yaml` and a completed production file to
`/etc/bluebubbles/base.yaml` and `/etc/bluebubbles/production.yaml`. Use
`config/server/production.example.yaml` only as a starting point. Keep FastAPI on
`127.0.0.1:8000`, set one trusted proxy, keep application TLS disabled because
Nginx terminates it, configure LDAPS with certificate validation, use the exact
mounted attachment paths, and set `monitoring.backup_status_path` to
`/var/lib/bluebubbles/state/backup-status.json`.

Mount attachment storage persistently before startup. Verify the intended volume,
capacity, ownership, and write access; a missing mount must block the service:

```bash
findmnt /var/lib/bluebubbles/attachments
df -h /var/lib/bluebubbles/attachments
sudo -u bluebubbles test -w /var/lib/bluebubbles/attachments
```

Validate configuration before migration:

```bash
sudo -u bluebubbles /opt/bluebubbles/shared/venv/bin/bluebubbles-server \
  validate-config --environment production --config-directory /etc/bluebubbles
```

Create and verify a backup before every production migration, then apply migrations
with the migration role:

```bash
sudo -u bluebubbles /opt/bluebubbles/shared/venv/bin/alembic \
  -c /opt/bluebubbles/current/alembic.ini upgrade head
sudo -u bluebubbles /opt/bluebubbles/shared/venv/bin/alembic \
  -c /opt/bluebubbles/current/alembic.ini current
```

Create the initial administrator with `bluebubbles-create-admin`; it prompts for a
password, hashes it with Argon2id, refuses duplicates, and records the bootstrap
event. Prefer at least two tested directory-backed SuperAdministrators, then
disable or tightly protect the local bootstrap account.

## Nginx, TLS, systemd, and firewall

Render `deployment/templates/bluebubbles.nginx.conf.template` with the stable
hostname only. Install it as `/etc/nginx/sites-available/bluebubbles`, link it into
`sites-enabled`, install the organisation-issued certificate and chain, and keep
the private key `root:root` mode `0600`.

```bash
sudo nginx -t
sudo systemctl reload nginx
openssl s_client -connect <hostname>:443 -servername <hostname>
```

Install the checked-in service and backup units, reload systemd, then inspect the
hardening result before enabling them:

```bash
sudo systemctl daemon-reload
sudo systemd-analyze security bluebubbles.service
sudo systemctl enable --now bluebubbles.service bluebubbles-backup.timer
sudo systemctl status bluebubbles.service
sudo journalctl -u bluebubbles.service --since today
```

Apply a reviewed firewall policy after replacing both subnet placeholders. Permit
443 from approved client networks and 22 only from management networks. Port 80 is
optional for redirect. From a separate client host, verify 5432, 6379, and 8000 are
closed and no unexpected service is exposed.

## Acceptance check

Deployment is incomplete until all of these pass and evidence is retained:

```text
Hostname and certificate validate; TLS 1.0/1.1 fail.
Liveness and readiness succeed through Nginx.
FastAPI, PostgreSQL, and Redis are unreachable directly from the LAN.
Service runs as bluebubbles, starts on boot, stops cleanly, and restarts on failure.
Attachment mount guard, permissions, low-space warning, and full-volume rejection work.
Migrations are current; audit chain verifies; workers and outbox are healthy.
Administrator and two synthetic users authenticate.
Encrypted direct and group messages round-trip; no server plaintext marker appears.
Encrypted attachment upload/download verifies its checksum.
Session revocation and logout invalidate tokens.
Coordinated backup and clean-environment restore pass.
```

## Windows client

Build on a clean supported Windows host from the lock file:

```powershell
python scripts\packaging\build_client.py --version <project-version> \
  --output dist\client --inno-compiler "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

Compare the published SHA-256 before installing. Test the installer on clean
Windows 10 and Windows 11 without Python: install, launch from Start Menu, create a
synthetic profile, connect with valid TLS, restart, upgrade, confirm drafts/settings/
offline queue/credentials survive, uninstall, and verify application binaries are
removed while profile data is preserved by default. Test explicit profile deletion
separately with disposable data. An unsigned NEA build will display Windows
publisher warnings and must not be presented as code-signed.
