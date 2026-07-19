# Task 21 execution report

## Completion boundary

Task 21 adds secure Debian deployment templates and automation, Nginx TLS and
WebSocket proxying, a hardened systemd service and backup timer, restricted storage
and secret-file layouts, release and backup integrity contracts, coordinated backup
implementation, upgrade/rollback controls, a reproducible PyInstaller one-directory
Windows build, an Inno Setup installer definition, and complete operator runbooks.
The Debian release carries an exact server-only dependency set so a fresh virtual
environment is complete without installing the Windows-only GUI runtime.

## Integration decisions

The authoritative Nginx topology exposed a predecessor mismatch: production
validation previously required application-level TLS. It now accepts Nginx
termination only when FastAPI binds to loopback and exactly one trusted proxy is
declared. The production example uses `127.0.0.1:8000`; Nginx alone exposes HTTPS
and WSS. The backup status writer emits the exact `completed_at`, `successful`, and
`checksum_valid` schema consumed by Task 20 monitoring. The systemd unit uses the
implemented CLI, real configuration-directory semantics, real health paths,
`/api/v1/ws`, the actual Alembic configuration, and the implemented administrator
bootstrap command.

## Automated boundary evidence

`test_task_21_deployment.py` covers canonical path minimums and traversal/outside
attempts; SHA-256 length, alphabet and case; zero-byte artifacts; empty and duplicate
sets; positive protocol/configuration limits; safe identifier and control-character
boundaries; timezone awareness and reversed timestamps; successful versus partial
failed backups; warning count/length/line rules; streaming chunks at one byte and
outside the 16 MiB cap; tampering and deletion; non-directory roots; template key
sets, hostname/newline injection; PostgreSQL identifiers; source/output overlap and
missing paths; project-version drift; and static exposure, route, hardening, and
uninstall-preservation rules. Server configuration tests cover both rejected unsafe
production defaults and accepted loopback-only Nginx termination.

## Artifact evidence (2026-07-18)

The source environment was Windows 11 `10.0.26200`, Python 3.13.5, PyInstaller
6.21.0 and its 2026.6 hooks. Strict mypy passed the eleven new deployment/build
files. The server archive was generated and independently verified:

```text
bluebubbles-server-0.1.0.tar.gz
size: 278760 bytes
SHA-256: a8f47d32b1354f1422d4136be70eaa30847109d0e783bf723063a494139f8440
manifest verification: true
two-build byte-for-byte reproducibility: true
```

The Windows one-directory client built successfully. Its executable evidence was:

```text
BlueBubbles/BlueBubbles.exe
size: 7810090 bytes
SHA-256: ec8a77e816ff244d1d02125b45b518af4bccf640edbbe9e124c42e37eb8a544a
signed: false (no organisational signing certificate supplied)
```

The executable was launched with Qt's off-screen platform, remained running for
five seconds, and was then stopped by the test harness. Generated archives and
binaries remain ignored build output; their reports can be reproduced from source.

## Environment-bound acceptance

Automated evidence cannot honestly substitute for a clean Debian 13 VM, real
systemd/Nginx/PostgreSQL/Redis/TLS/firewall exposure, clean Windows 10/11 installer
VMs, an Inno Setup compiler, or a separate backup-restore host. The exact manual
scripts, expected results, evidence fields, destructive warnings, and acceptance
gate are documented in `documentation/operations`. These items must be recorded in
the Task 22 acceptance matrix and remain explicit rather than being claimed from
the development workstation.
