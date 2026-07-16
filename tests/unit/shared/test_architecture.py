"""Source-level tests for shared-package dependency and contract ownership."""

import ast
from pathlib import Path


def _shared_files() -> tuple[Path, ...]:
    root = Path(__file__).resolve().parents[3] / "src" / "bluebubbles" / "shared"
    return tuple(root.rglob("*.py"))


def test_shared_package_does_not_import_client_or_server() -> None:
    forbidden = ("bluebubbles.client", "bluebubbles.server")
    for source_file in _shared_files():
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        imports = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        ]
        imports.extend(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        assert not any(name.startswith(forbidden) for name in imports), source_file


def test_error_code_has_one_authoritative_definition() -> None:
    definitions: list[Path] = []
    source_root = Path(__file__).resolve().parents[3] / "src" / "bluebubbles"
    for source_file in source_root.rglob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        if any(
            isinstance(node, ast.ClassDef) and node.name == "ErrorCode"
            for node in tree.body
        ):
            definitions.append(source_file)
    assert len(definitions) == 1
    assert definitions[0].as_posix().endswith("shared/errors/codes.py")


def test_every_shared_module_has_documentation() -> None:
    for source_file in _shared_files():
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        assert ast.get_docstring(tree), source_file


def test_client_and_server_domain_packages_are_independently_importable() -> None:
    source_root = Path(__file__).resolve().parents[3] / "src" / "bluebubbles"
    for package, forbidden in (
        ("client", "bluebubbles.server"),
        ("server", "bluebubbles.client"),
    ):
        for source_file in (source_root / package / "domain").rglob("*.py"):
            tree = ast.parse(source_file.read_text(encoding="utf-8"))
            imports = [
                node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module is not None
            ]
            imports.extend(
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            )
            assert not any(name.startswith(forbidden) for name in imports), source_file
