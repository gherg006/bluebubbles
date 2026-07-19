"""Regression tests for dependency vulnerabilities found during Task 22."""

import tomllib
from pathlib import Path

from starlette.requests import Request


def test_locked_security_sensitive_dependencies_remain_on_remediated_versions() -> None:
    project_root = Path(__file__).resolve().parents[2]
    with (project_root / "pylock.toml").open("rb") as stream:
        lock = tomllib.load(stream)
    versions = {
        package["name"].casefold(): package["version"]
        for package in lock["packages"]
        if "version" in package
    }
    assert versions["black"] == "26.5.1"
    assert versions["cryptography"] == "49.0.0"
    assert versions["fastapi"] == "0.139.1"
    assert versions["pynacl"] == "1.6.2"
    assert versions["pytest"] == "9.1.1"
    assert versions["starlette"] == "1.3.1"


def test_malformed_host_cannot_change_security_sensitive_request_path() -> None:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/admin/maintenance",
        "raw_path": b"/api/v1/admin/maintenance",
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"attacker.invalid/concealed?value=")],
        "client": ("127.0.0.1", 12345),
        "server": ("127.0.0.1", 8000),
    }

    request = Request(scope)

    assert request.url.path == "/api/v1/admin/maintenance"
    assert request.url.hostname == "127.0.0.1"
