# BlueBubbles

BlueBubbles is an offline-capable, client-server desktop messaging platform for
local-area networks. The project is being built incrementally from the Version
1.0 engineering specification, with strict separation between shared protocol
contracts, server code, and the PySide6 desktop client.

This repository currently contains the verified foundation, shared protocol
contracts, strict client/server configuration, domain entities, typed error and
recovery primitives, and the complete versioned PostgreSQL schema. Repository
services, authentication infrastructure, and private-key operations are added in
later specification stages. See [domain models and error handling](documentation/development/domain-models-and-errors.md)
for the server/client plaintext boundary and error compatibility rules, and
[database schema and migrations](documentation/development/database-schema-and-migrations.md)
for the persistence contract and controlled upgrade process.

## Requirements

- Python 3.13 or newer
- Windows 11 for the desktop client
- Debian 13 for the production server

PostgreSQL is required to apply or exercise the server schema. Redis becomes
necessary when its runtime infrastructure stage is introduced. Server lifecycle
ownership does not connect to either service yet.

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

## Running the applications

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
`ws://127.0.0.1:8443/ws`, with `application.environment: development`.

The Debian server and Windows client have separate settings models, loaders,
configuration files, and environment-variable namespaces. See
[configuration and deployment](documentation/development/configuration.md) for
source precedence, protected secret files, TLS guidance, and production setup.

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
