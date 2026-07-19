# Task 22 execution report

## Implemented testing boundary

Task 22 adds generated property/security tests, 117 exhaustive constrained-setting
edge/out-of-bounds cases, a high-confidence secret scanner in the normal quality
gate, resolved-lock dependency auditing, fixed dependency regression tests, CI jobs
for Windows quality/package builds and migrated PostgreSQL integration, reproducible
local performance measurement, formal acceptance/traceability matrices, manual
usability/accessibility/infrastructure protocols, defect history, and explicit
known-untested records.

## Defects found and corrected

Testing found and corrected raw control characters being normalized before
rejection (`DEF-VALIDATION-001`). Dependency audits found 20 advisory records
across six workstation/server packages (`DEF-DEP-001`); all affected direct,
transitive, and build pins were upgraded, the application suite passed on the
replacements, and both final audits contain no known vulnerabilities. Task 21 also
corrected the Nginx/FastAPI TLS ownership mismatch (`DEF-DEPLOY-001`). No failed
result was removed from the record.

## Evidence

The final repository gate passed Black, Ruff, the high-confidence secret scan,
strict mypy across 350 source files, and a 477-case pytest collection: 474 passed,
three environment-gated PostgreSQL cases skipped, and branch-aware coverage was
90.16%. The only warnings were upstream deprecations from the FastAPI test client
and ldap3/pyasn1. Performance evidence is
`documentation/testing/evidence/performance-local-2026-07-18.json`; dependency
evidence is `dependency-audit-2026-07-18.json` and
`server-dependency-audit-2026-07-18.json`. Generated values and environment limits
are described beside results so component timings cannot be mistaken for
end-to-end LAN acceptance.

The final server archive was independently manifest-verified. The corrected
Windows one-directory executable was rebuilt against the remediated lock, its
report path was resolved from the publication root, and it remained responsive for
a five-second off-screen smoke test before controlled shutdown.

## Release status

Automated quality can pass on this workstation, but Version 1.0 acceptance is not
complete while PostgreSQL integration tests skip and the acceptance matrix contains
`PARTIAL` or `NOT RUN`. Required external evidence includes real Redis/LDAP,
Debian/systemd/Nginx/firewall/TLS, clean Windows installers, backup restore,
upgrade/rollback, full user journeys, LAN performance, usability participants, and
screen-reader/accessibility review. This stage documents those blockers rather than
claiming a release candidate; Tasks 23 and 24 remain out of scope.
