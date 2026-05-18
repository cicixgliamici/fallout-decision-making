import json

import polars as pl
import pytest

from pcds.experiments import EXPERIMENTS, run_experiment_suite, validate_experiment_outputs
from pcds.scenarios import default_scenario_path
from pcds.voting import VOTING_RULES


def test_experiment_suite_writes_validated_outputs(tmp_path):
    paths = run_experiment_suite(
        scenario_path=default_scenario_path(),
        output_dir=tmp_path,
        runs=2,
        steps=2,
        seed=7,
    )

    assert set(paths) == {"raw", "summary", "effects", "validation", "metadata", "report"}
    for path in paths.values():
        assert path.exists()

    raw = pl.read_csv(paths["raw"])
    summary = pl.read_csv(paths["summary"])
    effects = pl.read_csv(paths["effects"])
    validation = json.loads(paths["validation"].read_text(encoding="utf-8"))
    report = paths["report"].read_text(encoding="utf-8")

    assert raw.height == len(EXPERIMENTS) * len(VOTING_RULES) * 2
    assert summary.height == len(EXPERIMENTS) * len(VOTING_RULES)
    assert effects.height == len(EXPERIMENTS) * len(VOTING_RULES) * 4
    assert validation["passed"] is True
    assert "runs is below 20" in validation["warnings"][0]
    assert "Validation status: **PASS**" in report


def test_validate_experiment_outputs_rejects_missing_required_columns():
    raw = pl.DataFrame(
        {
            "experiment": ["moderate_scarcity"],
            "rule": ["majority"],
            "run_id": [0],
            "seed": [42],
        }
    )
    summary = pl.DataFrame({"experiment": ["moderate_scarcity"], "rule": ["majority"]})

    validation = validate_experiment_outputs(raw, summary, runs=1, steps=1)

    assert validation["passed"] is False
    assert any("missing required columns" in error for error in validation["errors"])


def test_experiment_suite_rejects_non_positive_runs(tmp_path):
    with pytest.raises(ValueError, match="runs must be greater than zero"):
        run_experiment_suite(default_scenario_path(), output_dir=tmp_path, runs=0, steps=1)


def test_suite_outputs_are_reproducible_for_same_seed(tmp_path):
    first_paths = run_experiment_suite(
        scenario_path=default_scenario_path(),
        output_dir=tmp_path / "first",
        runs=2,
        steps=3,
        seed=11,
    )
    second_paths = run_experiment_suite(
        scenario_path=default_scenario_path(),
        output_dir=tmp_path / "second",
        runs=2,
        steps=3,
        seed=11,
    )

    assert first_paths["raw"].read_text(encoding="utf-8") == second_paths["raw"].read_text(
        encoding="utf-8"
    )
    assert first_paths["summary"].read_text(encoding="utf-8") == second_paths[
        "summary"
    ].read_text(encoding="utf-8")
    assert first_paths["effects"].read_text(encoding="utf-8") == second_paths[
        "effects"
    ].read_text(encoding="utf-8")
