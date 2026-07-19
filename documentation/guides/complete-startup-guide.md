# Complete startup guide: Debian Trixie server and Windows client

This is the single start-to-finish operating procedure for BlueBubbles 0.1.0.
Follow it in order. Commands labelled **Debian** run on the server; commands
labelled **Windows PowerShell** run on the administrator's Windows workstation.
Use synthetic accounts until release acceptance is complete.

> **Release blocker:** the current packaged client starts, but its default runtime
> backend is `UnavailableUiBackend`. It cannot authenticate or exchange messages.
> This is tracked as `RC-CLIENT-001`.
> Complete the infrastructure rehearsal below only in an isolated test network and
> do not deploy to users until `documentation/release/release-candidate-status.md`
> records that blocker as closed and a clean two-client smoke test passes.

## 1. Record the deployment values

Choose and record these before typing commands. Do not use the example values as
real credentials.

| Name | Example | Rule |
|---|---|---|
| `SERVER_FQDN` | `chat.internal.example` | DNS name in the TLS certificate SAN |
| `SERVER_IP` | `192.168.10.20` | Static address or DHCP reservation |
| `CLIENT_SUBNET` | `192.168.10.0/24` | Only approved client network |
| `MANAGEMENT_SUBNET` | `192.168.50.0/24` | Only approved SSH administrators |
| release version | `0.1.0` | Must match the manifest and application |
| PostgreSQL database | `bluebubbles` | Dedicated, never an administrator database |

Generate separate random passwords for the migration, runtime, backup, Redis, LDAP
bind, and token-signing identities. Store them in the organisation's password
manager. Never put them in shell history, YAML, screenshots, Git, or this guide.

## 2. Prepare Debian 13 Trixie

Install a minimal supported Debian 13 Trixie amd64 host from verified official
media. Configure its hostname, fixed network identity, DNS, UTC-capable time sync,
security updates, persistent attachment storage, and a separate durable backup
destination. The official starting points are the
[Debian Trixie release page](https://www.debian.org/releases/trixie/) and
[amd64 installation guide](https://www.debian.org/releases/trixie/amd64/).

**Debian:**

```sh
sudo apt update
sudo apt full-upgrade --yes
sudo apt install --yes python3 python3-venv python3-pip build-essential libpq-dev \
  postgresql postgresql-client redis-server nginx openssl ca-certificates curl \
  ufw
python3 --version
timedatectl status
```

Python must report 3.13 or newer. Reboot if the kernel or core libraries changed,
then repeat `timedatectl status` and confirm DNS resolves `SERVER_FQDN` to
`SERVER_IP` from both the server and a client VLAN machine.

## 3. Build and transfer the server release

On the controlled source workstation, from the repository root:

**Windows PowerShell:**

```powershell
.\.venv313\Scripts\python.exe scripts\development\run_quality_checks.py
.\.venv313\Scripts\python.exe scripts\deployment\build_release.py `
  --created-by RELEASE_OPERATOR --output dist\server-final
```

Transfer the `.tar.gz`, `.tar.gz.sha256`, and `.manifest.json` files through an
approved channel. Independently compare the manifest checksum with the build-host
record. On Debian, place the three files in an empty staging directory and run:

**Debian:**

```sh
cd /var/tmp/bluebubbles-release
sha256sum --check bluebubbles-server-0.1.0.tar.gz.sha256
sudo install -d -o root -g root -m 0750 /opt/bluebubbles/releases/0.1.0
sudo tar --extract --gzip --file bluebubbles-server-0.1.0.tar.gz \
  --directory /opt/bluebubbles/releases/0.1.0 --strip-components=1 \
  --no-same-owner
```

Stop if the checksum does not say `OK`, the version differs, extraction reports an
error, or the directory already contains an unrelated release.

## 4. Run the controlled installer

**Debian:**

```sh
sudo sh /opt/bluebubbles/releases/0.1.0/scripts/deployment/install_server.sh --check
sudo sh /opt/bluebubbles/releases/0.1.0/scripts/deployment/install_server.sh \
  --apply --release-root /opt/bluebubbles/releases/0.1.0
readlink -f /opt/bluebubbles/current
sudo -u bluebubbles /opt/bluebubbles/shared/venv/bin/python -m pip check
```

The symlink must resolve to the `0.1.0` directory and the dependency check must say
there are no broken requirements. The installer deliberately does not start an
unconfigured service.

## 5. Create PostgreSQL identities and database

Open an interactive PostgreSQL administration session so passwords do not appear
in command history:

**Debian:**

```sh
sudo -u postgres psql
```

At the `psql` prompt:

```sql
CREATE ROLE bluebubbles_migration LOGIN;
CREATE ROLE bluebubbles_app LOGIN;
CREATE ROLE bluebubbles_backup LOGIN;
\password bluebubbles_migration
\password bluebubbles_app
\password bluebubbles_backup
CREATE DATABASE bluebubbles OWNER bluebubbles_migration ENCODING 'UTF8';
\connect bluebubbles
REVOKE ALL ON DATABASE bluebubbles FROM PUBLIC;
GRANT CONNECT ON DATABASE bluebubbles TO bluebubbles_app, bluebubbles_backup;
\quit
```

Create `/etc/bluebubbles/secrets/migration_database_url` interactively with the
migration URL and `/etc/bluebubbles/secrets/database_url` with the runtime URL.
Both use the `postgresql+asyncpg` scheme. Use `sudoedit`, not command-line echo:

```sh
sudo install -o root -g bluebubbles -m 0640 /dev/null \
  /etc/bluebubbles/secrets/migration_database_url
sudo install -o root -g bluebubbles -m 0640 /dev/null \
  /etc/bluebubbles/secrets/database_url
sudoedit /etc/bluebubbles/secrets/migration_database_url
sudoedit /etc/bluebubbles/secrets/database_url
```

Create the PostgreSQL password file used only by the root-owned backup unit. Its
single line is
`127.0.0.1:5432:bluebubbles:bluebubbles_backup:REPLACE_PASSWORD`:

```sh
sudo install -o root -g root -m 0600 /dev/null \
  /etc/bluebubbles/secrets/backup.pgpass
sudoedit /etc/bluebubbles/secrets/backup.pgpass
```

Apply migrations using only the migration secret:

```sh
sudo -u bluebubbles env \
  BLUEBUBBLES_DATABASE_URL_FILE=/etc/bluebubbles/secrets/migration_database_url \
  /opt/bluebubbles/shared/venv/bin/alembic \
  -c /opt/bluebubbles/current/alembic.ini upgrade head
```

Return to `sudo -u postgres psql bluebubbles` and grant runtime/backup privileges:

```sql
GRANT USAGE ON SCHEMA public TO bluebubbles_app, bluebubbles_backup;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bluebubbles_app;
REVOKE UPDATE, DELETE, TRUNCATE ON audit_events FROM bluebubbles_app;
GRANT SELECT, INSERT ON audit_events TO bluebubbles_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bluebubbles_app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bluebubbles_backup;
ALTER DEFAULT PRIVILEGES FOR ROLE bluebubbles_migration IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO bluebubbles_app;
ALTER DEFAULT PRIVILEGES FOR ROLE bluebubbles_migration IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO bluebubbles_app;
ALTER DEFAULT PRIVILEGES FOR ROLE bluebubbles_migration IN SCHEMA public
  GRANT SELECT ON TABLES TO bluebubbles_backup;
\quit
```

After every future migration, explicitly recheck `audit_events` privileges; default
table privileges do not replace the audit restriction.

## 6. Configure Redis

Bind Redis only to loopback, keep protected mode enabled, and create a dedicated
ACL user whose key pattern is `~bluebubbles:*`. Use Redis' protected ACL-file
procedure or the organisation's approved secret manager; do not place its password
on a command line. Restart Redis, then create this protected URL file with
`sudoedit`:

```sh
sudo install -o root -g bluebubbles -m 0640 /dev/null \
  /etc/bluebubbles/secrets/redis_url
sudoedit /etc/bluebubbles/secrets/redis_url
sudo systemctl restart redis-server
sudo ss -ltnp | grep 6379
```

The URL format is `redis://bluebubbles:REPLACE_PASSWORD@127.0.0.1:6379/0`.
The socket inspection must show loopback only.

## 7. Configure application secrets and YAML

Generate at least 64 random token bytes directly into the protected file:

```sh
sudo sh -c 'umask 007; openssl rand -base64 64 > /etc/bluebubbles/secrets/token_signing_key'
sudo chown root:bluebubbles /etc/bluebubbles/secrets/token_signing_key
sudo chmod 0640 /etc/bluebubbles/secrets/token_signing_key
```

If Active Directory is enabled, create the LDAP bind-password file in the same way
with `sudoedit`, then uncomment its variable in `/etc/bluebubbles/environment`.
When directory authentication is disabled, leave that line commented so startup
does not require an unused secret. Copy and edit the YAML files:

```sh
sudo install -o root -g bluebubbles -m 0640 \
  /opt/bluebubbles/current/config/server/base.yaml /etc/bluebubbles/base.yaml
sudo install -o root -g bluebubbles -m 0640 \
  /opt/bluebubbles/current/config/server/production.example.yaml \
  /etc/bluebubbles/production.yaml
sudoedit /etc/bluebubbles/production.yaml
```

Replace every example hostname, DN, UUID, and path. Keep FastAPI at
`127.0.0.1:8000`, `trusted_proxy_count: 1`, application TLS disabled, Nginx as the
TLS owner, and all secrets in files. For local-account rehearsal set the directory
provider to disabled and authentication provider to local; production policy may
instead require LDAPS/Active Directory. Validate without displaying secrets:

```sh
sudo -u bluebubbles /opt/bluebubbles/shared/venv/bin/bluebubbles-server \
  validate-config --environment production --config-directory /etc/bluebubbles
```

Do not continue until it prints `Server configuration is valid.`

## 8. Install TLS and Nginx

Install the organisation-issued certificate chain and private key at the paths used
by the checked-in Nginx template. The key must remain `root:root` mode `0600`.
Render the hostname with the safe renderer; it preserves Nginx variables such as
`$host` and refuses to overwrite an existing file:

```sh
sudo install -d -o root -g root -m 0755 /etc/ssl/bluebubbles
sudo install -o root -g root -m 0644 FULLCHAIN_SOURCE \
  /etc/ssl/bluebubbles/fullchain.pem
sudo install -o root -g root -m 0600 PRIVATE_KEY_SOURCE \
  /etc/ssl/bluebubbles/private.key
sudo -u bluebubbles /opt/bluebubbles/shared/venv/bin/python \
  /opt/bluebubbles/current/scripts/deployment/render_nginx.py \
  --template /opt/bluebubbles/current/deployment/templates/bluebubbles.nginx.conf.template \
  --output /var/tmp/bluebubbles.nginx.conf --hostname SERVER_FQDN
sudo install -o root -g root -m 0644 /var/tmp/bluebubbles.nginx.conf \
  /etc/nginx/sites-available/bluebubbles
sudo ln -s /etc/nginx/sites-available/bluebubbles \
  /etc/nginx/sites-enabled/bluebubbles
sudo nginx -t
sudo systemctl reload nginx
```

Replace the literal `SERVER_FQDN`, `FULLCHAIN_SOURCE`, and `PRIVATE_KEY_SOURCE`
before running. Remove the default Nginx site only after the BlueBubbles test passes.

## 9. Apply the firewall

Do not enable a firewall rule until the management subnet is correct, or SSH access
may be lost:

```sh
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from MANAGEMENT_SUBNET to any port 22 proto tcp
sudo ufw allow from CLIENT_SUBNET to any port 443 proto tcp
sudo ufw allow from CLIENT_SUBNET to any port 80 proto tcp
sudo ufw enable
sudo ufw status numbered
```

From a separate client host, confirm 443 is open and 5432, 6379, and 8000 are
closed. Never infer this from the server's own loopback tests.

## 10. Start the server

Confirm the attachment path is the intended persistent mount before systemd starts:

```sh
findmnt /var/lib/bluebubbles/attachments
sudo -u bluebubbles test -w /var/lib/bluebubbles/attachments
sudo systemctl daemon-reload
sudo systemctl enable --now bluebubbles.service bluebubbles-backup.timer
sudo systemctl status bluebubbles.service --no-pager
curl --fail --silent https://SERVER_FQDN/health/live
curl --fail --silent https://SERVER_FQDN/health/ready
```

Readiness must return a healthy JSON response through Nginx. If not, inspect only
redacted operational logs with `journalctl -u bluebubbles.service --since today`.

## 11. Create the first administrator

The bootstrap command prompts for a password and does not accept it as an argument:

```sh
sudo -u bluebubbles /opt/bluebubbles/shared/venv/bin/bluebubbles-create-admin
```

Create and test a second SuperAdministrator before relying on directory-only
administration. Record the bootstrap audit event without recording the password.

## 12. Prepare the Windows client configuration

Do not use the default example address. As an administrator, create
`C:\ProgramData\BlueBubbles\client.yaml` from
`config\client\managed.example.yaml`. Set the exact HTTPS/WSS hostname and install
the internal CA certificate. The loader automatically uses this managed file when
present; `BLUEBUBBLES_CLIENT_CONFIG_FILE` can select another absolute file.

Minimum production file:

```yaml
application:
  environment: production
server:
  base_url: https://SERVER_FQDN
  websocket_url: wss://SERVER_FQDN/api/v1/ws
tls:
  verify_certificates: true
  trusted_ca_path: C:\ProgramData\BlueBubbles\internal-ca.crt
  expected_hostname: SERVER_FQDN
```

Grant ordinary users read-only access and administrators modification access to
the `BlueBubbles` ProgramData directory. Never place a client private key there.

## 13. Install and start the Windows client

Only use the versioned Inno Setup installer after its checksum and signature policy
have been checked. The current workspace has only a one-directory smoke artifact,
not an accepted installer. When an accepted installer exists:

1. Verify its SHA-256 against the trusted release record.
2. Run the installer as an administrator.
3. Confirm BlueBubbles appears in Installed Apps and has an uninstaller.
4. Start BlueBubbles from the Start menu.
5. Confirm the login window shows `https://SERVER_FQDN`.
6. Confirm Windows trusts the server certificate without bypassing validation.

The current build will then show the known backend-unavailable error on login. That
is a release blocker, not a configuration problem.

## 14. Required end-to-end acceptance after the blocker is fixed

Use the exact 20-step smoke sequence in
`documentation/release/release-candidate-checklist.md`: two ordinary users,
administrator login, direct/group encrypted messages, read/edit/delete, attachment,
offline queue, revocation, audit verification, restart, and persistence. Then
perform plaintext, network, permission, key, session, audit, offline, attachment,
UI, backup/restore, upgrade, and rollback inspections. A successful startup alone
is not release acceptance.

## Troubleshooting stop conditions

| Symptom | Check | Do not do |
|---|---|---|
| configuration invalid | exact field in safe validation error; file ownership/mode | print secret files |
| readiness 503 | PostgreSQL, Redis, storage mount, migration head | expose internal ports |
| TLS warning | DNS, SAN, chain, client clock, CA file | disable verification |
| database permission error | migration head and runtime grants | grant superuser |
| Redis unavailable | loopback listener, ACL, protected URL file | bind Redis to LAN |
| client cannot log in | current release blocker status first | treat component tests as E2E proof |
| attachment mount absent | stop service and restore the correct mount | let systemd write to root disk |
| upgrade failure | keep previous release selected; follow rollback runbook | downgrade schema blindly |

For recovery procedures use
`documentation/operations/backup-restore-upgrade.md`; for incident response use
`documentation/operations/administration-runbooks.md`.
