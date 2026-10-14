"""Keep a compact, auditable study snapshot in the reviewer documentation."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
from importlib.metadata import distribution, version
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import polars as pl
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from pcds.provenance import source_fingerprints


def archive_differences(source: Path, destination: Path) -> None:
    """Compress verbose elementary observations without dropping any seed or metric."""
    entry = ZipInfo(source.name, date_time=(2026, 10, 14, 0, 0, 0))
    entry.compress_type = ZIP_DEFLATED
    # A fixed archive timestamp avoids unrelated binary differences on regeneration.
    with ZipFile(destination, "w") as archive:
        archive.writestr(entry, source.read_bytes())


def record_environment(destination: Path) -> None:
    """Record only project/test dependency closure, excluding unrelated installed projects."""
    pending = ["numpy", "networkx", "polars", "matplotlib", "pydantic", "typer", "pyswip",
               "pytest", "ruff"]
    pinned = {}
    while pending:
        name = canonicalize_name(pending.pop())
        if name in pinned:
            continue
        pinned[name] = version(name)
        for text in distribution(name).requires or []:
            requirement = Requirement(text)
            if requirement.marker is None or requirement.marker.evaluate({"extra": ""}):
                pending.append(requirement.name)
    text = (f"# Recorded {platform.system()}/Python {platform.python_version()} environment; "
            "not a cross-platform lockfile.\n")
    text += "# Install this repository separately; source hashes identify local changes.\n"
    text += "\n".join(f"{name}=={value}" for name, value in sorted(pinned.items())) + "\n"
    (destination / "environment_requirements.txt").write_text(text, encoding="utf-8")


def _copy_holdout(source: Path, destination: Path) -> list[str]:
    """Keep a separate seed block distinct from the main condition estimates."""
    metadata = json.loads((source / "holdout_metadata.json").read_text(encoding="utf-8"))
    if metadata["source_sha256"] != source_fingerprints():
        raise ValueError("holdout source differs from current code")
    validation = json.loads((source / "holdout_validation.json").read_text(encoding="utf-8"))
    if not validation["passed"]:
        raise ValueError("only a validated holdout block can become a review snapshot")
    names = ["holdout_raw.csv", "holdout_effects.csv", "holdout_metadata.json",
             "holdout_validation.json"]
    for name in names:
        shutil.copyfile(source / name, destination / name)
    archive = "holdout_paired_differences.csv.zip"
    archive_differences(source / "holdout_paired_differences.csv", destination / archive)
    return [*names, archive]


def prepare_snapshot(source: Path, destination: Path, holdout: Path | None = None) -> None:
    """Copy only validated outputs produced by the current recorded source contents."""
    validation = json.loads((source / "suite_validation.json").read_text(encoding="utf-8"))
    metadata = json.loads((source / "suite_metadata.json").read_text(encoding="utf-8"))
    if not validation["passed"]:
        raise ValueError("only a validated study can become a review snapshot")
    if metadata["source_sha256"] != source_fingerprints():
        raise ValueError("study source differs from current code; regenerate or restore that revision")
    raw = pl.read_csv(source / "suite_raw.csv")
    if raw.height != validation["checks"]["expected_raw_rows"]:
        raise ValueError("raw row count does not match validation")
    destination.mkdir(parents=True, exist_ok=True)
    names = [
        "suite_raw.csv", "suite_summary.csv", "suite_effects_vs_majority.csv",
        "suite_metadata.json", "suite_validation.json", "survival_by_condition.png",
        "baseline_paired_effects.png",
    ]
    for name in names:
        shutil.copyfile(source / name, destination / name)
    archive_name = "suite_paired_differences.csv.zip"
    archive_differences(source / "suite_paired_differences.csv", destination / archive_name)
    report = (source / "suite_report.md").read_text(encoding="utf-8")
    report = report.replace("(suite_paired_differences.csv)", f"({archive_name})")
    (destination / "suite_report.md").write_text(report, encoding="utf-8")
    record_environment(destination)
    names.extend([archive_name, "suite_report.md", "environment_requirements.txt"])
    if holdout is not None:
        names.extend(_copy_holdout(holdout, destination))
    manifest = {"artifacts": {
        name: hashlib.sha256((destination / name).read_bytes()).hexdigest() for name in sorted(names)
    }}
    # Include packaging code identity separately; it does not change simulated outcomes.
    manifest["packaging_script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (destination / "artifact_sha256.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                                     encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--holdout", type=Path)
    options = parser.parse_args()
    prepare_snapshot(options.source, options.destination, options.holdout)
    print(f"Prepared review evidence: {options.destination}")


if __name__ == "__main__":
    main()
