# BlueBubbles

BlueBubbles is an offline-capable, client-server desktop messaging platform for
local-area networks. The project is being built incrementally from the Version
1.0 engineering specification, with strict separation between shared protocol
contracts, server code, and the PySide6 desktop client.

This repository currently contains the verified repository-and-tooling
foundation and the shared client/server protocol contracts. Messaging services,
authentication infrastructure, persistence, and private-key operations are
added in later specification stages.

## Requirements

- Python 3.13 or newer
- Windows 11 for the desktop client
- Debian 13 for the production server

PostgreSQL and Redis become necessary when their corresponding implementation
stages are introduced. The repository-and-tooling stage does not connect to
external services.

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
python -m black --check src tests scripts
python -m ruff check src tests scripts
python -m mypy src tests scripts
python -m pytest
```

## Running the applications

Start the development server:

```powershell
python -m bluebubbles.server.main
```

The server listens on loopback by default at `http://127.0.0.1:8000`. Start the
desktop client in a second terminal:

```powershell
python -m bluebubbles.client.main
```

These entry points intentionally expose only the minimal runtime foundation.
The shared contracts do not alter application startup; later specification
stages add configuration, lifecycle management, health checks, and user
workflows.

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
