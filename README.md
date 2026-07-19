# BlueBubbles

BlueBubbles is an offline-capable, client-server desktop messaging platform for
local-area networks. The project is being built incrementally from the Version
1.0 engineering specification, with strict separation between shared protocol
contracts, server code, and the PySide6 desktop client.

The documented implementation now covers Tasks 1-23: shared contracts, encrypted messaging
and attachments, PostgreSQL persistence, Redis-backed delivery, offline client
storage and synchronisation, the PySide6 interface, administration/monitoring,
Debian deployment, Windows packaging, and automated full-system test evidence.
Live infrastructure, usability, accessibility, and clean-machine acceptance items
that have not run are explicitly retained in the
[acceptance matrix](documentation/testing/acceptance-matrix.md). **No release
candidate has been issued:** the production client backend, final Windows installer,
and clean-environment acceptance remain blocked as recorded in the
[release status](documentation/release/release-candidate-status.md). Start with the
[complete startup guide](documentation/guides/complete-startup-guide.md), the
[repository index](documentation/INDEX.md), and the
[testing strategy](documentation/testing/testing-strategy.md).

## Requirements

- Python 3.13 or newer
- Windows 11 for the desktop client
- Debian 13 for the production server

PostgreSQL is the authoritative server store. Redis supports revocation,
rate-limiting, cache, and cross-process event delivery; documented degraded modes
do not make it a persistence substitute. LDAP is required only when that
authentication provider is selected.

## Development setup

Create and activate a virtual environment, then install the project with its
development tools:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[development]"
```

Run the complete foundation check:

```powershell
python scripts/development/run_quality_checks.py
```

The equivalent individual commands are:

```powershell
python -m black --check src tests scripts migrations
python -m ruff check src tests scripts migrations
python -m mypy src tests scripts migrations
python -m pytest
```

Render the initial PostgreSQL migration without changing a database, or apply it
with migration credentials after configuring the protected database URL:

```powershell
alembic upgrade head --sql
alembic upgrade head
```

## Running the development applications

Validate and start the development server:

```powershell
python -m bluebubbles.server.main validate-config
python -m bluebubbles.server.main
```

The development server listens on loopback at `http://127.0.0.1:8443`. Start
the independently configured Windows desktop client in a second terminal:

```powershell
python -m bluebubbles.client.main
```

The checked-in client configuration targets the eventual encrypted LAN endpoint
`https://192.168.0.210:8443`. For local development, copy the client YAML and
set its HTTP/WebSocket endpoints to `http://127.0.0.1:8443` and
`ws://127.0.0.1:8443/api/v1/ws`, with
`application.environment: development`.

The current packaged/default client deliberately uses an unavailable presentation
backend because its production HTTP/WebSocket/storage/cryptography composition has
not been implemented. The window can be exercised, but server-backed login and
messaging cannot yet succeed. Do not treat a UI smoke run as end-to-end acceptance.

The Debian server and Windows client have separate settings models, loaders,
configuration files, and environment-variable namespaces. See
[configuration](documentation/development/configuration.md) for source precedence
and protected secrets, and
[deployment and installation](documentation/operations/deployment-and-installation.md)
for the production topology.

## Dependency management

`pyproject.toml` is authoritative for direct dependencies and tool settings.
`pylock.toml` locks the resolved dependency graph for repeatable Windows
development installations. Regenerate it on Python 3.13 after changing a
dependency:

```powershell
python -m pip lock --output pylock.toml ".[development]"
```

Do not commit secrets, local configuration, virtual environments, databases,
or generated build output.
