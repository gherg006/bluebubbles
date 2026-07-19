# Developer guide

## Repository and environment

Use Python 3.13, the locked development dependencies, and the repository index as
the navigation source. Do not scan or rewrite unrelated packages. Preserve the
dependency direction presentation -> services -> protocols -> adapters and the
separate domain/ORM/DTO representations.

```powershell
py -3.13 -m venv .venv313
.\.venv313\Scripts\Activate.ps1
python -m pip install -e ".[development]"
python scripts\development\run_quality_checks.py
```

The gate runs Black, Ruff/security rules, secret scanning, strict mypy, pytest,
branch coverage, and the 90% aggregate floor. Focused tests may use `--no-cov`; the
final gate may not. Real PostgreSQL tests require an already migrated dedicated
database in `BLUEBUBBLES_TEST_DATABASE_URL` and intentionally skip otherwise.

## Architectural rules

- Client/GUI never access PostgreSQL. Server never receives plaintext/private keys.
- Routers authenticate/translate; services authorise/coordinate/commit.
- One `UnitOfWorkFactory` call creates a fresh session and full repository bundle.
- Repositories never commit, roll back, close, encrypt, authorise, or emit UI.
- Async task owners retain references, bound shutdown, cancel and await tasks.
- Cryptographic canonicalisation, identifiers and protocol values have one source.
- Migrations are immutable after use; new schema changes receive new revisions.
- Unknown configuration and unsafe production defaults fail startup.

## Change workflow

1. Read the focused architecture note and affected public contracts.
2. Write boundary/negative tests before or with the correction.
3. Implement the smallest complete change without placeholder production paths.
4. Review security after authentication, crypto, path, audit, deployment, secret,
   or offline changes; review migration/compatibility triggers separately.
5. Update generated references:

```powershell
python scripts\documentation\generate_reference.py
```

6. Run the full quality gate and relevant package/release smoke checks.
7. Update the stable defect ID, execution report, acceptance matrix and limitations.

## Testing expectations

Cover minimum, exact maximum, first outside, empty, malformed, duplicate,
unauthorised, stale, expired, tampered, interrupted, retry, rollback and cleanup
states wherever meaningful. Security tests must exercise the production code path.
Never replace PostgreSQL semantics with SQLite or call skipped infrastructure tests
passed. Preserve failed evidence and correct the cause.

## Builds

```powershell
python scripts\deployment\build_release.py --created-by OPERATOR --output dist\server
python scripts\packaging\build_client.py --version 0.1.0 --output dist\client
```

Server archives normalize timestamps/ownership/modes and include a manifest plus
SHA-256 sidecar. Windows publishing requires the complete Inno Setup installer,
checksum, version metadata, uninstaller and signing limitation/signature. A
PyInstaller one-directory smoke artifact alone is not the final installer.

## Current highest-priority defect

`ClientApplication` defaults to `UnavailableUiBackend`; tests inject callbacks but
the packaged application does not compose HTTP/WebSocket, session, cryptographic,
storage, transfer and synchronisation services. Do not weaken the release gate or
replace it with fake success. Close `RC-CLIENT-001` with a real injected production
backend and two-client clean-environment tests.
