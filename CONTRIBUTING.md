# Contributing

Changes must follow the engineering specification and its implementation order.
Do not implement a later stage before its predecessors are complete.

Use Python 3.13 or newer, include type hints and concise docstrings, and keep
responsibilities separated across shared, server, and client packages. Add
tests in the matching path beneath `tests/` and run:

```powershell
python scripts/development/run_quality_checks.py
```

Never commit credentials, private keys, production configuration, databases,
or plaintext user content. Document user-visible changes in `CHANGELOG.md`.
