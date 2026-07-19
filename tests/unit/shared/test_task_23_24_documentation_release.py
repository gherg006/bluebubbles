"""Task 23 documentation traceability and Task 24 fail-closed release gates."""

import re
from pathlib import Path

from scripts.documentation.generate_reference import (
    api_reference,
    configuration_reference,
)
from scripts.release.assess_candidate import assess

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = PROJECT_ROOT / "documentation"
LINK_PATTERN = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
LINK_CHECK_FILES = (
    PROJECT_ROOT / "README.md",
    DOCUMENTATION_ROOT / "INDEX.md",
    DOCUMENTATION_ROOT / "documentation-coverage.md",
    DOCUMENTATION_ROOT / "guides/complete-startup-guide.md",
    DOCUMENTATION_ROOT / "guides/user-guide.md",
    DOCUMENTATION_ROOT / "guides/administrator-guide.md",
    DOCUMENTATION_ROOT / "guides/developer-guide.md",
    DOCUMENTATION_ROOT / "release/known-limitations-and-evaluation.md",
    DOCUMENTATION_ROOT / "release/release-candidate-status.md",
)


def test_generated_references_match_authoritative_models_and_routes() -> None:
    assert (DOCUMENTATION_ROOT / "reference/configuration-reference.md").read_text(
        encoding="utf-8"
    ) == configuration_reference()
    api = (DOCUMENTATION_ROOT / "reference/api-and-websocket-reference.md").read_text(
        encoding="utf-8"
    )
    assert api == api_reference()
    assert "`database.url`" in configuration_reference()
    assert "`network.port`" in configuration_reference()
    assert "`/api/v1/auth/login`" in api
    assert "`/api/v1/ws`" in api


def test_consolidated_document_links_resolve() -> None:
    failures: list[str] = []
    for source in LINK_CHECK_FILES:
        text = source.read_text(encoding="utf-8")
        for raw_target in LINK_PATTERN.findall(text):
            target = raw_target.partition("#")[0].strip("<>")
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (source.parent / target).resolve()
            if not resolved.exists():
                failures.append(f"{source.relative_to(PROJECT_ROOT)} -> {target}")
    assert not failures, "Broken documentation links:\n" + "\n".join(failures)


def test_required_diagrams_guides_boundaries_and_release_warning_are_present() -> None:
    architecture = (
        DOCUMENTATION_ROOT / "architecture/system-architecture.md"
    ).read_text(encoding="utf-8")
    assert architecture.count("```mermaid") == 13
    for guide in (
        "complete-startup-guide.md",
        "user-guide.md",
        "administrator-guide.md",
        "developer-guide.md",
        "active-directory.md",
    ):
        assert (DOCUMENTATION_ROOT / "guides" / guide).is_file()
    startup = (DOCUMENTATION_ROOT / "guides/complete-startup-guide.md").read_text(
        encoding="utf-8"
    )
    status = (DOCUMENTATION_ROOT / "release/release-candidate-status.md").read_text(
        encoding="utf-8"
    )
    assert "RC-CLIENT-001" in startup
    assert "**Decision: BLOCKED" in status
    assert "No BlueBubbles 0.1.0 release candidate has been issued" in status


def test_current_candidate_assessment_refuses_known_missing_evidence() -> None:
    report = assess(PROJECT_ROOT, worktree_clean=True)
    gates = {gate.code: gate for gate in report.gates}
    assert not report.eligible
    assert gates["RC-QUALITY-001"].passed
    assert gates["RC-DOCS-001"].passed
    assert gates["RC-SOURCE-001"].passed
    assert not gates["RC-SERVER-001"].passed
    assert not gates["RC-INSTALLER-001"].passed
    assert not gates["RC-CLIENT-001"].passed
    assert not gates["RC-ACCEPTANCE-001"].passed
