import json

import polars as pl
import pytest

from pcds.experiments import EXPERIMENTS, run_experiment_suite, validate_experiment_outputs
from pcds.paired_analysis import METRICS
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

    assert set(paths) == {"raw", "summary", "effects", "paired", "validation", "metadata", "report"}
    for path in paths.values():
        assert path.exists()

    raw = pl.read_csv(paths["raw"])
    summary = pl.read_csv(paths["summary"])
    effects = pl.read_csv(paths["effects"])
    validation = json.loads(paths["validation"].read_text(encoding="utf-8"))
    metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
    report = paths["report"].read_text(encoding="utf-8")

    assert raw.height == len(EXPERIMENTS) * len(VOTING_RULES) * 2
    assert summary.height == len(EXPERIMENTS) * len(VOTING_RULES)
    assert effects.height == len(EXPERIMENTS) * len(VOTING_RULES) * len(METRICS)
    paired = pl.read_csv(paths["paired"])
    assert paired.height == raw.height * len(METRICS)
    assert effects["n_pairs"].unique().to_list() == [2]
    assert effects["ci95_lower"].null_count() == 0
    assert effects["ci95_upper"].null_count() == 0
    assert validation["passed"] is True
    assert "runs is below 20" in validation["warnings"][0]
    assert "Validation status: **PASS**" in report
    assert "Outcome Dashboard" in report
    assert metadata["metric_schema"] == "separate-outcomes-v1"
    assert set(metadata["welfare_profiles"]) == {"survival_priority", "health_priority", "balanced"}
    assert metadata["randomness_scheme"] == "event-keyed-v1"
    assert metadata["paired_analysis"]["ci_method"] == "paired_percentile_bootstrap"
    assert set(metadata["runtime_versions"]) == {
        "python",
        "numpy",
        "networkx",
        "polars",
        "pydantic",
    }
    configurations = metadata["experiment_configurations"]
    assert configurations["fixed_preferences"]["parameters"]["decision"]["mode"] == "fixed"
    equal_accuracy = configurations["equal_accuracy"]["parameters"]["decision"]
    assert equal_accuracy["expert_accuracy"] == equal_accuracy["general_accuracy"]
    assert "final_assessment_error" in raw.columns
    assert "total_preference_changes" in raw.columns
    fixed_rows = raw.filter(pl.col("experiment") == "fixed_preferences")
    assert fixed_rows["total_preference_changes"].sum() == 0
    assert fixed_rows["final_assessment_error"].sum() == 0.0


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
    assert first_paths["summary"].read_text(encoding="utf-8") == second_paths["summary"].read_text(
        encoding="utf-8"
    )
    assert first_paths["effects"].read_text(encoding="utf-8") == second_paths["effects"].read_text(
        encoding="utf-8"
    )
    assert first_paths["paired"].read_text(encoding="utf-8") == second_paths["paired"].read_text(
        encoding="utf-8"
    )


def test_equal_accuracy_removes_authored_specialist_advantage():
    from pcds.experiments import _scenario_with_overrides
    from pcds.models import Role
    from pcds.scenarios import AgentSpec, load_scenario

    base = load_scenario(default_scenario_path())
    base.agents = [
        AgentSpec(name="farmer", role=Role.FARMER, general_accuracy=0.2, expert_accuracy=0.9)
    ]
    equal = _scenario_with_overrides(base, EXPERIMENTS["equal_accuracy"])
    assert equal.agents[0].expert_accuracy == equal.agents[0].general_accuracy == 0.2
    assert base.agents[0].expert_accuracy == 0.9


@pytest.fixture
def complete_artifact_frames():
    rows = [
        {
            "experiment": experiment,
            "rule": rule,
            "run_id": run_id,
            "seed": 42 + run_id,
            **{metric: 0.5 for metric in METRICS},
            **{
                f"final_{resource}": 10.0
                for resource in ["food", "water", "medicine", "energy", "security"]
            },
            "randomness_scheme": "event-keyed-v1",
            "metric_schema": "separate-outcomes-v1",
            "initial_population": 8,
            "final_survivors": 8,
            "final_eligible_voters": 8,
            "final_survival_rate": 1.0,
            "final_welfare_component_survival": 0.3,
            "final_welfare_component_health": 0.1,
            "final_welfare_component_resources": 0.1,
            "shock_count": 2,
            "environment_trace_digest": f"{run_id:064x}",
        }
        for experiment in EXPERIMENTS
        for rule in VOTING_RULES
        for run_id in range(2)
    ]
    summary = [
        {
            "experiment": experiment,
            "rule": rule,
            **{f"mean_{metric}": 0.5 for metric in METRICS},
            **{f"ci95_{metric}": 0.05 for metric in METRICS},
            **{f"n_{metric}": 2 for metric in METRICS},
        }
        for experiment in EXPERIMENTS
        for rule in VOTING_RULES
    ]
    return pl.DataFrame(rows), pl.DataFrame(summary)


def test_validation_rejects_unmatched_environmental_traces(complete_artifact_frames):
    raw, summary = complete_artifact_frames
    assert validate_experiment_outputs(raw, summary, runs=2, steps=40)["passed"]
    raw = raw.with_columns(
        pl.when((pl.col("experiment") == "moderate_scarcity") & (pl.col("rule") == "approval"))
        .then(pl.lit("f" * 64))
        .otherwise(pl.col("environment_trace_digest"))
        .alias("environment_trace_digest")
    )
    validation = validate_experiment_outputs(raw, summary, runs=2, steps=40)
    assert not validation["passed"]
    assert "paired rules have different environmental draw traces" in validation["errors"]


def test_validation_rejects_duplicate_pairs_despite_correct_row_count(complete_artifact_frames):
    raw, summary = complete_artifact_frames
    corrupted = pl.concat([raw.slice(1), raw.slice(1, 1)])
    assert corrupted.height == raw.height
    validation = validate_experiment_outputs(corrupted, summary, runs=2, steps=40)
    assert not validation["passed"]
    assert any("unique seed" in error for error in validation["errors"])


def test_validation_handles_null_metric_without_crashing(complete_artifact_frames):
    raw, summary = complete_artifact_frames
    raw = raw.with_columns(pl.lit(None, dtype=pl.Float64).alias("final_welfare"))
    assert not validate_experiment_outputs(raw, summary, runs=2, steps=40)["passed"]


def test_single_run_suite_reports_unavailable_intervals(tmp_path):
    paths = run_experiment_suite(default_scenario_path(), output_dir=tmp_path, runs=1, steps=2)
    validation = json.loads(paths["validation"].read_text(encoding="utf-8"))
    assert validation["passed"]
    assert any("fewer than 2 seed pairs" in warning for warning in validation["warnings"])
    summary = pl.read_csv(paths["summary"])
    effects = pl.read_csv(paths["effects"])
    assert all(summary[f"ci95_{metric}"].null_count() == summary.height for metric in METRICS)
    assert effects["ci95_lower"].null_count() == effects.height


def test_validation_rejects_health_means_for_an_absent_population(complete_artifact_frames):
    raw, summary = complete_artifact_frames
    corrupted = raw.with_columns(pl.lit(0).alias("final_survivors"))
    validation = validate_experiment_outputs(corrupted, summary, runs=2, steps=40)
    assert not validation["passed"]
    assert any("undefined exactly" in error for error in validation["errors"])


def test_validation_rejects_hidden_welfare_component_mismatch(complete_artifact_frames):
    raw, summary = complete_artifact_frames
    corrupted = raw.with_columns(pl.lit(0.0).alias("final_welfare_component_survival"))
    validation = validate_experiment_outputs(corrupted, summary, runs=2, steps=40)
    assert "welfare does not match its component contributions" in validation["errors"]
