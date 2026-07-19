"""Task 21 deployment, packaging, integrity, and boundary tests."""

import json
import re
import tarfile
import tomllib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError
from scripts.deployment.backup import BackupPlan, BackupRunner
from scripts.deployment.build_release import _normalise_tar_info
from scripts.deployment.render_nginx import render_nginx
from scripts.packaging.build_client import ClientBuilder, ClientBuildPlan

from bluebubbles.deployment import (
    ArtifactRecord,
    BackupManifest,
    BackupResult,
    DeploymentTemplateRenderer,
    FileIntegrityService,
    ReleaseManifest,
)
from bluebubbles.version import __version__

NOW = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
VALID_ARTIFACT = ArtifactRecord(path="release/app.whl", size_bytes=3, sha256="a" * 64)


def _release(**changes: object) -> ReleaseManifest:
    values: dict[str, object] = {
        "application_version": "0.1.0",
        "protocol_version": 1,
        "database_revision": "0001_initial_schema",
        "configuration_version": 1,
        "created_at": NOW,
        "created_by": "release-operator",
        "artifacts": (VALID_ARTIFACT,),
    }
    values.update(changes)
    return ReleaseManifest.model_validate(values)


@pytest.mark.parametrize(
    "path", ["", "/absolute", "../escape", "a/../b", "a\\b", "./a", "a//b"]
)
def test_artifact_paths_reject_empty_absolute_traversal_and_noncanonical_values(
    path: str,
) -> None:
    with pytest.raises(ValidationError, match="canonical relative POSIX"):
        ArtifactRecord(path=path, size_bytes=0, sha256="0" * 64)


@pytest.mark.parametrize("digest", ["a" * 63, "A" * 64, "g" * 64])
def test_artifact_digest_rejects_wrong_length_case_and_alphabet(digest: str) -> None:
    with pytest.raises(ValidationError, match="64 lower-case"):
        ArtifactRecord(path="artifact", size_bytes=0, sha256=digest)


def test_release_manifest_enforces_nonempty_unique_artifact_set() -> None:
    assert _release().protocol_version == 1
    with pytest.raises(ValidationError, match="at least one"):
        _release(artifacts=())
    with pytest.raises(ValidationError, match="unique"):
        _release(artifacts=(VALID_ARTIFACT, VALID_ARTIFACT))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("application_version", "bad value"),
        ("database_revision", "line\nbreak"),
        ("created_by", ""),
    ],
)
def test_release_manifest_rejects_unsafe_identifiers(field: str, value: str) -> None:
    with pytest.raises(ValidationError, match="unsupported characters"):
        _release(**{field: value})


def test_release_manifest_requires_offset_aware_timestamp() -> None:
    with pytest.raises(ValidationError, match="UTC offset"):
        _release(created_at=NOW.replace(tzinfo=None))


def _backup(**changes: object) -> BackupManifest:
    values: dict[str, object] = {
        "backup_id": "20260718T120000Z",
        "started_at": NOW,
        "completed_at": NOW + timedelta(seconds=1),
        "application_version": "0.1.0",
        "database_revision": "0001_initial_schema",
        "database": BackupResult.SUCCESS,
        "attachments": BackupResult.SUCCESS,
        "configuration": BackupResult.SUCCESS,
        "verification": BackupResult.SUCCESS,
        "artifacts": (VALID_ARTIFACT,),
    }
    values.update(changes)
    return BackupManifest.model_validate(values)


def test_backup_manifest_enforces_results_chronology_and_uniqueness() -> None:
    assert _backup().verification is BackupResult.SUCCESS
    assert _backup(database=BackupResult.FAILED, artifacts=()).artifacts == ()
    with pytest.raises(ValidationError, match="verified artifacts"):
        _backup(artifacts=())
    with pytest.raises(ValidationError, match="cannot precede"):
        _backup(completed_at=NOW - timedelta(microseconds=1))
    with pytest.raises(ValidationError, match="unique"):
        _backup(artifacts=(VALID_ARTIFACT, VALID_ARTIFACT))


@pytest.mark.parametrize("warning", ["", "line\nbreak", "x" * 501])
def test_backup_manifest_rejects_invalid_warning_evidence(warning: str) -> None:
    with pytest.raises(ValidationError, match="bounded"):
        _backup(warnings=(warning,))


def test_backup_manifest_rejects_naive_time_and_unsafe_identifier() -> None:
    with pytest.raises(ValidationError, match="UTC offset"):
        _backup(started_at=NOW.replace(tzinfo=None))
    with pytest.raises(ValidationError, match="unsupported characters"):
        _backup(backup_id="../backup")


@pytest.mark.parametrize("chunk_size", [0, 16 * 1024 * 1024 + 1])
def test_integrity_service_rejects_out_of_bounds_chunk_sizes(chunk_size: int) -> None:
    with pytest.raises(ValueError, match="between 1 byte and 16 MiB"):
        FileIntegrityService(chunk_size=chunk_size)


def test_integrity_service_streams_verifies_and_detects_tampering(
    tmp_path: Path,
) -> None:
    root = tmp_path / "release"
    root.mkdir()
    artifact = root / "nested" / "app.whl"
    artifact.parent.mkdir()
    artifact.write_bytes(b"abc")
    service = FileIntegrityService(chunk_size=1)

    record = service.record(root, artifact)

    assert record.path == "nested/app.whl"
    assert record.size_bytes == 3
    assert service.verify(root, record)
    artifact.write_bytes(b"abd")
    assert not service.verify(root, record)
    artifact.unlink()
    assert not service.verify(root, record)


def test_integrity_service_rejects_non_directory_root_and_escape(
    tmp_path: Path,
) -> None:
    root_file = tmp_path / "root"
    root_file.write_bytes(b"root")
    outside = tmp_path / "outside"
    outside.write_bytes(b"outside")
    with pytest.raises(ValueError, match="must be a directory"):
        FileIntegrityService().record(root_file, outside)
    root = tmp_path / "directory"
    root.mkdir()
    with pytest.raises(ValueError, match="inside"):
        FileIntegrityService().record(root, outside)


def test_template_renderer_requires_exact_placeholders_and_safe_values() -> None:
    renderer = DeploymentTemplateRenderer(
        "server_name ${server_hostname}; proxy_pass http://${upstream};",
        required_values=frozenset({"server_hostname", "upstream"}),
    )
    assert "chat.example.internal" in renderer.render(
        {"server_hostname": "chat.example.internal", "upstream": "127.0.0.1:8000"}
    )
    with pytest.raises(ValueError, match="exactly match"):
        renderer.render({"server_hostname": "chat.example.internal"})
    with pytest.raises(ValueError, match="unsafe"):
        renderer.render(
            {"server_hostname": "chat.example.internal\nroot", "upstream": "localhost"}
        )
    with pytest.raises(ValueError, match="cannot be empty"):
        DeploymentTemplateRenderer("", required_values=frozenset())
    with pytest.raises(ValueError, match="placeholders"):
        DeploymentTemplateRenderer("${unknown}", required_values=frozenset())


def test_nginx_renderer_preserves_native_variables_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    template = PROJECT_ROOT / "deployment/templates/bluebubbles.nginx.conf.template"
    output = tmp_path / "bluebubbles.conf"

    render_nginx(template, output, "chat.internal.example")
    rendered = output.read_text(encoding="utf-8")

    assert "server_name chat.internal.example;" in rendered
    assert "$host$request_uri" in rendered
    assert "$http_upgrade" in rendered
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        render_nginx(template, output, "chat.internal.example")


def test_backup_plan_rejects_invalid_database_root_overlap_and_missing_sources(
    tmp_path: Path,
) -> None:
    attachments = tmp_path / "attachments"
    configuration = tmp_path / "configuration"
    attachments.mkdir()
    configuration.mkdir()
    valid = BackupPlan(
        tmp_path / "backups",
        "bluebubbles_1",
        attachments,
        configuration,
        tmp_path / "state" / "status.json",
    )
    assert valid.database == "bluebubbles_1"
    assert valid.database_user == "bluebubbles_backup"
    with pytest.raises(ValueError, match="PostgreSQL identifier"):
        BackupPlan(
            tmp_path / "backups",
            "db;drop",
            attachments,
            configuration,
            tmp_path / "status",
        )
    with pytest.raises(ValueError, match="cannot contain"):
        BackupPlan(
            tmp_path,
            "database",
            attachments,
            configuration,
            tmp_path / "status",
        )
    with pytest.raises(FileNotFoundError):
        BackupPlan(
            tmp_path / "backups",
            "database",
            tmp_path / "missing",
            configuration,
            tmp_path / "status",
        )
    with pytest.raises(ValueError, match="database user"):
        BackupPlan(
            tmp_path / "backups",
            "database",
            attachments,
            configuration,
            tmp_path / "status",
            database_user="backup;drop",
        )
    with pytest.raises(ValueError, match="database host"):
        BackupPlan(
            tmp_path / "backups",
            "database",
            attachments,
            configuration,
            tmp_path / "status",
            database_host="host/name",
        )


def test_backup_uses_restricted_identity_and_publishes_verified_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attachments = tmp_path / "attachments"
    configuration = tmp_path / "configuration"
    attachments.mkdir()
    configuration.mkdir()
    (attachments / "ciphertext").write_bytes(b"encrypted")
    (configuration / "production.yaml").write_text("safe: true\n", encoding="utf-8")
    calls: list[tuple[str, ...]] = []

    def fake_run(command: tuple[str, ...], **_kwargs: object) -> None:
        calls.append(command)
        Path(command[command.index("--file") + 1]).write_bytes(b"database-dump")

    monkeypatch.setattr("scripts.deployment.backup.subprocess.run", fake_run)
    status = tmp_path / "state" / "status.json"
    plan = BackupPlan(
        tmp_path / "backups",
        "bluebubbles",
        attachments,
        configuration,
        status,
    )

    manifest = BackupRunner(plan).run(stop_service=False)

    assert manifest.verification.value == "success"
    assert calls and "--host" in calls[0] and "127.0.0.1" in calls[0]
    assert "--username" in calls[0] and "bluebubbles_backup" in calls[0]
    assert json.loads(status.read_text(encoding="utf-8"))["successful"] is True


def test_client_build_plan_uses_authoritative_version_and_non_shell_command() -> None:
    plan = ClientBuildPlan(__version__, PROJECT_ROOT, PROJECT_ROOT / "dist" / "test")
    assert plan.pyinstaller_command[1:3] == ("-m", "PyInstaller")
    assert "--clean" in plan.pyinstaller_command
    with pytest.raises(ValueError, match="authoritative"):
        ClientBuildPlan("9.9.9", PROJECT_ROOT, PROJECT_ROOT / "dist" / "test")
    with pytest.raises(ValueError, match="below"):
        ClientBuildPlan(__version__, PROJECT_ROOT, PROJECT_ROOT)


def test_client_build_report_path_is_relative_to_published_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "dist"
    plan = ClientBuildPlan(__version__, tmp_path, output)

    def fake_run(*_args: object, **_kwargs: object) -> None:
        executable = output / "BlueBubbles" / "BlueBubbles.exe"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"packaged-client")

    monkeypatch.setattr("scripts.packaging.build_client.subprocess.run", fake_run)

    report_path = ClientBuilder(plan).build()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["executable"]["path"] == "BlueBubbles/BlueBubbles.exe"
    assert (output / report["executable"]["path"]).is_file()


def test_server_requirements_are_exact_and_cover_non_gui_runtime() -> None:
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text("utf-8"))
    direct = {
        re.split(r"[<>=!~;\[]", value, maxsplit=1)[0].casefold()
        for value in project["project"]["dependencies"]
    }
    lines = (
        (PROJECT_ROOT / "deployment" / "server-requirements.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    requirements = [line for line in lines if line and not line.startswith("#")]
    names = {line.split("==", maxsplit=1)[0].casefold() for line in requirements}

    assert all(re.fullmatch(r"[A-Za-z0-9_.-]+==[^=\s]+", line) for line in requirements)
    assert direct - {"pyside6"} <= names
    assert "pyside6" not in names
    assert any(
        dependency.startswith("PySide6==") and "sys_platform == 'win32'" in dependency
        for dependency in project["project"]["dependencies"]
    )


def test_release_tar_metadata_is_reproducible_and_scripts_are_executable() -> None:
    script = _normalise_tar_info(tarfile.TarInfo("release/install.sh"))
    regular = _normalise_tar_info(tarfile.TarInfo("release/pyproject.toml"))
    directory = tarfile.TarInfo("release/config")
    directory.type = tarfile.DIRTYPE
    directory = _normalise_tar_info(directory)

    assert (script.uid, script.gid, script.mtime, script.mode) == (0, 0, 0, 0o755)
    assert (regular.uid, regular.gid, regular.mtime, regular.mode) == (0, 0, 0, 0o644)
    assert directory.mode == 0o755


def test_release_builder_excludes_self_mutating_candidate_assessment() -> None:
    source = (PROJECT_ROOT / "scripts/deployment/build_release.py").read_text(
        encoding="utf-8"
    )
    assert '"release-candidate-assessment-*.json"' in source


def test_server_lifecycle_scripts_install_and_check_locked_dependencies() -> None:
    install = (PROJECT_ROOT / "scripts/deployment/install_server.sh").read_text(
        encoding="utf-8"
    )
    upgrade = (PROJECT_ROOT / "scripts/deployment/upgrade_server.sh").read_text(
        encoding="utf-8"
    )
    rollback = (PROJECT_ROOT / "scripts/deployment/rollback_server.sh").read_text(
        encoding="utf-8"
    )

    for script in (install, upgrade, rollback):
        assert "server-requirements.txt" in script
        assert "python -m pip check" in script
        assert "/bin/pip " not in script
    assert "/opt/bluebubbles/releases/*" in install
    assert "/opt/bluebubbles/current.new" in install


def test_checked_in_deployment_templates_match_real_routes_and_exposure_policy() -> (
    None
):
    nginx = (
        PROJECT_ROOT / "deployment/templates/bluebubbles.nginx.conf.template"
    ).read_text(encoding="utf-8")
    service = (PROJECT_ROOT / "deployment/templates/bluebubbles.service").read_text(
        encoding="utf-8"
    )
    backup_service = (
        PROJECT_ROOT / "deployment/templates/bluebubbles-backup.service"
    ).read_text(encoding="utf-8")
    environment = (PROJECT_ROOT / "deployment/templates/environment").read_text(
        encoding="utf-8"
    )
    installer = (PROJECT_ROOT / "packaging/windows/BlueBubbles.iss").read_text(
        encoding="utf-8"
    )
    assert "location /api/v1/ws" in nginx
    assert "proxy_pass http://127.0.0.1:8000" in nginx
    assert "ssl_protocols TLSv1.2 TLSv1.3" in nginx
    assert "RequiresMountsFor=/var/lib/bluebubbles/attachments" in service
    assert "NoNewPrivileges=true" in service
    assert "--config-directory /etc/bluebubbles" in service
    assert "PGPASSFILE=/etc/bluebubbles/secrets/backup.pgpass" in backup_service
    assert "--database-user bluebubbles_backup" in backup_service
    assert "ReadWritePaths=/var/backups/bluebubbles" in backup_service
    assert "# BLUEBUBBLES_LDAP_BIND_PASSWORD_FILE=" in environment
    assert "%LOCALAPPDATA%" not in installer
    assert "deliberately preserved" in installer
