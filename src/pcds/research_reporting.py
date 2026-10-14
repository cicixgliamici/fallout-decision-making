"""Present observed outcomes and paired uncertainty without inventing a winner."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

RULE_LABELS = {
    "majority": "Plurality",
    "approval": "Top-two approval",
    "expert_delegation": "Expert delegation",
    "liquid_democracy": "Liquid delegation",
}
CONDITION_LABELS = {
    "moderate_scarcity": "Authored baseline",
    "fixed_preferences": "Fixed preferences",
    "equal_accuracy": "Equal information accuracy",
    "severe_scarcity": "Severe consumption",
    "environmental_shocks": "Higher shock probability (0.30)",
    "low_trust": "Sparse trust network",
    "high_trust": "Dense trust network",
    "expertise_imbalance": "Unequal role distribution",
    "energy_zero": "No energy replenishment",
    "energy_low": "Energy replenishment: 1",
    "energy_high": "Energy replenishment: 4",
    "treatment_low_cost": "Medicine / health point: 0.5",
    "treatment_high_cost": "Medicine / health point: 2",
    "low_hazard": "Lower shock probability (0.05)",
}
FOCUS_METRICS = {
    "final_survival_rate": "Survival",
    "final_population_health": "Population health",
    "final_prior_preference_satisfaction": "Original-priority satisfaction",
    "final_delegation_concentration": "Ballot concentration",
}


def _condition_order(raw: pl.DataFrame) -> list[str]:
    """Keep baseline first and retain declared condition order, never sort by outcome."""
    observed = raw["experiment"].unique(maintain_order=True).to_list()
    return sorted(observed, key=lambda name: name != "moderate_scarcity")


def _value(value: float | None, scale: float = 1.0) -> str:
    return "N/A" if value is None else f"{scale * value:.1f}"


def _effect(row: dict) -> str:
    """Use score points; survival differences on this scale are percentage points."""
    mean = _value(row["absolute_delta"], 100)
    lower, upper = (_value(row[key], 100) for key in ("ci95_lower", "ci95_upper"))
    return f"{mean} [{lower}, {upper}]; {row['n_pairs']}/{row['n_seed_pairs']}"


def material_table(raw: pl.DataFrame) -> str:
    """Expose extinction separately from average survival, with fixed rule ordering."""
    lines = [
        "| Condition | Rule | Survival % | Extinct / runs | Population health /100 | Blocked / active cycles |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for condition in _condition_order(raw):
        for rule, label in RULE_LABELS.items():
            frame = raw.filter((pl.col("experiment") == condition) & (pl.col("rule") == rule))
            if frame.is_empty():
                continue
            extinct = frame.filter(pl.col("final_survivors") == 0).height
            # Inactive observations after extinction are not attempted actions.
            blocked = frame["blocked_policy_count"].sum()
            steps = frame["observation_steps"][0]
            active = frame.height * steps - frame["inactive_cycle_count"].sum()
            lines.append(
                f"| {CONDITION_LABELS.get(condition, condition)} | {label} | "
                f"{_value(frame['final_survival_rate'].mean(), 100)} | {extinct}/{frame.height} | "
                f"{_value(frame['final_population_health'].mean(), 100)} | {blocked}/{active} |"
            )
    return "\n".join(lines)


def representation_table(summary: pl.DataFrame) -> str:
    """Show conditional coverage beside every political mean, including plurality."""
    metrics = ["final_prior_preference_satisfaction", "final_delegation_concentration"]
    lines = [
        "| Condition | Rule | Original-priority satisfaction /100 (n) | Concentration /100 (n) |",
        "| --- | --- | ---: | ---: |",
    ]
    # A stable lexical order is sufficient here; charts and material tables carry baseline first.
    for row in summary.sort(["experiment", "rule"]).iter_rows(named=True):
        values = [
            f"{_value(row[f'mean_{metric}'], 100)} ({row[f'n_{metric}']})" for metric in metrics
        ]
        lines.append(
            f"| {CONDITION_LABELS.get(row['experiment'], row['experiment'])} | "
            f"{RULE_LABELS[row['rule']]} | {' | '.join(values)} |"
        )
    return "\n".join(lines)


def paired_table(effects: pl.DataFrame, conditions: list[str]) -> str:
    """Report all focus comparisons, including null and unfavorable differences."""
    lines = [
        "| Condition | Rule vs plurality | Survival | Population health | Original satisfaction | Concentration |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for condition in conditions:
        for rule, label in RULE_LABELS.items():
            if rule == "majority":
                continue
            selected = effects.filter((pl.col("experiment") == condition) & (pl.col("rule") == rule))
            if selected.is_empty():
                continue
            by_metric = {row["metric"]: row for row in selected.iter_rows(named=True)}
            cells = [_effect(by_metric[metric]) for metric in FOCUS_METRICS]
            lines.append(f"| {CONDITION_LABELS.get(condition, condition)} | {label} | {' | '.join(cells)} |")
    return "\n".join(lines)


def report_text(raw: pl.DataFrame, summary: pl.DataFrame, effects: pl.DataFrame, validation: dict) -> str:
    """Lead with scale and limits, then facts, then detailed comparison tables."""
    checks = validation["checks"]
    extinct = raw.filter(pl.col("final_survivors") == 0).height
    conditions = _condition_order(raw)
    status = "PASS" if validation["passed"] else "FAIL"
    warnings = "; ".join(validation["warnings"]) or "none"
    sections = [
        "# Governance Experiment: Results and Interpretation",
        f"{raw.height:,} trajectories; {checks['runs']} seeds per rule/condition; "
        f"{checks['steps']} cycles; {len(conditions)} conditions. Physics: `{raw['physics_schema'][0]}`.",
        "## What to Read First",
        f"{extinct}/{raw.height} trajectories end with no survivors. This aggregate combines "
        "different conditions; use the per-condition rows below for comparisons. A non-extinct "
        "colony may still have lost most residents.",
        "Survival and population health are the primary material outcomes. Satisfaction and "
        "ballot concentration describe representation, conditional on a surviving electorate. "
        "There is no overall institution ranking or composite political-quality score.",
        "This is exploratory analysis of authored assumptions, not a preregistered confirmatory "
        "study or empirical prediction. Tests establish implementation behavior; simulation "
        "consistency checks do not establish empirical validity.",
        f"Validation status: **{status}**. Warnings: {warnings}.",
        "## Outcome Dashboard",
        "Survival is a percentage of the original population. Population health is the mean "
        "health of that population, assigning zero to deaths, scaled to 0-100. Extinction is "
        "the number of trials ending at zero survivors. Active cycles exclude post-extinction "
        "placeholders. Both healthy and severely depleted colonies can be non-extinct.",
        "![Mean survival by condition and rule](survival_by_condition.png)",
        material_table(raw),
        "## Paired Effects Against Plurality",
        "Each cell is mean difference [95% percentile bootstrap interval]; defined/total seed "
        "pairs. Every difference is rule minus plurality, multiplied by 100. For survival these "
        "are percentage points, not relative percent changes; other metrics use score points. "
        "Positive survival, health, or satisfaction differences raise that measure; negative "
        "concentration differences disperse ballot control. No interval is shown with fewer "
        "than two defined pairs.",
        "![Baseline paired differences and coverage](baseline_paired_effects.png)",
        paired_table(effects, conditions),
        "## Representation and Coverage",
        "Values below are conditional means /100, with the number of defined runs (n). "
        "The paired table instead uses the intersection of defined runs under both rules. "
        "Different survivor/electorate subsets can change these estimates. Even complete "
        "run coverage does not imply that most residents survived.",
        representation_table(summary),
        "## What These Comparisons Can Establish",
        "Within each condition, rules share initial populations, trust networks, and outside "
        "draws. Paired intervals describe seed variability within that condition. An interval "
        "crossing zero is inconclusive about the direction; it does not prove equivalence. "
        "An interval excluding zero is pointwise exploratory evidence, with no multiplicity "
        "adjustment across metrics and conditions. Do not infer a universal winner.",
        "The optional physical sensitivity panel changes one parameter at a time. It can "
        "expose dependence on energy, treatment conversion cost, and hazards; it does not "
        "estimate interactions or a global sensitivity decomposition. Fixed preferences and "
        "equal information accuracy are mechanism ablations, not empirical validation.",
        "Survivor health, current satisfaction, resource stocks, welfare decompositions, and "
        "alternative welfare weights remain available in the CSV exports. Welfare weights "
        "are normative choices. No policy, seed, or unsuccessful result is removed to favor "
        "a voting rule.",
        "## Audit Files",
        "- [Raw trajectories](suite_raw.csv): final outcomes, execution diagnostics, and outside-trace digests.\n"
        "- [Paired effects](suite_effects_vs_majority.csv): every metric, interval, and coverage.\n"
        "- [Per-seed differences](suite_paired_differences.csv): elementary matched observations.\n"
        "- [Rule summaries](suite_summary.csv): descriptive means and separate-rule intervals.\n"
        "- [Metadata](suite_metadata.json): complete configurations, runtime versions, source hashes.\n"
        "- [Validation](suite_validation.json): checks and warnings.",
    ]
    return "\n\n".join(sections) + "\n"


def _save_figure(figure: Figure, path: Path) -> None:
    """Use a headless renderer so generating evidence never requires a GUI."""
    FigureCanvasAgg(figure)
    figure.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    figure.clear()


def survival_figure(raw: pl.DataFrame, output: Path) -> None:
    """Keep a fixed 0-100 scale and show values so small survival is not exaggerated."""
    conditions = _condition_order(raw)
    values = np.empty((len(conditions), len(RULE_LABELS)))
    for i, condition in enumerate(conditions):
        for j, rule in enumerate(RULE_LABELS):
            frame = raw.filter((pl.col("experiment") == condition) & (pl.col("rule") == rule))
            mean = frame["final_survival_rate"].mean()
            values[i, j] = np.nan if mean is None else mean * 100
    figure = Figure(figsize=(10, max(4, len(conditions) * 0.42 + 1.7)), layout="constrained")
    axis = figure.subplots()
    mesh = axis.imshow(values, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    axis.set_xticks(range(len(RULE_LABELS)), list(RULE_LABELS.values()), fontsize=10)
    axis.set_yticks(range(len(conditions)), [CONDITION_LABELS.get(c, c) for c in conditions])
    for i, j in np.ndindex(values.shape):
        text = "N/A" if np.isnan(values[i, j]) else f"{values[i, j]:.1f}%"
        axis.text(j, i, text, ha="center", va="center", color="white" if values[i, j] > 55 else "#172b40")
    axis.set_title("Mean final survival: fraction of the original population", pad=16)
    figure.colorbar(mesh, ax=axis, label="Survival (%)", shrink=0.8)
    _save_figure(figure, output / "survival_by_condition.png")


def baseline_effect_figure(effects: pl.DataFrame, output: Path) -> None:
    """Plot means and intervals independently; missing intervals never become zero bars."""
    figure = Figure(figsize=(11, 7), layout="constrained")
    axes = figure.subplots(2, 2).flat
    rules = [rule for rule in RULE_LABELS if rule != "majority"]
    for axis, (metric, title) in zip(axes, FOCUS_METRICS.items()):
        labels = []
        for index, rule in enumerate(rules):
            frame = effects.filter(
                (pl.col("experiment") == "moderate_scarcity")
                & (pl.col("rule") == rule) & (pl.col("metric") == metric)
            )
            if frame.is_empty():
                labels.append(RULE_LABELS[rule] + " (N/A)")
                continue
            row = frame.row(0, named=True)
            labels.append(f"{RULE_LABELS[rule]} ({row['n_pairs']}/{row['n_seed_pairs']})")
            if row["absolute_delta"] is not None:
                axis.scatter(row["absolute_delta"] * 100, index, color="#185a85", zorder=3)
            if row["ci95_lower"] is not None and row["ci95_upper"] is not None:
                axis.hlines(index, row["ci95_lower"] * 100, row["ci95_upper"] * 100,
                            color="#185a85", linewidth=2)
        axis.axvline(0, color="#687685", linestyle="--", linewidth=1)
        axis.set_yticks(range(len(rules)), labels, fontsize=9)
        axis.set_ylim(len(rules) - 0.5, -0.5)
        axis.set_title(title)
        axis.set_xlabel("Rule minus plurality, score points (x100)", fontsize=9)
        axis.grid(axis="x", alpha=0.15)
    figure.suptitle("Authored baseline: paired differences and 95% intervals\n"
                    "Labels show defined/total seed pairs; survival uses percentage points", fontsize=12)
    _save_figure(figure, output / "baseline_paired_effects.png")


def write_research_report(
    raw: pl.DataFrame, summary: pl.DataFrame, effects: pl.DataFrame, validation: dict, output: Path
) -> None:
    """Write figures and a readable report from the same validated data, without resimulation."""
    output.mkdir(parents=True, exist_ok=True)
    # Store the horizon in a local reporting copy; do not change the raw CSV schema.
    reporting_raw = raw.with_columns(pl.lit(validation["checks"]["steps"]).alias("observation_steps"))
    survival_figure(reporting_raw, output)
    baseline_effect_figure(effects, output)
    text = report_text(reporting_raw, summary, effects, validation)
    (output / "suite_report.md").write_text(text, encoding="utf-8")
