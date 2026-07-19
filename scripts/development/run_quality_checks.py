"""Run every repository-and-tooling quality gate in a fixed order."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
CHECKS: Final[tuple[tuple[str, ...], ...]] = (
    (
        "-m",
        "black",
        "--check",
        "src",
        "tests",
        "scripts",
        "migrations",
    ),
    ("-m", "ruff", "check", "src", "tests", "scripts", "migrations"),
    ("scripts/testing/run_security_checks.py",),
    ("-m", "mypy", "src", "tests", "scripts", "migrations"),
    ("-m", "pytest"),
)


def main() -> int:
    """Run format, lint, type, and test checks; stop at the first failure."""
    with tempfile.TemporaryDirectory(prefix="bluebubbles-black-") as cache_directory:
        environment = os.environ.copy()
        environment["BLACK_CACHE_DIR"] = cache_directory
        for arguments in CHECKS:
            # The executable and arguments are repository-owned constants, not input.
            completed = subprocess.run(  # noqa: S603
                (sys.executable, *arguments),
                cwd=PROJECT_ROOT,
                check=False,
                env=environment,
            )
            if completed.returncode != 0:
                return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
