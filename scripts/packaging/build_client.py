"""Build and verify the Windows one-directory client and optional installer."""

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from bluebubbles.deployment import FileIntegrityService
from bluebubbles.version import __version__

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ClientBuildPlan:
    """Describe validated client packaging inputs and outputs."""

    version: str
    project_root: Path
    output_root: Path

    def __post_init__(self) -> None:
        """Reject unsafe versions and output paths before cleanup or execution."""
        if self.version != __version__:
            raise ValueError(
                "build version must equal the authoritative project version"
            )
        project = self.project_root.resolve(strict=True)
        output = self.output_root.resolve()
        if output == project or project not in output.parents:
            raise ValueError("client build output must be below the project root")

    @property
    def pyinstaller_command(self) -> tuple[str, ...]:
        """Return the non-shell PyInstaller invocation."""
        return (
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--distpath",
            str(self.output_root),
            "--workpath",
            str(self.project_root / "build" / "pyinstaller"),
            str(self.project_root / "packaging" / "windows" / "BlueBubbles.spec"),
        )


class ClientBuilder:
    """Own the clean build, checksums, report, and optional Inno Setup step."""

    def __init__(self, plan: ClientBuildPlan) -> None:
        """Create a builder for one immutable build plan."""
        self._plan = plan

    def build(self, *, installer_compiler: Path | None = None) -> Path:
        """Build the client and return the machine-readable build report path."""
        if self._plan.output_root.exists():
            shutil.rmtree(self._plan.output_root)
        subprocess.run(  # noqa: S603 - immutable repository-owned command
            self._plan.pyinstaller_command,
            cwd=self._plan.project_root,
            check=True,
        )
        client_root = self._plan.output_root / "BlueBubbles"
        executable = client_root / "BlueBubbles.exe"
        if not executable.is_file():
            raise RuntimeError("PyInstaller did not produce BlueBubbles.exe")
        integrity = FileIntegrityService()
        # The report travels beside the bundle, so paths are relative to that
        # published root (not to the nested PyInstaller directory).
        executable_record = integrity.record(self._plan.output_root, executable)
        report = {
            "application_version": self._plan.version,
            "created_at": datetime.now(UTC).isoformat(),
            "format": "pyinstaller-onedir",
            "executable": executable_record.model_dump(mode="json"),
            "signed": False,
            "signing_limitation": (
                "No organisational Windows code-signing certificate was supplied."
            ),
        }
        report_path = self._plan.output_root / "client-build-report.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        checksum_path = self._plan.output_root / "BlueBubbles.exe.sha256"
        checksum_path.write_text(
            f"{executable_record.sha256}  BlueBubbles/BlueBubbles.exe\n",
            encoding="ascii",
        )
        if installer_compiler is not None:
            self._build_installer(installer_compiler)
        return report_path

    def _build_installer(self, compiler: Path) -> None:
        """Compile the checked-in Inno Setup definition when explicitly requested."""
        resolved = compiler.resolve(strict=True)
        if not resolved.is_file() or resolved.name.casefold() != "iscc.exe":
            raise ValueError("installer compiler must be an existing ISCC.exe")
        subprocess.run(  # noqa: S603 - explicitly selected compiler and fixed script
            (
                str(resolved),
                f"/DMyAppVersion={self._plan.version}",
                f"/DSourceDirectory={self._plan.output_root / 'BlueBubbles'}",
                str(
                    self._plan.project_root
                    / "packaging"
                    / "windows"
                    / "BlueBubbles.iss"
                ),
            ),
            cwd=self._plan.project_root,
            check=True,
        )


def main() -> int:
    """Parse packaging inputs and execute the controlled build."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=__version__)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "dist")
    parser.add_argument("--inno-compiler", type=Path)
    parser.add_argument("--print-command", action="store_true")
    arguments = parser.parse_args()
    plan = ClientBuildPlan(arguments.version, PROJECT_ROOT, arguments.output)
    if arguments.print_command:
        print(json.dumps(plan.pyinstaller_command))
        return 0
    report = ClientBuilder(plan).build(installer_compiler=arguments.inno_compiler)
    print(f"Client build completed: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
