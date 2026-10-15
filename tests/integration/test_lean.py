"""Build the actual pinned Lean sources independently of Python simulation checks."""

from pathlib import Path
import shutil
import subprocess
import tomllib

import pytest

pytestmark = pytest.mark.lean
ROOT = Path(__file__).resolve().parents[2]


def test_pinned_lean_build():
    lake = shutil.which("lake")
    assert lake, "Lean integration requires lake on PATH; install the pinned toolchain."
    pins = tomllib.loads((ROOT / "toolchains.toml").read_text(encoding="utf-8"))
    expected = pins["formal"]["lean"]
    formal = ROOT / "formal/lean"
    assert (formal / "lean-toolchain").read_text().strip() == f"leanprover/lean4:v{expected}"
    version = subprocess.run([lake, "env", "lean", "--version"], cwd=formal,
                             stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
    assert version.returncode == 0, version.stdout + version.stderr
    assert f"version {expected}," in version.stdout, version.stdout
    build = subprocess.run([lake, "build", "Wasteland"], cwd=formal, capture_output=True,
                           stdin=subprocess.DEVNULL, text=True, timeout=180)
    assert build.returncode == 0, build.stdout + build.stderr
    assert "declaration uses 'sorry'" not in build.stdout + build.stderr
    assert (formal / ".lake/build/lib/lean/Wasteland/Governance.olean").is_file()
