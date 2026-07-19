"""Verify a server release against its external manifest before installation."""

import argparse
import json
from pathlib import Path

from bluebubbles.deployment import FileIntegrityService, ReleaseManifest


def verify_manifest(manifest_path: Path, artifact_root: Path) -> bool:
    """Return whether every strictly parsed manifest artifact is authentic."""
    manifest = ReleaseManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    integrity = FileIntegrityService()
    return all(integrity.verify(artifact_root, item) for item in manifest.artifacts)


def main() -> int:
    """Verify named evidence and return non-zero on mismatch."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--artifact-root", type=Path, required=True)
    arguments = parser.parse_args()
    valid = verify_manifest(arguments.manifest, arguments.artifact_root)
    print(json.dumps({"valid": valid}))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
