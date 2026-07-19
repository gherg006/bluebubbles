# Task 21 and 22 defect log

## DEF-DEPLOY-001 — reverse-proxy TLS contract mismatch

- Severity: High deployment/security.
- Reproduction: production validation rejected Nginx TLS termination while the
  authoritative topology required plaintext FastAPI on loopback behind Nginx.
- Cause: predecessor production validation treated all TLS termination as
  application-owned.
- Correction: production accepts disabled application TLS only with loopback host
  and exactly one trusted proxy; production example moved to `127.0.0.1:8000`.
- Regression: server configuration and Task 21 template tests.
- Retest: focused tests and full Task 21 quality gate passed.

## DEF-VALIDATION-001 — control text normalized before rejection

- Severity: Medium input validation/log safety.
- Reproduction: newline/tab controls in display text were converted to spaces by
  `split()` before the control-character check.
- Cause: validation order checked normalized output instead of raw input.
- Correction: reject ASCII controls before whitespace normalization.
- Regression: Hypothesis generates every ASCII control class inside otherwise safe
  display text.
- Retest: property/security suite and full quality gate passed.

## DEF-DEP-001 — known vulnerabilities in locked dependencies

- Severity: Critical release gate.
- Reproduction: the workstation lock audit reported 19 advisory records in Black,
  cryptography, PyNaCl, pytest, and transitive Starlette; the separate exact Debian
  set then identified one advisory in setuptools 80.9.0.
- Cause: dependency pins predated 2026 security fixes.
- Correction: upgraded FastAPI 0.139.1/Starlette 1.3.1, cryptography 49.0.0,
  PyNaCl 1.6.2, Black 26.5.1, pytest 9.1.1, pytest-asyncio 1.4.0, and setuptools
  83.0.0; regenerated the complete lock. Black's new stable formatting changed one
  existing migration expression without behavior change.
- Regression: exact lock-version checks and malformed-host request-path test for
  the Starlette path confusion advisory.
- Retest: dependency compatibility check clean; the final 477-case collection
  passed 474 and skipped only three environment-gated PostgreSQL cases; the final
  workstation-lock and exact Debian-server audits report no known vulnerabilities.

## DEF-PACK-001 - client report path used the wrong reference root

- Severity: Medium packaging/integrity evidence.
- Reproduction: the one-directory client was correctly emitted as
  `BlueBubbles/BlueBubbles.exe`, but its JSON report recorded `BlueBubbles.exe`,
  which did not resolve from the directory containing that report.
- Cause: the integrity record was rooted at the nested bundle instead of the
  published output directory.
- Correction: calculate the artifact record from the report's output root.
- Regression: a simulated build asserts the reported path resolves to the actual
  executable from the published root.
- Retest: focused Task 21 tests passed 32/32; the rebuilt executable remained
  responsive for five seconds and was stopped cleanly.

## DEF-CI-001 - CI package and integration evidence was incomplete

- Severity: Medium release-evidence integrity.
- Reproduction: the initial artifact step uploaded the client checksum/report but
  omitted the executable bundle, while the integration-only pytest job inherited
  the full-suite 90% coverage floor and would fail despite passing its tests.
- Cause: workflow paths and the scoped integration invocation did not distinguish
  package publication from full-suite coverage enforcement.
- Correction: upload the complete client output, retain coverage enforcement in
  the Windows quality job, run the live PostgreSQL subset with `--no-cov`, and add
  the locked dependency audit to CI.
- Regression/retest: YAML parses successfully; local equivalents for the quality,
  package, manifest, smoke, dependency, and no-external-service test steps passed.
  The hosted PostgreSQL service job itself remains pending its first CI run.

## DEF-INSTALL-001 - fresh Debian environment omitted runtime dependencies

- Severity: Critical installation failure.
- Reproduction: the initial installer created an empty virtual environment and
  installed the application with `--no-deps`; it also did not select the supplied
  release as `/opt/bluebubbles/current`.
- Cause: client-bundle dependency exclusion was incorrectly reused for the server
  without a server dependency phase, and the source-layout step was incomplete.
- Correction: add an exact server-only dependency set, make PySide6 Windows-only,
  install/check dependencies before the no-dependency application install, require
  the release to be below the controlled release root, and atomically set `current`.
  Upgrade and rollback now restore each release's matching dependency set.
- Regression: 32 Task 21 tests cover dependency pins/direct-runtime coverage,
  install/upgrade/rollback commands, publication roots, and normalized executable
  archive permissions. CI creates and checks an isolated Linux server environment
  and runs ShellCheck before live PostgreSQL integration.
- Retest: static/local tests pass. The real clean-Debian execution remains `NOT RUN`
  until CI or the specified Debian VM is available, so operational acceptance is
  not overstated.
