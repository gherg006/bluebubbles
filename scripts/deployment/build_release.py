"""Create a curated server release archive with a verifiable manifest."""

import argparse
import gzip
import json
import shutil
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from bluebubbles.deployment import FileIntegrityService, ReleaseManifest
from bluebubbles.version import __version__

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
RELEASE_INPUTS: Final = (
    "src",
    "migrations",
    "config",
    "deployment",
    "scripts/deployment",
    "documentation",
    "alembic.ini",
    "pyproject.toml",
    "pylock.toml",
    "README.md",
    "LICENSE",
)


def _normalise_tar_info(member: tarfile.TarInfo) -> tarfile.TarInfo:
    """Remove build-host metadata and retain executable deployment scripts."""
    member.uid = 0
    member.gid = 0
    member.uname = ""
    member.gname = ""
    member.mtime = 0
    if member.isdir() or member.name.endswith(".sh"):
        member.mode = 0o755
    else:
        member.mode = 0o644
    return member


class ServerReleaseBuilder:
    """Collect only approved source inputs and produce integrity evidence."""

    def __init__(self, project_root: Path, output_directory: Path) -> None:
        """Validate an output location below the project without following links."""
        self._project_root = project_root.resolve(strict=True)
        self._output_directory = output_directory.resolve()
        if self._output_directory == self._project_root:
            raise ValueError("release output cannot be the project root")
        if self._project_root not in self._output_directory.parents:
            raise ValueError("release output must remain below the project root")

    def build(self, *, created_by: str) -> tuple[Path, Path]:
        """Return the archive and external manifest paths for this source tree."""
        self._output_directory.mkdir(parents=True, exist_ok=True)
        archive_path = (
            self._output_directory / f"bluebubbles-server-{__version__}.tar.gz"
        )
        manifest_path = archive_path.with_suffix(archive_path.suffix + ".manifest.json")
        with tempfile.TemporaryDirectory(prefix="bluebubbles-release-") as temporary:
            stage = Path(temporary) / f"bluebubbles-server-{__version__}"
            stage.mkdir()
            for relative in RELEASE_INPUTS:
                source = self._project_root / relative
                if not source.exists() or source.is_symlink():
                    raise FileNotFoundError(
                        f"required release input missing: {relative}"
                    )
                destination = stage / relative
                if source.is_dir():
                    shutil.copytree(
                        source,
                        destination,
                        ignore=shutil.ignore_patterns(
                            "__pycache__",
                            "*.pyc",
                            "*.pyo",
                            "release-candidate-assessment-*.json",
                        ),
                    )
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
            with (
                archive_path.open("wb") as raw_archive,
                gzip.GzipFile(
                    filename="", mode="wb", fileobj=raw_archive, mtime=0
                ) as compressed,
                tarfile.open(
                    fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT
                ) as archive,
            ):
                archive.add(
                    stage,
                    arcname=stage.name,
                    recursive=True,
                    filter=_normalise_tar_info,
                )
        artifact = FileIntegrityService().record(self._output_directory, archive_path)
        manifest = ReleaseManifest(
            application_version=__version__,
            protocol_version=1,
            database_revision="0001_initial_schema",
            configuration_version=1,
            created_at=datetime.now(UTC),
            created_by=created_by,
            artifacts=(artifact,),
        )
        manifest_path.write_text(
            json.dumps(manifest.model_dump(mode="json"), indent=2) + "\n",
            encoding="utf-8",
        )
        archive_path.with_suffix(archive_path.suffix + ".sha256").write_text(
            f"{artifact.sha256}  {archive_path.name}\n", encoding="ascii"
        )
        return archive_path, manifest_path


def main() -> int:
    """Build a server archive from explicit operator metadata."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--created-by", required=True)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "dist" / "server")
    arguments = parser.parse_args()
    archive, manifest = ServerReleaseBuilder(PROJECT_ROOT, arguments.output).build(
        created_by=arguments.created_by
    )
    print(f"Release archive: {archive}")
    print(f"Release manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
