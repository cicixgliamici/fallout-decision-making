"""Identify actual research source contents, including uncommitted local edits.

Hashes cover file contents, including comments. A documentation-only source edit
therefore changes provenance even when all simulated outcomes remain identical.
Stored snapshots retain the source identity of the run that produced them.
"""

from hashlib import sha256
from pathlib import Path


def source_fingerprints() -> dict[str, str]:
    """Hash source and dependency declarations without claiming a clean Git revision."""
    root = Path(__file__).resolve().parents[2]
    paths = [*root.glob("src/pcds/*.py"), *root.glob("rules/*.pl")]
    paths.extend(root / name for name in ("pyproject.toml", "requirements.txt"))
    paths.extend([root / "toolchains.toml", root / "formal/lean/lean-toolchain"])
    paths.extend((root / "formal/lean").rglob("*.lean"))
    paths = [path for path in paths if ".lake" not in path.parts]
    # Normalize line endings: checkout settings must not create different source identities.
    return {
        path.relative_to(root).as_posix(): sha256(
            path.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        for path in sorted(paths)
        if path.is_file()
    }
