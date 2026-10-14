"""Compare outcomes from the same trial before estimating uncertainty.

Resample seed-level differences; members within one community are not independent trials.
"""

from __future__ import annotations

import math

import numpy as np
import polars as pl

from pcds.metric_definitions import METRIC_DIRECTIONS, METRICS, NULLABLE_METRICS
from pcds.randomness import event_rng

PAIR_KEYS = ["experiment", "run_id", "seed"]
BOOTSTRAP_RESAMPLES = 2000
CI_METHOD = "paired_percentile_bootstrap"


def pairing_errors(raw: pl.DataFrame, baseline_rule: str = "majority") -> list[str]:
    """Check that every compared seed has a unique matched baseline row.

    Undefined conditional outcomes are allowed; missing simulation rows are not.
    """
    required = {*PAIR_KEYS, "rule", *METRICS}
    missing = sorted(required - set(raw.columns))
    if missing:
        return [f"pairing is missing required columns: {missing}"]
    if raw.is_empty():
        return ["pairing requires non-empty raw results"]
    nonnullable = required - NULLABLE_METRICS
    # A blank survivor mean is legitimate after extinction; a missing seed/run
    # identifier is not. Never confuse these two reasons for absent information.
    if any(raw[column].null_count() for column in nonnullable):
        return ["pairing keys and metrics cannot contain null values"]
    if any(
        not isinstance(value, int | float) or not math.isfinite(value)
        for metric in METRICS
        for value in raw[metric]
        if value is not None
    ):
        return ["paired metrics must be finite numbers"]
    for identity in ("seed", "run_id"):
        if raw.select(["experiment", "rule", identity]).is_duplicated().any():
            return [f"pairing requires unique {identity} per experiment and rule"]
    errors: list[str] = []
    if "physics_schema" in raw.columns:
        # Old files lack this field. If present, require one complete version
        # per condition so identical draw digests cannot hide changed mechanics.
        versions = raw.group_by("experiment").agg(
            pl.col("physics_schema").n_unique().alias("versions")
        )
        if raw["physics_schema"].null_count() or versions.filter(pl.col("versions") != 1).height:
            errors.append("paired rules have different or missing physics schemas")
    if "environment_trace_digest" in raw.columns:
        traces = raw.group_by(PAIR_KEYS).agg(
            pl.col("environment_trace_digest").n_unique().alias("trace_count")
        )
        if traces.filter(pl.col("trace_count") != 1).height:
            errors.append("paired rules have different environmental draw traces")
    for (experiment,), frame in raw.partition_by("experiment", as_dict=True).items():
        baseline = frame.filter(pl.col("rule") == baseline_rule)
        if baseline.is_empty():
            errors.append(f"experiment {experiment!r} has no {baseline_rule!r} baseline")
            continue
        baseline_keys = set(baseline.select(PAIR_KEYS).iter_rows())
        for (rule,), candidate in frame.partition_by("rule", as_dict=True).items():
            if set(candidate.select(PAIR_KEYS).iter_rows()) != baseline_keys:
                errors.append(
                    f"experiment {experiment!r}, rule {rule!r} has mismatched seed/run pairs"
                )
    return errors


def build_paired_differences(raw: pl.DataFrame, baseline_rule: str = "majority") -> pl.DataFrame:
    """Subtract the baseline outcome within each experiment/run/seed pair.

    Keep undefined conditional differences as missing values with their seed rows intact.
    """
    errors = pairing_errors(raw, baseline_rule)
    if errors:
        raise ValueError("; ".join(errors))
    baseline = raw.filter(pl.col("rule") == baseline_rule).select(
        *PAIR_KEYS, *[pl.col(metric).alias(f"baseline_{metric}") for metric in METRICS]
    )
    matched = raw.join(baseline, on=PAIR_KEYS, how="left", validate="m:1")
    frames = []
    for metric in METRICS:
        # Subtract within a seed first; independent rule-level intervals do
        # not account for covariance induced by shared initial/external draws.
        frames.append(
            matched.select(
                *PAIR_KEYS,
                "rule",
                pl.lit(metric).alias("metric"),
                pl.lit(baseline_rule).alias("baseline_rule"),
                pl.col(f"baseline_{metric}").alias("baseline_value"),
                pl.col(metric).alias("rule_value"),
                (pl.col(metric) - pl.col(f"baseline_{metric}")).alias("difference"),
            )
        )
    return pl.concat(frames).sort(["experiment", "rule", "metric", "seed"])


def _bootstrap_interval(
    differences: np.ndarray, rng: np.random.Generator, resamples: int
) -> tuple[float | None, float | None]:
    """Resample seed-level differences to estimate uncertainty in their average.

    Return no interval when fewer than two defined pairs are available.
    """
    if len(differences) < 2:
        # One observed difference cannot estimate sampling uncertainty.
        return None, None
    # Resample seed-level differences together. Batches bound temporary memory
    # even when reviewers request many replications or bootstrap draws.
    means = np.empty(resamples)
    for start in range(0, resamples, 256):
        count = min(256, resamples - start)
        draws = rng.choice(differences, size=(count, len(differences)), replace=True)
        means[start : start + count] = draws.mean(axis=1)
    lower, upper = np.quantile(means, [0.025, 0.975])
    return float(lower), float(upper)


def summarize_paired_effects(
    paired: pl.DataFrame, seed: int = 42, resamples: int = BOOTSTRAP_RESAMPLES
) -> pl.DataFrame:
    """Report signed mean differences, paired variation, intervals, and usable coverage."""
    if resamples < 2:
        raise ValueError("bootstrap resamples must be at least 2")
    groups = paired.partition_by(["experiment", "rule", "metric"], as_dict=True)
    rows = [_summarize_pair_group(frame, seed, resamples) for _, frame in sorted(groups.items())]
    return pl.DataFrame(
        rows,
        schema_overrides={
            "absolute_delta": pl.Float64,
            "baseline_mean": pl.Float64,
            "rule_mean": pl.Float64,
            "paired_std": pl.Float64,
            "paired_standard_error": pl.Float64,
            "ci95_lower": pl.Float64,
            "ci95_upper": pl.Float64,
        },
    )


def _summarize_pair_group(frame: pl.DataFrame, seed: int, resamples: int) -> dict:
    """Estimate one metric's rule-versus-baseline effect using the same defined pairs.

    Conditional subsets are identified explicitly; their selection can depend on the rules.
    """
    experiment, rule, metric = frame.select("experiment", "rule", "metric").row(0)
    frame = frame.sort("seed")
    baseline_rule = frame["baseline_rule"][0]
    # Undefined conditional outcomes retain their rows in the paired export.
    # The estimand is explicitly restricted to pairs defined in both rules.
    total_pairs = frame.height
    frame = frame.filter(pl.col("difference").is_not_null())
    differences = frame["difference"].to_numpy()
    # Key inference independently so ordering experiments cannot change CIs.
    bootstrap_seed = event_rng(seed, "paired_bootstrap", 0, experiment, rule, metric).getrandbits(
        64
    )
    lower, upper = _bootstrap_interval(
        differences, np.random.default_rng(bootstrap_seed), resamples
    )
    deviation = float(np.std(differences, ddof=1)) if len(differences) > 1 else None
    return {
        "experiment": experiment,
        "rule": rule,
        "metric": metric,
        "baseline_rule": baseline_rule,
        "baseline_mean": frame["baseline_value"].mean(),
        "rule_mean": frame["rule_value"].mean(),
        # Retain the existing column name: absolute means additive units,
        # not abs(difference); a negative delta must retain its sign.
        "absolute_delta": float(np.mean(differences)) if len(differences) else None,
        "n_pairs": len(differences),
        "n_seed_pairs": total_pairs,
        "n_undefined_pairs": total_pairs - len(differences),
        "estimand": "defined_pairs_only" if metric in NULLABLE_METRICS else "all_seed_pairs",
        "preferred_direction": METRIC_DIRECTIONS[metric],
        "paired_std": deviation,
        "paired_standard_error": deviation / math.sqrt(len(differences))
        if deviation is not None
        else None,
        "ci95_lower": lower,
        "ci95_upper": upper,
        "ci_method": CI_METHOD,
        "bootstrap_resamples": resamples,
    }
