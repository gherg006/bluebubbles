# Version 1.0 testing strategy

BlueBubbles uses static, unit, component, integration, security, property,
deployment, packaging, performance, and manual acceptance layers. A passing unit
suite is not treated as proof of a clean deployment or complete user journey.

## Environments and commands

The fast deterministic set requires Python 3.13 and no external services:

```powershell
python -m pytest tests/unit tests/security
```

The repository quality gate runs Black, Ruff security and correctness rules, the
high-confidence secret scan, strict mypy, every default test, and branch-aware
coverage with a 90% minimum:

```powershell
python scripts/development/run_quality_checks.py
```

Real PostgreSQL tests require a dedicated migrated database named only by
`BLUEBUBBLES_TEST_DATABASE_URL`. They intentionally skip without it. Never point
the variable at an administrator or production database. Redis and LDAP acceptance
require disposable controlled services. Deployment, firewall, TLS, Windows
installer, upgrade, rollback, and restore tests require the isolated environments
defined in the operations guides.

Release-only checks are:

```powershell
python -m pip_audit --locked .
python scripts/testing/measure_performance.py --output <evidence-file>
python scripts/deployment/build_release.py --created-by <operator>
python scripts/packaging/build_client.py --output dist\client
```

The dependency audit requires advisory-database network access. Application runtime
does not. Generated archives, executables, caches, local databases, and credentials
are not source files.

The final 2026-07-18 workstation run checked 350 typed source files and collected
477 tests: 474 passed, the three real-PostgreSQL tests skipped because no dedicated
database URL was supplied, and aggregate line-plus-branch coverage was 90.16%.
Those skips are carried into the acceptance matrix as incomplete live evidence.

## Isolation and fixtures

Unit tests use function-scoped fakes, deterministic clocks/UUIDs, in-memory event
publishers, temporary directories, temporary encrypted SQLite profiles, mock LDAP
adapters, controlled key pairs, and explicit API/container replacements. Async
tests use strict event-loop mode, await owned tasks, cancel workers during cleanup,
and use events or bounded retries rather than arbitrary long sleeps. PostgreSQL
adapters are never replaced with SQLite.

Every test uses synthetic people, accounts, departments, messages, attachments,
reasons, keys, and credentials. Marker strings used to detect plaintext exposure
are synthetic and must never contain real personal or production data. Evidence may
record hashes and safe identifiers but not passwords, tokens, private keys, private
paths, bind credentials, or message/attachment plaintext.

## Boundary and generated-input policy

Task 22 dynamically enumerates every Pydantic field constraint in server and client
settings. The resulting 117 cases validate the accepted exact edge and the first
rejected value outside it for ports, counts, sizes, timeouts, page limits, group
limits, cache/storage thresholds, retry limits, worker schedules, percentages,
protocol values, and minimum string lengths. Model-level relationships are tested
separately, including warning/critical ordering, default/maximum page and cache
ordering, TLS pairs, production proxy safety, chunk ranges, retention order,
directory requirements, retry caps, protocol membership, and certificate pins.

Hypothesis generates valid and invalid Base64 sizes, filenames and Unicode/control
text, canonical mappings in different insertion orders, opaque cursor values,
fingerprints, chunk indices, and release paths. Each accepted filename/path is
checked for containment and each decoded/canonical value for round-trip equality.

Subsystem tests cover minimum, exact maximum, first out-of-bounds, malformed,
missing, duplicate, unauthorized, stale-version, expired-time, tampered, interrupted,
retry, rollback, and cleanup behavior wherever the public contract exposes those
states. The requirement/acceptance matrix links every mandatory category to its
executable or manual method.

## Static and security controls

Ruff's `S` rules cover insecure random use, unsafe subprocesses, hard-coded secret
patterns, temporary files, deserialization, and broad suppression. The dedicated
scanner covers private-key headers, JWT-shaped tokens, and non-placeholder database
credentials without echoing matched secrets. Architecture tests prohibit shared to
client/server, server to client, domain to transport/ORM, view-model to views, and
router to ORM dependency inversions.

`pip-audit` checks the resolved lock against current Python advisories. A clean
result is time-bound evidence and must be regenerated before release. Manual crypto
review still checks for ECB, unauthenticated encryption, nonce reuse patterns,
static keys, private-key upload, signature/tag bypass, insecure randomness, and
algorithm fallback.

## Coverage and failure policy

Coverage is line plus branch coverage. Exclusions are limited to executable main
wrappers and the standard `if __name__ == "__main__"` branch. Reports identify
untested files and branches; 90% aggregate is the floor, not a reason to ignore a
security-critical branch.

Failures remain in the defect log with stable `DEF-<SUBSYSTEM>-<NUMBER>` IDs,
severity, reproduction, cause, correction, regression test, and retest. Rerunning a
flaky case until it passes is not evidence. An infrastructure skip is recorded as
`NOT RUN`, never `PASS`.

## Known untested areas

The current workstation cannot provide Debian/systemd/Nginx/firewall exposure, a
real PostgreSQL/Redis/LDAP stack, clean Windows 10/11 installer VMs, Inno Setup,
LAN impairment, multi-user usability participants, screen-reader evaluation, or a
separate clean restore host. Full 2 GiB attachment, 100-user live group, 100,000
message database, soak/load, crash-at-process-instruction, and production-like LAN
latency tests are also not run here. Hardware-backed keys, multi-device behavior,
public Internet deployment, clustering, and automatic updates are outside Version
1.0 scope. These limitations block release acceptance but do not hide automated
component results.
