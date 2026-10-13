"""Run predefined conditions and turn checked outcomes into reviewable evidence.

Validation guards data consistency; model validity still needs a separate research argument.
"""

from __future__ import annotations

import json
import math
import platform
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import polars as pl

from pcds.metric_definitions import METRIC_DIRECTIONS, METRIC_SCHEMA, NULLABLE_METRICS
from pcds.metrics import WELFARE_PROFILES
from pcds.models import EnvironmentalShock, Role
from pcds.paired_analysis import (
    BOOTSTRAP_RESAMPLES,
    CI_METHOD,
    METRICS,
    build_paired_differences,
    pairing_errors,
    summarize_paired_effects,
)
from pcds.randomness import RANDOMNESS_SCHEME
from pcds.scenarios import Scenario, load_scenario
from pcds.simulation import compare_rules
from pcds.voting import VOTING_RULES

EXPERIMENTS: dict[str, dict] = {
    "moderate_scarcity": {},
    "fixed_preferences": {"decision_mode": "fixed"},
    "equal_accuracy": {"equal_accuracy": True},
    "severe_scarcity": {
        "food_consumption": 1.05,
        "water_consumption": 0.95,
        "medicine_consumption": 0.12,
    },
    "environmental_shocks": {
        "shock": EnvironmentalShock(
            # Keep this stress condition stronger than the revised baseline
            # (0.22), so the suite does not repeat an identical scenario.
            probability=0.30,
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
    "environment_trace_digest",
    "randomness_scheme",
    "shock_count",
    "initial_population",
    "final_survivors",
    "final_eligible_voters",
    "final_welfare_component_survival",
    "final_welfare_component_health",
    "final_welfare_component_resources",
    "metric_schema",
)


def run_experiment_suite(
    scenario_path: str | Path,
    output_dir: str | Path = "results",
    runs: int = 100,
    steps: int = 40,
    seed: int = 42,
) -> dict[str, Path]:
    """Run predefined scarcity, information, and trust conditions on matching seeds.

    Write raw observations, paired differences, summaries, metadata, and an English
    report only after consistency checks succeed.
    """
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
        summary_frames.append(
            summarize_rules(df).with_columns(pl.lit(experiment_name).alias("experiment"))
        )

    raw = pl.concat(raw_frames)
    # Keep one observation per rule and seed until differences are matched.
    # Matching averages instead would lose the shared-trial variation.
    summary = pl.concat(summary_frames)
    validation = validate_experiment_outputs(raw, summary, runs=runs, steps=steps)
    if not validation["passed"]:
        raise ValueError("Invalid experiment outputs: " + "; ".join(validation["errors"]))
    paired = build_paired_differences(raw)
    effects = summarize_paired_effects(paired, seed=seed)

    raw_path = output / "suite_raw.csv"
    summary_path = output / "suite_summary.csv"
    effects_path = output / "suite_effects_vs_majority.csv"
    paired_path = output / "suite_paired_differences.csv"
    validation_path = output / "suite_validation.json"
    metadata_path = output / "suite_metadata.json"
    report_path = output / "suite_report.md"

    raw.write_csv(raw_path)
    summary.write_csv(summary_path)
    effects.write_csv(effects_path)
    paired.write_csv(paired_path)
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    metadata_path.write_text(
        json.dumps(
            {
                "created_at": datetime.now(UTC).isoformat(),
                "scenario": str(scenario_path),
                "runs": runs,
                "steps": steps,
                "seed": seed,
                "randomness_scheme": RANDOMNESS_SCHEME,
                "metric_schema": METRIC_SCHEMA,
                "metric_directions": METRIC_DIRECTIONS,
                "conditional_metrics": sorted(NULLABLE_METRICS),
                "conditional_estimand": "mean difference among seed pairs defined in both rules",
                "welfare_profiles": {
                    name: weights.model_dump() for name, weights in WELFARE_PROFILES.items()
                },
                # Bootstrap/PRNG implementations can change between releases;
                # record the runtime needed to reproduce the exported intervals.
                "runtime_versions": {
                    "python": platform.python_version(),
                    **{
                        package: version(package)
                        for package in ("numpy", "networkx", "polars", "pydantic")
                    },
                },
                "paired_analysis": {
                    "baseline_rule": "majority",
                    "pair_keys": ["experiment", "run_id", "seed"],
                    "ci_method": CI_METHOD,
                    "confidence_level": 0.95,
                    "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
                    "bootstrap_seed": seed,
                },
                "experiments": list(EXPERIMENTS),
                "scenario_configuration": base.model_dump(mode="json"),
                "experiment_configurations": {
                    name: _scenario_with_overrides(base, overrides).model_dump(mode="json")
                    for name, overrides in EXPERIMENTS.items()
                },
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
        "paired": paired_path,
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
    """Check coverage, pairing, numeric bounds, and outcome-population consistency.

    Passing means the exported data meet these checks, not that the model is empirically valid.
    """
    errors: list[str] = []
    warnings: list[str] = []

    expected_experiments = set(EXPERIMENTS)
    expected_rules = set(VOTING_RULES)
    expected_raw_rows = len(expected_experiments) * len(expected_rules) * runs
    expected_summary_rows = len(expected_experiments) * len(expected_rules)

    missing_raw = sorted(set(RAW_REQUIRED_COLUMNS) - set(raw.columns))
    if missing_raw:
        errors.append(f"raw output is missing required columns: {missing_raw}")
    errors.extend(pairing_errors(raw))
    if "randomness_scheme" in raw.columns and set(raw["randomness_scheme"].to_list()) != {
        RANDOMNESS_SCHEME
    }:
        errors.append("raw output uses an unsupported randomness scheme")
    if "metric_schema" in raw.columns and set(raw["metric_schema"].to_list()) != {METRIC_SCHEMA}:
        errors.append("raw output uses an unsupported metric schema")

    summary_required = {"experiment", "rule"} | {
        column
        for metric in METRICS
        for column in (f"mean_{metric}", f"ci95_{metric}", f"n_{metric}")
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
            errors.append(
                f"raw experiments are {sorted(observed)}, expected {sorted(expected_experiments)}"
            )
    if "rule" in raw.columns:
        observed = set(raw["rule"].unique().to_list())
        if observed != expected_rules:
            errors.append(f"raw rules are {sorted(observed)}, expected {sorted(expected_rules)}")

    for column in [c for c in RAW_REQUIRED_COLUMNS if c in raw.columns]:
        null_count = raw.select(pl.col(column).null_count()).item()
        if null_count and column not in NULLABLE_METRICS:
            errors.append(f"raw column {column!r} contains {null_count} null values")

    if {"experiment", "rule"} <= set(raw.columns):
        counts = raw.group_by(["experiment", "rule"]).len()
        expected_groups = {
            (experiment, rule) for experiment in expected_experiments for rule in expected_rules
        }
        observed_groups = set(counts.select("experiment", "rule").iter_rows())
        if observed_groups != expected_groups:
            errors.append("raw output does not contain every experiment/rule combination")
        if counts.filter(pl.col("len") != runs).height:
            errors.append("raw experiment/rule groups do not all have the requested number of runs")

    for column in [c for c in raw.columns if c.startswith("final_")]:
        values = raw[column].to_list()
        if any(
            not _is_finite_number(value)
            for value in values
            if value is not None or column not in NULLABLE_METRICS
        ):
            errors.append(f"raw column {column!r} contains non-finite values")

    _require_range(raw, "final_survival_rate", lower=0.0, upper=1.0, errors=errors)
    _require_range(raw, "final_inequality", lower=0.0, upper=1.0, errors=errors)
    for metric in METRICS:
        if metric == "final_resilience":
            continue
        _require_range(
            raw, metric, lower=0.0, upper=1.0, errors=errors, allow_null=metric in NULLABLE_METRICS
        )
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
        count_column = "n_" + column.removeprefix("ci95_")
        if count_column in summary.columns:
            required_intervals = summary.filter(pl.col(count_column) >= 2)
            _require_range(required_intervals, column, lower=0.0, upper=None, errors=errors)
    _require_range(raw, "shock_count", lower=0.0, upper=float(steps), errors=errors)
    errors.extend(_population_metric_errors(raw))

    if runs < 20:
        warnings.append(
            "runs is below 20; use larger runs for presentation-quality confidence intervals"
        )
    if runs < 2:
        warnings.append("fewer than 2 seed pairs; paired confidence intervals are unavailable")
    if steps < 20:
        warnings.append(
            "steps is below 20; short runs are useful for smoke tests, not result claims"
        )

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


def _population_metric_errors(raw: pl.DataFrame) -> list[str]:
    """Check denominators, legitimate absences, and the stated welfare decomposition.

    Conditional averages cannot exist when their relevant population has disappeared.
    """
    required = {"initial_population", "final_survivors", "final_eligible_voters", *METRICS}
    components = [f"final_welfare_component_{name}" for name in ("survival", "health", "resources")]
    if not required.union(components) <= set(raw.columns):
        return []
    errors: set[str] = set()
    for row in raw.iter_rows(named=True):
        # Original population, end-of-round survivors, and decision-time voters
        # are different counts; each metric must use its declared denominator.
        population, survivors, voters = (
            row[name] for name in ("initial_population", "final_survivors", "final_eligible_voters")
        )
        if (
            not all(isinstance(value, int) for value in (population, survivors, voters))
            or population < 1
            or not (0 <= survivors <= population and 0 <= voters <= population)
        ):
            errors.add("population and electorate counts must be valid integers")
            continue
        for metric in NULLABLE_METRICS:
            count = survivors if metric == "final_survivor_health" else voters
            if (row[metric] is None) != (count == 0):
                errors.add(f"{metric} must be undefined exactly when its population is empty")
        if _is_finite_number(row["final_survival_rate"]) and not math.isclose(
            row["final_survival_rate"], survivors / population, abs_tol=1e-12
        ):
            errors.add("survival rate does not match survivor/population counts")
        health = row["final_survivor_health"]
        expected_health = survivors / population * health if _is_finite_number(health) else 0.0
        if _is_finite_number(row["final_population_health"]) and not math.isclose(
            row["final_population_health"], expected_health, abs_tol=1e-12
        ):
            errors.add("population health does not match survival and survivor health")
        if all(_is_finite_number(row[name]) for name in [*components, "final_welfare"]):
            if not math.isclose(
                sum(row[name] for name in components), row["final_welfare"], abs_tol=1e-12
            ):
                errors.add("welfare does not match its component contributions")
        for metric in ["final_welfare", *[f"final_welfare_{name}" for name in WELFARE_PROFILES]]:
            if _is_finite_number(row[metric]) and row[metric] > survivors / population + 1e-12:
                errors.add("survival-gated welfare cannot exceed the survival rate")
    return sorted(errors)


def _scenario_with_overrides(base: Scenario, overrides: dict) -> Scenario:
    """Make an independent scenario for one condition, leaving the baseline unchanged."""
    scenario = base.model_copy(deep=True)
    for key, value in overrides.items():
        # Experiments modify either simulation parameters or top-level scenario
        # controls while keeping the base scenario intact for the next run.
        if key == "decision_mode":
            scenario.parameters.decision.mode = value
        elif key == "equal_accuracy":
            # Remove the specialist advantage without changing trust or roles.
            scenario.parameters.decision.expert_accuracy = (
                scenario.parameters.decision.general_accuracy
            )
            if isinstance(scenario.agents, list):
                for agent in scenario.agents:
                    general = agent.general_accuracy
                    agent.expert_accuracy = (
                        general
                        if general is not None
                        else scenario.parameters.decision.general_accuracy
                    )
        elif hasattr(scenario.parameters, key):
            setattr(scenario.parameters, key, value)
        elif key == "role_distribution":
            scenario.role_distribution = {Role(role): weight for role, weight in value.items()}
        else:
            setattr(scenario, key, value)
    return scenario


def summarize_rules(df: pl.DataFrame) -> pl.DataFrame:
    """Summarize rule-level outcomes with counts of defined values and descriptive intervals.

    These separate-rule intervals are not confidence intervals on paired differences.
    """
    expressions = []
    for metric in METRICS:
        expressions.extend(
            [
                pl.col(metric).mean().alias(f"mean_{metric}"),
                pl.col(metric).count().alias(f"n_{metric}"),
                (1.96 * pl.col(metric).std() / pl.col(metric).count().sqrt()).alias(
                    f"ci95_{metric}"
                ),
            ]
        )
    return (
        df.group_by("rule")
        .agg(expressions)
        .sort(
            ["mean_final_welfare", "rule"],
            descending=[True, False],
        )
    )


def _markdown_report(summary: pl.DataFrame, effects: pl.DataFrame, validation: dict) -> str:
    """Build an English report that keeps material outcomes, representation, and coverage visible."""
    validation_status = "PASS" if validation["passed"] else "FAIL"
    lines = [
        "# Experiment Suite Report",
        "",
        "Each row reports rule-level means and approximate 95% confidence intervals.",
        "Effects use matched experiment/run/seed differences with approximate 95% percentile bootstrap intervals (2,000 resamples).",
        "Intervals are unavailable with fewer than two defined pairs. Metric directions are recorded in `preferred_direction`; delegated vote share is descriptive.",
        "Conditional outcomes are undefined without survivors/voters. Effects report `n_pairs`, `n_seed_pairs`, and `n_undefined_pairs`; conditional estimates concern only pairs defined in both rules.",
        "Read survival, health, satisfaction, and ballot concentration together. Low health dispersion or low concentration alone cannot establish a good outcome.",
        "Welfare weights express normative priorities. Contributions and three prespecified sensitivity profiles are exported separately; satisfaction and power are not folded into the index.",
        "",
        f"Validation status: **{validation_status}**",
        "",
        "## Outcome Dashboard",
        "",
        _outcome_dashboard(summary),
        "",
        "## Summary",
        "",
        "```csv\n" + summary.write_csv() + "```",
        "",
        "## Paired Effects vs Majority Baseline",
        "",
        "```csv\n" + effects.write_csv() + "```",
        "",
        "Per-seed differences are stored in `suite_paired_differences.csv`.",
        "These intervals describe sampling uncertainty within the model, not validity of its assumptions or simultaneous coverage across comparisons.",
        "",
        "## Validation",
        "",
        "```json\n" + json.dumps(validation, indent=2) + "\n```",
    ]
    return "\n".join(lines)


def _outcome_dashboard(summary: pl.DataFrame) -> str:
    """Present related outcomes side by side, including counts for conditional means."""
    columns = [
        "final_survival_rate",
        "final_population_health",
        "final_survivor_health",
        "final_preference_satisfaction",
        "final_prior_preference_satisfaction",
        "final_delegation_concentration",
        "final_welfare",
    ]
    lines = [
        "| Experiment | Rule | Survival | Population health | Survivor health (n) | Current satisfaction (n) | Initial satisfaction (n) | Concentration (n) | Welfare |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary.sort(["experiment", "rule"]).iter_rows(named=True):
        cells = [row["experiment"], row["rule"]]
        for metric in columns:
            value = row[f"mean_{metric}"]
            cell = "N/A" if value is None else f"{value:.3f}"
            if metric in NULLABLE_METRICS:
                cell += f" ({row[f'n_{metric}']})"
            cells.append(cell)
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _require_range(
    df: pl.DataFrame,
    column: str,
    lower: float,
    upper: float | None,
    errors: list[str],
    allow_null: bool = False,
) -> None:
    """Flag invalid numeric values while allowing explicitly undefined conditional measures."""
    if column not in df.columns:
        return
    observed = df[column].to_list()
    if any(
        not _is_finite_number(value) for value in observed if value is not None or not allow_null
    ):
        errors.append(f"column {column!r} contains null or non-finite values")
    values = [value for value in observed if _is_finite_number(value)]
    # Permit only floating-point roundoff at mathematical unit boundaries.
    below = sum(1 for value in values if value < lower - 1e-12)
    if below:
        errors.append(f"column {column!r} has {below} values below {lower}")
    if upper is not None:
        above = sum(1 for value in values if value > upper + 1e-12)
        if above:
            errors.append(f"column {column!r} has {above} values above {upper}")


def _is_finite_number(value: object) -> bool:
    """Exclude missing values, infinities, and invalid numbers from numeric checks."""
    return isinstance(value, int | float) and math.isfinite(float(value))
