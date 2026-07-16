"""Run every repository-and-tooling quality gate in a fixed order."""

import subprocess
import sys
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
CHECKS: Final[tuple[tuple[str, ...], ...]] = (
    ("-m", "black", "--check", "src", "tests", "scripts"),
    ("-m", "ruff", "check", "src", "tests", "scripts"),
    ("-m", "mypy", "src", "tests", "scripts"),
    ("-m", "pytest"),
)


def main() -> int:
    """Run format, lint, type, and test checks; stop at the first failure."""
    for arguments in CHECKS:
        # The executable and arguments are repository-owned constants, not input.
        completed = subprocess.run(  # noqa: S603
            (sys.executable, *arguments), cwd=PROJECT_ROOT, check=False
        )
        if completed.returncode != 0:
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
