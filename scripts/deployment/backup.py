"""Create a coordinated PostgreSQL, attachment, and configuration backup."""

import argparse
import json
import os
import re
import subprocess
import tarfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from bluebubbles.deployment import (
    BackupManifest,
    BackupResult,
    FileIntegrityService,
)
from bluebubbles.version import __version__

_DATABASE_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


@dataclass(frozen=True)
class BackupPlan:
    """Describe validated backup sources and an isolated destination."""

    output_root: Path
    database: str
    attachments: Path
    configuration: Path
    status_file: Path
    database_host: str = "127.0.0.1"
    database_user: str = "bluebubbles_backup"

    def __post_init__(self) -> None:
        """Reject unsafe roots, names, links, and overlapping paths."""
        if not _DATABASE_PATTERN.fullmatch(self.database):
            raise ValueError("database must be a PostgreSQL identifier")
        if not _DATABASE_PATTERN.fullmatch(self.database_user):
            raise ValueError("database user must be a PostgreSQL identifier")
        if not re.fullmatch(r"[A-Za-z0-9.-]{1,253}", self.database_host):
            raise ValueError("database host must be a hostname or IP address")
        output = self.output_root.resolve()
        if not output.is_absolute() or output == Path(output.anchor):
            raise ValueError("backup output must be a non-root absolute path")
        sources = (
            self.attachments.resolve(strict=True),
            self.configuration.resolve(strict=True),
        )
        if any(not source.is_dir() or source.is_symlink() for source in sources):
            raise ValueError("backup sources must be existing non-symlink directories")
        if any(output == source or output in source.parents for source in sources):
            raise ValueError("backup output cannot contain or equal a source")
        status = self.status_file.resolve()
        if status == Path(status.anchor):
            raise ValueError("backup status must be a non-root file path")


class BackupRunner:
    """Own one bounded offline backup and its atomic monitoring evidence."""

    def __init__(self, plan: BackupPlan) -> None:
        """Create a runner for one immutable plan."""
        self._plan = plan

    def run(self, *, stop_service: bool) -> BackupManifest:
        """Create all artifacts, verify them, and always restore service state."""
        started_at = datetime.now(UTC)
        backup_id = started_at.strftime("%Y%m%dT%H%M%SZ")
        backup_root = self._plan.output_root / "sets" / backup_id
        backup_root.mkdir(parents=True, mode=0o700, exist_ok=False)
        service_stopped = False
        results = {
            "database": BackupResult.FAILED,
            "attachments": BackupResult.FAILED,
            "configuration": BackupResult.FAILED,
            "verification": BackupResult.FAILED,
        }
        warnings: list[str] = []
        try:
            if stop_service:
                self._service_command("stop")
                service_stopped = True
            database_path = backup_root / "database.dump"
            subprocess.run(  # noqa: S603 - validated database, fixed executable
                (
                    "pg_dump",
                    "--format=custom",
                    "--file",
                    str(database_path),
                    "--host",
                    self._plan.database_host,
                    "--username",
                    self._plan.database_user,
                    self._plan.database,
                ),
                check=True,
                timeout=3600,
            )
            results["database"] = BackupResult.SUCCESS
            self._archive_directory(
                self._plan.attachments, backup_root / "attachments.tar.gz"
            )
            results["attachments"] = BackupResult.SUCCESS
            self._archive_directory(
                self._plan.configuration, backup_root / "configuration.tar.gz"
            )
            results["configuration"] = BackupResult.SUCCESS
            integrity = FileIntegrityService()
            artifacts = tuple(
                integrity.record(backup_root, path)
                for path in sorted(backup_root.iterdir())
                if path.is_file()
            )
            if not artifacts or not all(
                integrity.verify(backup_root, artifact) for artifact in artifacts
            ):
                raise RuntimeError("backup artifact verification failed")
            results["verification"] = BackupResult.SUCCESS
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            warnings.append(f"backup failed with {type(error).__name__}")
            artifacts = ()
        finally:
            if service_stopped:
                try:
                    self._service_command("start")
                except subprocess.SubprocessError:
                    warnings.append("service restart failed with SubprocessError")
        manifest = BackupManifest(
            backup_id=backup_id,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            application_version=__version__,
            database_revision="0001_initial_schema",
            database=results["database"],
            attachments=results["attachments"],
            configuration=results["configuration"],
            verification=results["verification"],
            artifacts=artifacts,
            warnings=tuple(warnings),
        )
        (backup_root / "manifest.json").write_text(
            json.dumps(manifest.model_dump(mode="json"), indent=2) + "\n",
            encoding="utf-8",
        )
        self._write_status(manifest)
        return manifest

    @staticmethod
    def _archive_directory(source: Path, destination: Path) -> None:
        """Archive a tree without accepting links that could escape its root."""
        if any(path.is_symlink() for path in source.rglob("*")):
            raise RuntimeError("backup source contains an unsupported symbolic link")
        with tarfile.open(destination, "w:gz", format=tarfile.PAX_FORMAT) as archive:
            archive.add(source, arcname=source.name, recursive=True)

    @staticmethod
    def _service_command(action: str) -> None:
        """Stop or start only the fixed BlueBubbles systemd unit."""
        if action not in {"start", "stop"}:
            raise ValueError("unsupported service action")
        subprocess.run(  # noqa: S603 - action is checked against a fixed allowlist
            ("systemctl", action, "bluebubbles.service"),
            check=True,
            timeout=120,
        )

    def _write_status(self, manifest: BackupManifest) -> None:
        """Atomically publish the exact schema consumed by Task 20 monitoring."""
        successful = all(
            result is BackupResult.SUCCESS
            for result in (
                manifest.database,
                manifest.attachments,
                manifest.configuration,
                manifest.verification,
            )
        )
        payload = {
            "backup_id": manifest.backup_id,
            "completed_at": manifest.completed_at.isoformat(),
            "successful": successful,
            "checksum_valid": manifest.verification is BackupResult.SUCCESS,
            "database": manifest.database.value,
            "attachments": manifest.attachments.value,
            "configuration": manifest.configuration.value,
        }
        self._plan.status_file.parent.mkdir(parents=True, mode=0o750, exist_ok=True)
        temporary = self._plan.status_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.chmod(temporary, 0o640)
        chown = getattr(os, "chown", None)
        if chown is not None:
            chown(temporary, -1, self._plan.status_file.parent.stat().st_gid)
        temporary.replace(self._plan.status_file)


def main() -> int:
    """Create one backup and return non-zero unless every component verifies."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--database-host", default="127.0.0.1")
    parser.add_argument("--database-user", default="bluebubbles_backup")
    parser.add_argument("--attachments", type=Path, required=True)
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--status-file", type=Path, required=True)
    parser.add_argument("--stop-service", action="store_true")
    arguments = parser.parse_args()
    plan = BackupPlan(
        arguments.output_root,
        arguments.database,
        arguments.attachments,
        arguments.configuration,
        arguments.status_file,
        arguments.database_host,
        arguments.database_user,
    )
    manifest = BackupRunner(plan).run(stop_service=arguments.stop_service)
    return 0 if manifest.verification is BackupResult.SUCCESS else 1


if __name__ == "__main__":
    raise SystemExit(main())
