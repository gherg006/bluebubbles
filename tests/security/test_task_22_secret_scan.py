"""Task 22 tests for repository secret-pattern scanning and safe reports."""

from pathlib import Path

from scripts.testing.run_security_checks import SecretPatternScanner


def test_secret_scanner_accepts_clear_placeholders_and_rejects_real_markers(
    tmp_path: Path,
) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "safe.py").write_text(
        'URL = "postgresql://app:development-only@example/db"\n', encoding="utf-8"
    )
    assert SecretPatternScanner(tmp_path).scan() == ()

    unsafe_url = "postgresql://" + "app:s3cret-value@localhost/db"
    (source / "unsafe.py").write_text(
        f'URL = "{unsafe_url}"\n' + "KEY = '-----BEGIN " + "PRIVATE KEY-----'\n",
        encoding="utf-8",
    )
    findings = SecretPatternScanner(tmp_path).scan()

    assert {finding.category for finding in findings} == {
        "database_credential",
        "private_key",
    }
    assert all("s3cret" not in str(finding) for finding in findings)


def test_repository_secret_scan_has_no_high_confidence_findings() -> None:
    project_root = Path(__file__).resolve().parents[2]
    assert SecretPatternScanner(project_root).scan() == ()
