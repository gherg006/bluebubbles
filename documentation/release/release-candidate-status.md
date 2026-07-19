# Release-candidate status

**Decision: BLOCKED. No BlueBubbles 0.1.0 release candidate has been issued.**

The documentation stage is complete in source, but the release gate cannot be
passed honestly. The default packaged client constructs `UnavailableUiBackend`,
so it cannot perform production login or messaging. A PyInstaller bundle is not a
functional product while that seam remains unbound. There is also no verified
Windows Setup executable, and the acceptance matrix retains required live Debian,
PostgreSQL, Redis, LDAP, TLS, backup/restore, two-client, accessibility and
usability work.

The machine-readable assessment is deliberately fail-closed. It must not be
edited to waive a gate. Correct the product/environment, retain the evidence, and
rerun it. The canonical open defects are `RC-CLIENT-001` and
`RC-INSTALLER-001` in the defect log.

## What is usable now

- The component architecture and contracts have broad deterministic test coverage.
- The server source archive, deployment helpers, systemd/Nginx templates and
  operational runbooks can be built and inspected.
- The client UI and lower-level client services are independently tested.
- The complete startup guide is suitable for executing the missing clean-host
  acceptance, but it clearly identifies the client blocker.

These facts are engineering evidence, not release acceptance.
