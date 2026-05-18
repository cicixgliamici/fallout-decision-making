from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from pcds.models import EnvironmentalShock, Role
from pcds.scenarios import Scenario, load_scenario
from pcds.simulation import compare_rules
from pcds.voting import VOTING_RULES


EXPERIMENTS: dict[str, dict] = {
    "moderate_scarcity": {},
    "severe_scarcity": {
        "food_consumption": 1.05,
        "water_consumption": 0.95,
        "medicine_consumption": 0.12,
    },
    "environmental_shocks": {
        "shock": EnvironmentalShock(
            probability=0.18,
            food_loss=12.0,
            water_loss=10.0,
            medicine_loss=4.0,
            security_loss=6.0,
            health_damage=0.025,
        )
    },
    "low_trust": {"trust_probability": 0.08, "trust_topology": "sparse"},
    "high_trust": {"trust_probability": 0.35, "trust_topology": "dense"},
    "expertise_imbalance": {
        "role_distribution": {
            "doctor": 0.08,
            "farmer": 0.42,
            "engineer": 0.08,
            "guard": 0.08,
            "scavenger": 0.26,
            "elder": 0.08,
        }
    },
}

METRICS: tuple[str, ...] = (
    "final_survival_rate",
    "final_welfare",
    "final_inequality",
    "final_resilience",
)

RAW_REQUIRED_COLUMNS: tuple[str, ...] = (
    "experiment",
    "rule",
    "run_id",
    "seed",
    *METRICS,
    "final_food",
    "final_water",
    "final_medicine",
    "final_energy",
    "final_security",
)


def run_experiment_suite(
    scenario_path: str | Path,
    output_dir: str | Path = "results",
    runs: int = 100,
    steps: int = 40,
    seed: int = 42,
) -> dict[str, Path]:
    """Run the predefined robustness scenarios and write reviewer-facing outputs."""
    if runs <= 0:
        raise ValueError("runs must be greater than zero")
    if steps <= 0:
        raise ValueError("steps must be greater than zero")

    base = load_scenario(scenario_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    raw_frames: list[pl.DataFrame] = []
    summary_frames: list[pl.DataFrame] = []

    for experiment_name, overrides in EXPERIMENTS.items():
        scenario = _scenario_with_overrides(base, overrides)
        df = compare_rules(runs=runs, steps=steps, seed=seed, scenario=scenario)
        df = df.with_columns(pl.lit(experiment_name).alias("experiment"))
        raw_frames.append(df)
        summary_frames.append(_summarize(df).with_columns(pl.lit(experiment_name).alias("experiment")))

    raw = pl.concat(raw_frames)
    summary = pl.concat(summary_frames)
    effects = _pairwise_effects(summary)
    validation = validate_experiment_outputs(raw, summary, runs=runs, steps=steps)

    raw_path = output / "suite_raw.csv"
    summary_path = output / "suite_summary.csv"
    effects_path = output / "suite_effects_vs_majority.csv"
    validation_path = output / "suite_validation.json"
    metadata_path = output / "suite_metadata.json"
    report_path = output / "suite_report.md"

    raw.write_csv(raw_path)
    summary.write_csv(summary_path)
    effects.write_csv(effects_path)
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    metadata_path.write_text(
        json.dumps(
            {
                "created_at": datetime.now(UTC).isoformat(),
                "scenario": str(scenario_path),
                "runs": runs,
                "steps": steps,
                "seed": seed,
                "experiments": list(EXPERIMENTS),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report_path.write_text(_markdown_report(summary, effects, validation), encoding="utf-8")

    return {
        "raw": raw_path,
        "summary": summary_path,
        "effects": effects_path,
        "validation": validation_path,
        "metadata": metadata_path,
        "report": report_path,
    }


def validate_experiment_outputs(
    raw: pl.DataFrame,
    summary: pl.DataFrame,
    runs: int,
    steps: int,
) -> dict:
    """Validate suite outputs before interpreting them as artifact evidence."""
    errors: list[str] = []
    warnings: list[str] = []

    expected_experiments = set(EXPERIMENTS)
    expected_rules = set(VOTING_RULES)
    expected_raw_rows = len(expected_experiments) * len(expected_rules) * runs
    expected_summary_rows = len(expected_experiments) * len(expected_rules)

    missing_raw = sorted(set(RAW_REQUIRED_COLUMNS) - set(raw.columns))
    if missing_raw:
        errors.append(f"raw output is missing required columns: {missing_raw}")

    summary_required = {"experiment", "rule"} | {
        column for metric in METRICS for column in (f"mean_{metric}", f"ci95_{metric}")
    }
    missing_summary = sorted(summary_required - set(summary.columns))
    if missing_summary:
        errors.append(f"summary output is missing required columns: {missing_summary}")

    if raw.height != expected_raw_rows:
        errors.append(f"raw output has {raw.height} rows, expected {expected_raw_rows}")
    if summary.height != expected_summary_rows:
        errors.append(f"summary output has {summary.height} rows, expected {expected_summary_rows}")

    if "experiment" in raw.columns:
        observed = set(raw["experiment"].unique().to_list())
        if observed != expected_experiments:
            errors.append(f"raw experiments are {sorted(observed)}, expected {sorted(expected_experiments)}")
    if "rule" in raw.columns:
        observed = set(raw["rule"].unique().to_list())
        if observed != expected_rules:
            errors.append(f"raw rules are {sorted(observed)}, expected {sorted(expected_rules)}")

    for column in [c for c in RAW_REQUIRED_COLUMNS if c in raw.columns]:
        null_count = raw.select(pl.col(column).null_count()).item()
        if null_count:
            errors.append(f"raw column {column!r} contains {null_count} null values")

    for column in [c for c in raw.columns if c.startswith("final_")]:
        values = raw[column].to_list()
        if any(not _is_finite_number(value) for value in values):
            errors.append(f"raw column {column!r} contains non-finite values")

    _require_range(raw, "final_survival_rate", lower=0.0, upper=1.0, errors=errors)
    _require_range(raw, "final_inequality", lower=0.0, upper=1.0, errors=errors)
    for column in (
        "final_welfare",
        "final_resilience",
        "final_food",
        "final_water",
        "final_medicine",
        "final_energy",
        "final_security",
    ):
        _require_range(raw, column, lower=0.0, upper=None, errors=errors)

    for column in [c for c in summary.columns if c.startswith("ci95_")]:
        _require_range(summary, column, lower=0.0, upper=None, errors=errors)

    if runs < 20:
        warnings.append("runs is below 20; use larger runs for presentation-quality confidence intervals")
    if steps < 20:
        warnings.append("steps is below 20; short runs are useful for smoke tests, not result claims")

    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "checks": {
            "expected_raw_rows": expected_raw_rows,
            "observed_raw_rows": raw.height,
            "expected_summary_rows": expected_summary_rows,
            "observed_summary_rows": summary.height,
            "experiments": sorted(expected_experiments),
            "rules": sorted(expected_rules),
            "runs": runs,
            "steps": steps,
        },
    }


def _scenario_with_overrides(base: Scenario, overrides: dict) -> Scenario:
    scenario = base.model_copy(deep=True)
    for key, value in overrides.items():
        # Experiments modify either simulation parameters or top-level scenario
        # controls while keeping the base scenario intact for the next run.
        if hasattr(scenario.parameters, key):
            setattr(scenario.parameters, key, value)
        elif key == "role_distribution":
            scenario.role_distribution = {Role(role): weight for role, weight in value.items()}
        else:
            setattr(scenario, key, value)
    return scenario


def _summarize(df: pl.DataFrame) -> pl.DataFrame:
    expressions = []
    for metric in METRICS:
        expressions.extend(
            [
                pl.col(metric).mean().alias(f"mean_{metric}"),
                (
                    1.96
                    * pl.col(metric).std().fill_null(0.0)
                    / pl.len().sqrt()
                ).alias(f"ci95_{metric}"),
            ]
        )
    return df.group_by("rule").agg(expressions).sort(
        ["mean_final_welfare", "rule"],
        descending=[True, False],
    )


def _pairwise_effects(summary: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict] = []
    for experiment in summary["experiment"].unique().sort():
        experiment_summary = summary.filter(pl.col("experiment") == experiment)
        baseline = experiment_summary.filter(pl.col("rule") == "majority")
        if baseline.is_empty():
            continue
        for row in experiment_summary.iter_rows(named=True):
            for metric in METRICS:
                # Majority is the direct-voting baseline used in the research
                # question, so each other rule is reported as a delta from it.
                baseline_mean = baseline.select(pl.col(f"mean_{metric}")).item()
                rule_mean = row[f"mean_{metric}"]
                rows.append(
                    {
                        "experiment": experiment,
                        "rule": row["rule"],
                        "metric": metric,
                        "baseline_rule": "majority",
                        "baseline_mean": baseline_mean,
                        "rule_mean": rule_mean,
                        "absolute_delta": rule_mean - baseline_mean,
                    }
                )
    return pl.DataFrame(rows)


def _markdown_report(summary: pl.DataFrame, effects: pl.DataFrame, validation: dict) -> str:
    validation_status = "PASS" if validation["passed"] else "FAIL"
    lines = [
        "# Experiment Suite Report",
        "",
        "Each row reports rule-level means and approximate 95% confidence intervals.",
        "",
        f"Validation status: **{validation_status}**",
        "",
        "## Summary",
        "",
        summary.write_csv(),
        "",
        "## Effects vs Majority Baseline",
        "",
        effects.write_csv(),
        "",
        "## Validation",
        "",
        json.dumps(validation, indent=2),
    ]
    return "\n".join(lines)


def _require_range(
    df: pl.DataFrame,
    column: str,
    lower: float,
    upper: float | None,
    errors: list[str],
) -> None:
    if column not in df.columns:
        return
    values = df[column].to_list()
    below = sum(1 for value in values if value < lower)
    if below:
        errors.append(f"column {column!r} has {below} values below {lower}")
    if upper is not None:
        above = sum(1 for value in values if value > upper)
        if above:
            errors.append(f"column {column!r} has {above} values above {upper}")


def _is_finite_number(value: object) -> bool:
    return isinstance(value, int | float) and math.isfinite(float(value))
