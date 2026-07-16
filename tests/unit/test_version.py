"""Tests for authoritative version discovery."""

import tomllib
from importlib.metadata import PackageNotFoundError
from pathlib import Path

import pytest

import bluebubbles.version as version_module
from bluebubbles.version import __version__, get_version


def test_version_matches_project_metadata() -> None:
    project_file = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with project_file.open("rb") as stream:
        project = tomllib.load(stream)

    assert __version__ == project["project"]["version"]
    assert get_version() == __version__


def test_source_tree_fallback_reads_authoritative_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def distribution_missing(_distribution_name: str) -> str:
        raise PackageNotFoundError

    monkeypatch.setattr(version_module, "version", distribution_missing)

    assert version_module.get_version() == __version__
