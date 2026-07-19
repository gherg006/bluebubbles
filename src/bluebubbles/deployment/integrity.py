"""Streaming integrity verification for release and backup artifacts."""

import hashlib
from pathlib import Path

from bluebubbles.deployment.manifests import ArtifactRecord


class FileIntegrityService:
    """Calculate and verify SHA-256 records without loading whole files."""

    def __init__(self, *, chunk_size: int = 1024 * 1024) -> None:
        """Create a verifier with a positive bounded-memory read size."""
        if chunk_size < 1 or chunk_size > 16 * 1024 * 1024:
            raise ValueError("chunk_size must be between 1 byte and 16 MiB")
        self._chunk_size = chunk_size

    def record(self, root: Path, path: Path) -> ArtifactRecord:
        """Return integrity metadata for a regular file contained by ``root``.

        Args:
            root: Trusted release or backup root.
            path: Candidate artifact below that root.

        Returns:
            The canonical relative path, size, and SHA-256 digest.

        Raises:
            ValueError: If either path is unsafe or the file escapes the root.
            FileNotFoundError: If the candidate is not a regular file.
        """
        resolved_root = root.resolve(strict=True)
        if not resolved_root.is_dir():
            raise ValueError("integrity root must be a directory")
        resolved_path = path.resolve(strict=True)
        try:
            relative_path = resolved_path.relative_to(resolved_root)
        except ValueError as error:
            raise ValueError(
                "artifact must remain inside the integrity root"
            ) from error
        if not resolved_path.is_file() or resolved_path.is_symlink():
            raise FileNotFoundError("artifact must be a regular non-symlink file")
        digest = hashlib.sha256()
        with resolved_path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(self._chunk_size), b""):
                digest.update(chunk)
        return ArtifactRecord(
            path=relative_path.as_posix(),
            size_bytes=resolved_path.stat().st_size,
            sha256=digest.hexdigest(),
        )

    def verify(self, root: Path, artifact: ArtifactRecord) -> bool:
        """Return whether one contained file still matches its recorded evidence."""
        candidate = root.joinpath(*PureArtifactPath.parts(artifact.path))
        try:
            actual = self.record(root, candidate)
        except (FileNotFoundError, OSError, ValueError):
            return False
        return actual == artifact


class PureArtifactPath:
    """Split a validated manifest path without host-dependent separators."""

    @staticmethod
    def parts(value: str) -> tuple[str, ...]:
        """Return safe POSIX components from an already validated value."""
        return tuple(value.split("/"))
