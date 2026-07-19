# NEA evidence index

This index points to repository evidence and identifies evidence that still needs a
human or clean environment. No absent evidence is represented as complete.

| Evidence area | Repository evidence | Status |
|---|---|---|
| Problem, stakeholders, objectives, research, alternatives | complete split specification, README and architecture decisions in development notes | Available; stakeholder/user-study artefacts remain owner-supplied |
| System/deployment/component diagrams | `architecture/system-architecture.md` diagrams 1-4 | Complete against current implementation |
| Authentication/message/attachment/offline/audit/backup flows | diagrams 5-13 | Complete against current implementation |
| Class/domain architecture | domain, repository and UI development notes plus typed source | Available; rendered class diagram not separately captured |
| Database design | schema/migration note, ORM, seven immutable revisions | Complete automated/rendered; live PostgreSQL rehearsal pending |
| Algorithms and pseudocode | `architecture/algorithms-and-pseudocode.md` | Complete |
| Interface design | PySide6 note, widget/ViewModel tests | Implemented UI evidence; current screenshots/human review pending |
| Security design | security guide, architecture/security/property tests | Automated evidence complete; deployed inspections pending |
| Development iterations | Task 06-23 execution reports and defect log | Available |
| Unit/API/crypto/file/offline/GUI tests | test tree, Task reports, acceptance matrix | Automated evidence available |
| Failed tests/corrections | stable defect log including dependency, deployment and release blockers | Available |
| Performance | local JSON baseline and acceptance matrix | Component only; LAN/E2E pending |
| Deployment/backup restore | scripts, manifests, guides | Static/component only; clean restore pending |
| Accessibility/user feedback | widget tests and manual protocols | Human evidence not yet supplied |
| Final evaluation/future improvements | known-limitations/evaluation document | Current and deliberately non-accepting |

Evidence files must contain synthetic data, redact sensitive screens/logs, identify
environment/version/time/tester, preserve failures, and link corrections to stable
defect IDs. Screenshots and user feedback cannot be fabricated by code generation.
