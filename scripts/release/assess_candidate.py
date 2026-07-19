"""Assess release-candidate evidence and refuse promotion when any gate is open."""

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from bluebubbles.deployment import FileIntegrityService, ReleaseManifest


@dataclass(frozen=True, slots=True)
class GateResult:
    """Record one independently verifiable release gate."""

    code: str
    passed: bool
    severity: str
    detail: str


@dataclass(frozen=True, slots=True)
class CandidateAssessment:
    """Record the complete promotion decision without weakening failures."""

    application_version: str
    assessed_at: str
    eligible: bool
    gates: tuple[GateResult, ...]


REQUIRED_DOCUMENTS = (
    "README.md",
    "documentation/architecture/system-architecture.md",
    "documentation/architecture/algorithms-and-pseudocode.md",
    "documentation/security/security-and-cryptography.md",
    "documentation/guides/complete-startup-guide.md",
    "documentation/guides/user-guide.md",
    "documentation/guides/administrator-guide.md",
    "documentation/guides/developer-guide.md",
    "documentation/guides/active-directory.md",
    "documentation/reference/configuration-reference.md",
    "documentation/reference/api-and-websocket-reference.md",
    "documentation/release/known-limitations-and-evaluation.md",
)


def _git_is_clean(repository: Path) -> bool:
    result = subprocess.run(  # noqa: S603 - fixed Git read-only inspection
        ("git", "status", "--porcelain"),
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    return not result.stdout.strip()


def _audits_are_clean(repository: Path) -> bool:
    evidence = repository / "documentation/testing/evidence"
    workstation = sorted(evidence.glob("dependency-audit-*.json"))
    server = sorted(evidence.glob("server-dependency-audit-*.json"))
    if not workstation or not server:
        return False
    paths = (workstation[-1], server[-1])
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if any(item.get("vulns") for item in payload.get("dependencies", ())):
            return False
    return True


def _acceptance_is_complete(repository: Path) -> bool:
    matrix = repository / "documentation/testing/acceptance-matrix.md"
    if not matrix.is_file():
        return False
    text = matrix.read_text(encoding="utf-8")
    return "| PARTIAL |" not in text and "| NOT RUN |" not in text


def _server_manifest_is_valid(manifest_path: Path | None) -> bool:
    if manifest_path is None or not manifest_path.is_file():
        return False
    manifest = ReleaseManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    root = manifest_path.parent
    integrity = FileIntegrityService()
    return all(integrity.verify(root, artifact) for artifact in manifest.artifacts)


def _client_installer_is_valid(installer: Path | None) -> bool:
    return bool(
        installer is not None
        and installer.is_file()
        and installer.suffix.casefold() == ".exe"
        and "setup" in installer.name.casefold()
        and installer.stat().st_size > 0
    )


def assess(
    repository: Path,
    *,
    server_manifest: Path | None = None,
    client_installer: Path | None = None,
    worktree_clean: bool | None = None,
) -> CandidateAssessment:
    """Return an evidence-based candidate decision for the selected repository."""
    repository = repository.resolve(strict=True)
    application = (repository / "src/bluebubbles/client/application.py").read_text(
        encoding="utf-8"
    )
    checks = (
        GateResult(
            "RC-QUALITY-001",
            _audits_are_clean(repository),
            "critical",
            "Both point-in-time dependency audits contain no known vulnerabilities.",
        ),
        GateResult(
            "RC-SERVER-001",
            _server_manifest_is_valid(server_manifest),
            "critical",
            "The server archive exists and matches every external manifest record.",
        ),
        GateResult(
            "RC-INSTALLER-001",
            _client_installer_is_valid(client_installer),
            "critical",
            "A non-empty versioned Windows Setup executable exists.",
        ),
        GateResult(
            "RC-CLIENT-001",
            "backend or UnavailableUiBackend()" not in application,
            "critical",
            "The packaged client composes a real production UiBackend.",
        ),
        GateResult(
            "RC-ACCEPTANCE-001",
            _acceptance_is_complete(repository),
            "critical",
            "The acceptance matrix has no PARTIAL or NOT RUN result.",
        ),
        GateResult(
            "RC-DOCS-001",
            all((repository / path).is_file() for path in REQUIRED_DOCUMENTS),
            "high",
            "Every mandatory consolidated document exists.",
        ),
        GateResult(
            "RC-SOURCE-001",
            worktree_clean if worktree_clean is not None else _git_is_clean(repository),
            "high",
            "The source worktree contains no uncommitted release changes.",
        ),
    )
    return CandidateAssessment(
        "0.1.0",
        datetime.now(UTC).isoformat(),
        all(result.passed for result in checks),
        checks,
    )


def main() -> int:
    """Assess, write JSON evidence, and return non-zero for a blocked candidate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--server-manifest", type=Path)
    parser.add_argument("--client-installer", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = assess(
        arguments.repository,
        server_manifest=arguments.server_manifest,
        client_installer=arguments.client_installer,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(asdict(report), indent=2) + "\n", encoding="utf-8"
    )
    print("ELIGIBLE" if report.eligible else "BLOCKED")
    for gate in report.gates:
        print(f"{'PASS' if gate.passed else 'FAIL'} {gate.code}: {gate.detail}")
    return 0 if report.eligible else 1


if __name__ == "__main__":
    raise SystemExit(main())
