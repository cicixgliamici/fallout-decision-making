"""Check that readable reports preserve units, missing outcomes, and coverage."""

import polars as pl

from pcds.research_reporting import _effect, material_table, paired_table, representation_table


def test_paired_cell_uses_signed_points_and_does_not_invent_uncertainty():
    row = {"absolute_delta": -0.025, "ci95_lower": None, "ci95_upper": None,
           "n_pairs": 1, "n_seed_pairs": 10}
    assert _effect(row) == "-2.5 [N/A, N/A]; 1/10"
    row.update(absolute_delta=None, n_pairs=0)
    assert _effect(row) == "N/A [N/A, N/A]; 0/10"


def test_material_table_separates_extinction_from_low_survival_and_inactive_cycles():
    raw = pl.DataFrame({
        "experiment": ["moderate_scarcity"] * 2, "rule": ["majority"] * 2,
        "final_survivors": [0, 1], "final_survival_rate": [0.0, 0.025],
        "final_population_health": [0.0, 0.01], "blocked_policy_count": [2, 1],
        "inactive_cycle_count": [30, 0], "observation_steps": [40, 40],
    })
    table = material_table(raw)
    assert "| Authored baseline | Plurality | 1.2 | 1/2 | 0.5 | 3/50 |" in table
    assert "winner" not in table


def test_political_means_show_absence_and_defined_run_counts():
    summary = pl.DataFrame({
        "experiment": ["moderate_scarcity"], "rule": ["majority"],
        "mean_final_prior_preference_satisfaction": [None],
        "n_final_prior_preference_satisfaction": [0],
        "mean_final_delegation_concentration": [None], "n_final_delegation_concentration": [0],
    })
    assert "| N/A (0) | N/A (0) |" in representation_table(summary)


def test_paired_table_retains_unfavorable_and_zero_coverage_results():
    from pcds.research_reporting import FOCUS_METRICS

    effects = pl.DataFrame([{
        "experiment": "moderate_scarcity", "rule": "expert_delegation", "metric": metric,
        "absolute_delta": -0.1 if metric == "final_survival_rate" else None,
        "ci95_lower": -0.2 if metric == "final_survival_rate" else None,
        "ci95_upper": -0.01 if metric == "final_survival_rate" else None,
        "n_pairs": 10 if metric == "final_survival_rate" else 0, "n_seed_pairs": 10,
    } for metric in FOCUS_METRICS])
    table = paired_table(effects, ["moderate_scarcity"])
    assert "-10.0 [-20.0, -1.0]; 10/10" in table
    assert "N/A [N/A, N/A]; 0/10" in table
