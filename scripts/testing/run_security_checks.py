"""Scan deployable repository inputs for high-confidence secret material."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
SCAN_ROOTS: Final = ("src", "config", "deployment", "packaging", "scripts", "tests")
TEXT_SUFFIXES: Final = {
    ".conf",
    ".ini",
    ".iss",
    ".py",
    ".service",
    ".sh",
    ".template",
    ".timer",
    ".toml",
    ".yaml",
    ".yml",
}
PRIVATE_KEY_HEADER: Final = "-----BEGIN " + "PRIVATE KEY-----"
JWT_PATTERN: Final = re.compile(
    r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\."
    r"[A-Za-z0-9_-]{10,}(?![A-Za-z0-9_-])"
)
DATABASE_CREDENTIAL_PATTERN: Final = re.compile(
    r"postgresql(?:\+asyncpg)?://[^\s:/]+:([^\s@]+)@", re.IGNORECASE
)
SAFE_CREDENTIAL_MARKERS: Final = frozenset(
    {
        "development-only",
        "example",
        "fake",
        "replace",
        "secret",
        "synthetic",
        "test",
        "unique-secret",
    }
)


@dataclass(frozen=True, slots=True)
class SecretFinding:
    """Identify one high-confidence prohibited value without echoing it."""

    path: Path
    line: int
    category: str


class SecretPatternScanner:
    """Scan text files while reporting only path, line, and safe category."""

    def __init__(self, root: Path) -> None:
        """Create a scanner rooted at an existing repository directory."""
        self._root = root.resolve(strict=True)
        if not self._root.is_dir():
            raise ValueError("secret scan root must be a directory")

    def scan(self) -> tuple[SecretFinding, ...]:
        """Return all private-key, JWT, and non-placeholder database findings."""
        findings: list[SecretFinding] = []
        for relative_root in SCAN_ROOTS:
            root = self._root / relative_root
            if not root.exists():
                continue
            for path in sorted(root.rglob("*")):
                if not path.is_file() or path.suffix.casefold() not in TEXT_SUFFIXES:
                    continue
                findings.extend(self._scan_file(path))
        return tuple(findings)

    def _scan_file(self, path: Path) -> list[SecretFinding]:
        """Inspect one bounded text file and never include matched values."""
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return [SecretFinding(path.relative_to(self._root), 0, "invalid_utf8")]
        findings: list[SecretFinding] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if PRIVATE_KEY_HEADER in line:
                findings.append(
                    SecretFinding(
                        path.relative_to(self._root), line_number, "private_key"
                    )
                )
            if JWT_PATTERN.search(line):
                findings.append(
                    SecretFinding(path.relative_to(self._root), line_number, "jwt")
                )
            for match in DATABASE_CREDENTIAL_PATTERN.finditer(line):
                credential = match.group(1).casefold()
                if not any(marker in credential for marker in SAFE_CREDENTIAL_MARKERS):
                    findings.append(
                        SecretFinding(
                            path.relative_to(self._root),
                            line_number,
                            "database_credential",
                        )
                    )
        return findings


def main() -> int:
    """Scan the current repository and return non-zero for any finding."""
    findings = SecretPatternScanner(PROJECT_ROOT).scan()
    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.category}")
    if findings:
        print(f"Secret scan failed with {len(findings)} high-confidence finding(s).")
        return 1
    print("Secret scan passed: no high-confidence secret material found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
