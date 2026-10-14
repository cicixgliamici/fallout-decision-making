"""Identify actual research source contents, including uncommitted local edits."""

from hashlib import sha256
from pathlib import Path


def source_fingerprints() -> dict[str, str]:
    """Hash source and dependency declarations without claiming a clean Git revision."""
    root = Path(__file__).resolve().parents[2]
    paths = [*root.glob("src/pcds/*.py"), *root.glob("rules/*.pl")]
    paths.extend(root / name for name in ("pyproject.toml", "requirements.txt"))
    # Normalize line endings: checkout settings must not create different source identities.
    return {
        path.relative_to(root).as_posix(): sha256(
            path.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        for path in sorted(paths)
        if path.is_file()
    }
