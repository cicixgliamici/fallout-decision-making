import math

import polars as pl
import pytest

from pcds.paired_analysis import METRICS, build_paired_differences, summarize_paired_effects


def make_raw(differences=(0.1, 0.1, 0.1)):
    rows = []
    for run_id, difference in enumerate(differences):
        baseline = 0.1 + run_id * 0.3
        for rule, value in [("majority", baseline), ("approval", baseline + difference)]:
            rows.append(
                {
                    "experiment": "test",
                    "rule": rule,
                    "run_id": run_id,
                    "seed": 42 + run_id,
                    **{metric: value for metric in METRICS},
                }
            )
    return pl.DataFrame(rows)


def approval_effects(raw):
    paired = build_paired_differences(raw)
    return summarize_paired_effects(paired).filter(pl.col("rule") == "approval")


def test_shared_seed_variation_cancels_in_constant_paired_effect():
    raw = make_raw()
    assert raw.filter(pl.col("rule") == "majority")["final_welfare"].std() > 0.2
    effects = approval_effects(raw.reverse())
    for row in effects.iter_rows(named=True):
        assert row["n_pairs"] == 3
        assert row["absolute_delta"] == pytest.approx(0.1)
        assert row["paired_std"] == pytest.approx(0.0, abs=1e-15)
        assert row["ci95_lower"] == pytest.approx(0.1)
        assert row["ci95_upper"] == pytest.approx(0.1)


def test_varying_differences_use_paired_sample_standard_deviation():
    effects = approval_effects(make_raw((0.1, 0.2, 0.3)))
    for row in effects.iter_rows(named=True):
        assert row["absolute_delta"] == pytest.approx(0.2)
        assert row["paired_std"] == pytest.approx(0.1)
        assert row["paired_standard_error"] == pytest.approx(0.1 / math.sqrt(3))
        assert row["ci95_lower"] < row["absolute_delta"] < row["ci95_upper"]


def test_pair_alignment_preserves_seed_and_raw_values():
    paired = build_paired_differences(make_raw((0.1, 0.2, 0.3)).reverse())
    welfare = paired.filter((pl.col("rule") == "approval") & (pl.col("metric") == "final_welfare"))
    assert welfare["seed"].to_list() == [42, 43, 44]
    assert welfare["difference"].to_list() == pytest.approx([0.1, 0.2, 0.3])
    assert welfare["baseline_value"].to_list() == pytest.approx([0.1, 0.4, 0.7])


def test_negative_effects_retain_sign_and_baseline_is_zero():
    effects = summarize_paired_effects(build_paired_differences(make_raw((-0.05, -0.05, -0.05))))
    assert all(value < 0 for value in effects.filter(pl.col("rule") == "approval")["ci95_upper"])
    baseline = effects.filter(pl.col("rule") == "majority")
    assert baseline["absolute_delta"].to_list() == [0.0] * len(METRICS)
    assert baseline["ci95_lower"].to_list() == [0.0] * len(METRICS)
    assert baseline["ci95_upper"].to_list() == [0.0] * len(METRICS)


def test_bootstrap_is_reproducible_under_raw_row_reordering():
    raw = make_raw((0.1, 0.2, 0.3))
    assert approval_effects(raw).equals(approval_effects(raw.reverse()))


def test_single_pair_reports_difference_without_confidence_interval():
    effects = approval_effects(make_raw((0.1,)))
    assert effects["absolute_delta"].to_list() == pytest.approx([0.1] * len(METRICS))
    for column in ["paired_std", "paired_standard_error", "ci95_lower", "ci95_upper"]:
        assert effects[column].null_count() == len(METRICS)


def test_missing_seed_pair_is_rejected():
    raw = make_raw().filter(~((pl.col("rule") == "approval") & (pl.col("seed") == 43)))
    with pytest.raises(ValueError, match="mismatched seed/run pairs"):
        build_paired_differences(raw)


def test_duplicate_seed_is_rejected():
    raw = make_raw()
    with pytest.raises(ValueError, match="unique seed"):
        build_paired_differences(pl.concat([raw, raw.head(1)]))


def test_mismatched_run_identifiers_are_rejected():
    raw = make_raw().with_columns(
        pl.when(pl.col("rule") == "approval")
        .then(pl.col("run_id") + 10)
        .otherwise(pl.col("run_id"))
        .alias("run_id")
    )
    with pytest.raises(ValueError, match="mismatched seed/run pairs"):
        build_paired_differences(raw)


def test_missing_baseline_is_rejected():
    with pytest.raises(ValueError, match="no 'majority' baseline"):
        build_paired_differences(make_raw().filter(pl.col("rule") == "approval"))


@pytest.mark.parametrize("value", [None, float("nan"), float("inf")])
def test_missing_or_nonfinite_metrics_are_rejected(value):
    raw = make_raw().with_columns(pl.lit(value).alias("final_welfare"))
    with pytest.raises(ValueError, match="null|finite"):
        build_paired_differences(raw)


def test_undefined_conditional_outcomes_keep_seed_pairs_and_report_coverage():
    raw = make_raw((0.1, 0.2, 0.3)).with_columns(
        pl.when((pl.col("rule") == "approval") & (pl.col("seed") == 43))
        .then(pl.lit(None))
        .otherwise(pl.col("final_survivor_health"))
        .alias("final_survivor_health")
    )
    paired = build_paired_differences(raw)
    assert paired.height == raw.height * len(METRICS)
    effects = summarize_paired_effects(paired)
    health = effects.filter(
        (pl.col("rule") == "approval") & (pl.col("metric") == "final_survivor_health")
    ).row(0, named=True)
    assert health["n_seed_pairs"] == 3
    assert health["n_pairs"] == 2
    assert health["n_undefined_pairs"] == 1
    assert health["absolute_delta"] == pytest.approx(0.2)
    assert health["estimand"] == "defined_pairs_only"
    survival = effects.filter(
        (pl.col("rule") == "approval") & (pl.col("metric") == "final_survival_rate")
    ).row(0, named=True)
    assert survival["n_pairs"] == 3
    assert survival["estimand"] == "all_seed_pairs"


def test_no_defined_health_pairs_do_not_invent_an_effect():
    raw = make_raw().with_columns(pl.lit(None, dtype=pl.Float64).alias("final_survivor_health"))
    effects = approval_effects(raw)
    health = effects.filter(pl.col("metric") == "final_survivor_health").row(0, named=True)
    assert health["n_pairs"] == 0
    assert health["n_seed_pairs"] == health["n_undefined_pairs"] == 3
    assert health["absolute_delta"] is None
    assert health["ci95_lower"] is health["ci95_upper"] is None
