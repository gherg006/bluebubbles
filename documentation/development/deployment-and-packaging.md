# Deployment and packaging

Task 21 provides one supported Version 1.0 topology: Debian 13 runs one
loopback-only FastAPI process behind Nginx, with local PostgreSQL and Redis plus
separately mounted encrypted attachment storage. Windows clients use a PyInstaller
one-directory build and an Inno Setup installer definition. No client needs Python.

## Security boundary

Nginx is the only ordinary LAN listener and terminates TLS 1.2 or 1.3. FastAPI
listens on `127.0.0.1:8000`; PostgreSQL and Redis remain loopback-only. Production
configuration validation accepts application-level TLS or the supported Nginx
mode. Nginx mode is valid only when the application listener is loopback and the
single trusted proxy is declared. This prevents a production operator from
accidentally exposing plaintext FastAPI traffic.

The systemd service runs as the non-login `bluebubbles` account, requires the
attachment mount, writes only to application data and log locations, and applies
filesystem, device, privilege, kernel, and temporary-directory restrictions.
Secrets are read from protected files listed in the environment template. They do
not enter release archives, manifests, build reports, command lines, or evidence.

## Integrity contracts

`bluebubbles.deployment` owns strict release and backup manifests, streaming
SHA-256 calculation, contained-path validation, and injection-resistant template
substitution. Manifest artifact paths are canonical relative POSIX paths. Absolute
paths, traversal, duplicate artifacts, malformed hashes, control characters,
naive timestamps, and inconsistent successful backups are rejected.

`scripts/deployment/build_release.py` creates a curated archive containing source,
migrations, locked dependency metadata, configuration examples, deployment files,
operations documentation, licensing, and health/backup tooling. Its external
manifest is verified before installation. Generated output remains ignored under
`dist` and is not a source artifact.

## Windows build

`scripts/packaging/build_client.py` requires the authoritative project version,
cleans only a validated output directory below the project, invokes PyInstaller
without a shell, verifies `BlueBubbles.exe`, and writes a checksum and JSON report.
The checked-in spec includes the production client configuration and licence and
disables UPX. The Inno Setup definition installs per machine, creates Start Menu
and optional desktop shortcuts, supports upgrade detection, and deliberately
preserves `%LOCALAPPDATA%\BlueBubbles` profiles on uninstall. Profile deletion is
a separate explicit user action because it removes drafts, queued messages, keys,
and encrypted local state.

An organisational signing certificate was not available during Task 21. Builds
therefore identify `signed: false`, publish SHA-256 evidence, and must not be
described as publisher-authenticated. Administrators must not disable endpoint
security to work around false positives.

## Verification ownership

Automated Task 21 tests cover manifest boundaries, integrity tampering, path
containment, backup-plan overlap, template injection, packaging version drift,
Nginx routes, systemd hardening, installer preservation, and Nginx/FastAPI
configuration compatibility. Debian, firewall, real TLS, clean Windows installer,
backup/restore, upgrade, and rollback acceptance require the isolated environments
and evidence procedure in the operations documentation.
