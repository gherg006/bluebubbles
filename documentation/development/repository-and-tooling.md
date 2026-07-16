# Repository and tooling

Task 01 establishes the project boundary without implementing later product
features. Production Python code lives under `src/bluebubbles`, separated into
the independent `shared` package and the server and client packages. Tests
mirror these paths under `tests/unit`, while cross-package startup checks live
under `tests/integration`.

The version in `pyproject.toml` is authoritative. The runtime version module
uses installed distribution metadata and reads the same project value only
when executing directly from a source checkout.

Both entry points are intentionally minimal but real: the FastAPI factory
serves application identity on `/`, and the PySide6 factory constructs a Qt
application with a visible foundation window. Neither entry point accesses a
database, network service, credential, or cryptographic key at this stage.

Application code uses the `bluebubbles` logger configured by
`configure_logging`. Each record is emitted as one JSON object. Components
receive or create child loggers rather than relying on mutable business state
stored globally.

Run `python scripts/development/run_quality_checks.py` after every change. It
enforces Black formatting, Ruff lint rules, strict mypy checks, unit tests,
integration tests, branch coverage, and the configured 90 percent minimum.
