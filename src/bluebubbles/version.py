"""Expose the application version from authoritative package metadata."""

import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _source_tree_version() -> str:
    """Read the version from pyproject.toml when running an unpackaged checkout."""
    project_file = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with project_file.open("rb") as project_stream:
        project = tomllib.load(project_stream)
    value = project["project"]["version"]
    if not isinstance(value, str):
        raise TypeError("project.version must be a string")
    return value


def get_version() -> str:
    """Return the installed version, falling back to source project metadata."""
    try:
        return version("bluebubbles-lan")
    except PackageNotFoundError:
        return _source_tree_version()


__version__ = get_version()
