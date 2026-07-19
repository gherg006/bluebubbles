# PyInstaller one-directory definition. Run through scripts/packaging/build_client.py.
from pathlib import Path

project_root = Path(SPECPATH).parents[1]

a = Analysis(
    [str(project_root / "src" / "bluebubbles" / "client" / "main.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[
        (str(project_root / "config" / "client" / "default.yaml"), "config/client"),
        (str(project_root / "LICENSE"), "."),
    ],
    hiddenimports=["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "mypy", "black", "ruff"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BlueBubbles",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="BlueBubbles",
)
