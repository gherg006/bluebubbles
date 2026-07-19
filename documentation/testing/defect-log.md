# Release defect log

## RC-CLIENT-001 - packaged client has no production backend

- Severity: Critical release blocker.
- Reproduction: construct the client through `bluebubbles.client.main`; the
  application supplies `UnavailableUiBackend` when tests have not injected a
  backend, so login and every server-backed workflow fail by design.
- Cause: Task 18 completed the presentation boundary, but no later stage composed
  HTTP, WebSocket, local storage, key management, and offline services into a
  production `UiBackend`.
- Required correction: implement that composition without weakening TLS,
  cryptographic, storage, or dependency-direction boundaries; then run the real
  two-client journeys.
- Status: OPEN. Version 0.1.0 is not eligible for release-candidate promotion.

## RC-INSTALLER-001 - Windows Setup executable is unavailable

- Severity: Critical release blocker.
- Reproduction: the PyInstaller one-directory bundle exists, but no Inno Setup
  compiler or signed/versioned Setup executable is present in this environment.
- Required correction: build and smoke-test the installer on clean Windows 11,
  verify install/uninstall and managed configuration, and retain its checksum.
- Status: OPEN.

## DEF-DEPLOY-002 - Nginx renderer consumed native variables

- Severity: Critical deployment startup failure.
- Reproduction: rendering the hostname through Python's generic template engine
  also interpreted Nginx variables such as `$host`, `$request_uri`, and
  `$http_upgrade` as application placeholders.
- Correction: deployment templates now substitute only braced application
  placeholders; the dedicated renderer validates hostnames and refuses overwrite.
- Regression/retest: Task 21 tests preserve native Nginx variables and exercise
  invalid hostnames and overwrite refusal.

## DEF-CONFIG-001 - service-readable secret permissions were rejected

- Severity: Critical deployment startup failure.
- Reproduction: installation correctly creates root-owned secret files readable by
  the `bluebubbles` service group (`0640`), while configuration validation accepted
  only owner-readable `0600` files.
- Correction: accept `0600` and group-readable `0640`, while still rejecting group
  mutation and every permission for other users.
- Regression/retest: exhaustive permission cases cover safe and unsafe modes.

## DEF-CLIENTCFG-001 - installed client ignored managed configuration

- Severity: High installation defect.
- Reproduction: an administrator-created ProgramData YAML had no effect because
  the loader always selected the bundled default unless code supplied a path.
- Correction: support an explicit `BLUEBUBBLES_CLIENT_CONFIG_FILE`, then an
  existing `%PROGRAMDATA%\BlueBubbles\client.yaml`, then the packaged default.
- Regression/retest: precedence, absence, and explicit override cases are tested.

## DEF-BACKUP-001 - scheduled backup could not authenticate or publish health

- Severity: Critical recovery defect.
- Reproduction: the root-owned systemd job invoked `pg_dump` without a database
  identity/password source, then wrote status mode `0600`, unreadable by the
  application monitoring service.
- Correction: use the restricted `bluebubbles_backup` identity with a root-only
  `PGPASSFILE`; publish status as root with the existing state-directory group and
  mode `0640`; confine service writes to backup and state paths.
- Regression/retest: backup command/identity, plan validation, status permissions
  and service-template tests.

## DEF-LDAPCFG-001 - disabled directory provider still required an LDAP secret

- Severity: Critical local-authentication startup defect.
- Reproduction: the installed environment always pointed at an LDAP password file;
  strict secret loading rejected its absence even when LDAP was disabled.
- Correction: ship the variable commented and require operators to enable it only
  after creating the file for directory authentication.
- Regression/retest: deployment template inspection and clean local-provider guide.

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
