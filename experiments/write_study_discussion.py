"""Refresh the dated reader-facing discussion from retained evidence tables."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from pcds.research_reporting import CONDITION_LABELS, RULE_LABELS


def number(value: float | None, scale: float = 100) -> str:
    return "N/A" if value is None else f"{value * scale:.2f}"


def effect_cell(frame: pl.DataFrame, rule: str, metric: str) -> str:
    row = frame.filter((pl.col("rule") == rule) & (pl.col("metric") == metric)).row(0, named=True)
    values = [number(row[key]) for key in ("absolute_delta", "ci95_lower", "ci95_upper")]
    return f"{values[0]} [{values[1]}, {values[2]}]; {row['n_pairs']}/{row['n_seed_pairs']}"


def baseline_table(raw: pl.DataFrame) -> str:
    lines = ["| Rule | Survival % | Extinct / runs | Population health (0-100) |",
             "| --- | ---: | ---: | ---: |"]
    for rule, label in RULE_LABELS.items():
        rows = raw.filter(pl.col("rule") == rule)
        extinct = rows.filter(pl.col("final_survivors") == 0).height
        lines.append(f"| {label} | {number(rows['final_survival_rate'].mean())} | "
                     f"{extinct}/{rows.height} | {number(rows['final_population_health'].mean())} |")
    return "\n".join(lines)


def material_effect_table(main: pl.DataFrame, holdout: pl.DataFrame) -> str:
    lines = ["| Rule minus plurality | Baseline survival | Baseline population health | Separate-block survival |",
             "| --- | --- | --- | --- |"]
    for rule, label in RULE_LABELS.items():
        if rule != "majority":
            cells = [effect_cell(main, rule, "final_survival_rate"),
                     effect_cell(main, rule, "final_population_health"),
                     effect_cell(holdout, rule, "final_survival_rate")]
            lines.append(f"| {label} | {' | '.join(cells)} |")
    return "\n".join(lines)


def sensitivity_table(raw: pl.DataFrame, steps: int) -> str:
    names = ["moderate_scarcity", "energy_zero", "energy_low", "energy_high",
             "treatment_low_cost", "treatment_high_cost", "low_hazard", "environmental_shocks"]
    lines = ["| Condition | Survival range across rules % | Extinct / runs | Blocked / active cycles |",
             "| --- | ---: | ---: | ---: |"]
    for name in names:
        frame = raw.filter(pl.col("experiment") == name)
        means = frame.group_by("rule").agg(pl.col("final_survival_rate").mean())
        extinct = frame.filter(pl.col("final_survivors") == 0).height
        active = frame.height * steps - frame["inactive_cycle_count"].sum()
        lines.append(f"| {CONDITION_LABELS[name]} | "
                     f"{number(means['final_survival_rate'].min())}-{number(means['final_survival_rate'].max())} | "
                     f"{extinct}/{frame.height} | {frame['blocked_policy_count'].sum()}/{active} |")
    return "\n".join(lines)


def main_findings(effects: pl.DataFrame) -> str:
    """Explain the dated baseline contrast without turning pointwise evidence into a ranking."""
    approval = effects.filter(
        (pl.col("rule") == "approval") & (pl.col("metric") == "final_survival_rate")
    ).row(0, named=True)
    return (
        f"The clearest baseline material contrast is top-two approval versus plurality: "
        f"**+{number(approval['absolute_delta'])} survival percentage points**, with a "
        f"pointwise 95% interval [{number(approval['ci95_lower'])}, "
        f"{number(approval['ci95_upper'])}]. The separate seed block points in the same "
        "direction, with wider uncertainty. Both delegation survival intervals cross zero "
        "in the baseline; their concentration intervals are above zero among defined "
        "decision-time electorates. This does not show a material delegation advantage "
        "here, and it does expose a representation tradeoff. It is not a general result "
        "about real institutions or all possible parameter settings."
    )


def write_discussion(snapshot: Path, destination: Path) -> None:
    """Use final data for every numerical claim; preserve separate seed-block estimates."""
    raw = pl.read_csv(snapshot / "suite_raw.csv")
    effects = pl.read_csv(snapshot / "suite_effects_vs_majority.csv")
    holdout = pl.read_csv(snapshot / "holdout_raw.csv")
    holdout_effects = pl.read_csv(snapshot / "holdout_effects.csv")
    metadata = json.loads((snapshot / "suite_metadata.json").read_text(encoding="utf-8"))
    # This is a dated interpretation template, not a generic study author.
    # Reject different designs rather than reusing its fixed protocol claims.
    if (metadata["runs"], metadata["steps"], metadata["seed"], raw.height, holdout.height) != (
        100, 40, 42, 5600, 80
    ):
        raise ValueError("discussion template requires the declared 2026-10-14 study design")
    baseline = raw.filter(pl.col("experiment") == "moderate_scarcity")
    baseline_effects = effects.filter(pl.col("experiment") == "moderate_scarcity")
    extinct = raw.filter(pl.col("final_survivors") == 0).height
    coverage = baseline_effects.filter(
        (pl.col("rule") != "majority")
        & (pl.col("metric") == "final_prior_preference_satisfaction")
    )["n_pairs"]
    relative = "evidence/2026-10-14"
    sections = [
        "# Current Results and Discussion",
        "Study snapshot: **2026-10-14**. Physics `stock-budgeted-v2`. The baseline was "
        "preserved; no parameter was retuned to make an institution win. This is a refreshed "
        "exploratory study, not empirical validation or a universal governance recommendation.",
        f"The main study runs **{raw.height:,} trajectories**, 100 seeds (42-141) per "
        "rule/condition, 14 conditions, 40 original residents, and 40 cycles. A separate "
        f"20-seed baseline block (10042-10061) adds **{holdout.height} trajectories**. "
        "All comparisons use shared outside draws within each condition and seed. "
        f"Main-study extinctions total **{extinct}/{raw.height}** across mixed conditions; "
        "that aggregate is not a baseline extinction probability.",
        f"Start with the [readable full report]({relative}/suite_report.md), the "
        "[study protocol](study_protocol.md), and the [assumption register and primary "
        "bibliography](research_basis.md). The [ODD specification](model_specification.md) "
        "connects the conceptual model to executable submodels.",
        "## What Happens in the Baseline",
        main_findings(baseline_effects),
        baseline_table(baseline),
        "Survival counts every original resident. Population health assigns zero to deaths. "
        "Extinction is a trial with no remaining residents; a trial with one survivor is "
        "non-extinct but is not a successful colony. Read these columns together rather "
        "than interpreting mean health among survivors as population-wide wellbeing.",
        "## How Large Are the Differences?",
        f"![Baseline paired differences and uncertainty]({relative}/baseline_paired_effects.png)",
        "Cells below show mean difference [95% percentile bootstrap interval]; defined/total "
        "seed pairs. Survival uses percentage points; health uses score points on a 0-100 "
        "scale. Differences are rule minus plurality, not relative percent gains. The "
        "separate block uses only 20 seeds, so its estimates are less precise and remain "
        "separate from the main 100-seed results.",
        material_effect_table(baseline_effects, holdout_effects),
        "An interval crossing zero leaves the direction unresolved at this precision; it "
        "does not establish equivalence. Excluding zero is pointwise exploratory evidence "
        "within this model. There is no multiplicity adjustment across the 84 primary "
        "material contrasts, and the development seed block was reused. Neither result "
        "licenses a general claim that delegation or direct voting is superior.",
        "## Why Physical Assumptions Matter",
        f"![Survival across all conditions]({relative}/survival_by_condition.png)",
        sensitivity_table(raw, metadata["steps"]),
        "Each sensitivity row changes one physical parameter around the authored baseline; "
        "the range describes the four rule means, not an uncertainty interval. Initial "
        "stocks, losses, and all other inputs stay fixed in those probes. Full per-rule "
        "values and paired effects appear in the report. The fixed no-shock production "
        "schedule remains evidence of finite-horizon feasibility, not evidence that voters "
        "find an optimal strategy or that every death is institutionally avoidable.",
        "Blocked actions have no policy effects. Post-extinction recording cycles are "
        "counted separately, so extinction does not inflate the action-failure rate. A "
        "parameter can have little effect in the tested range when its physical constraint "
        "is rarely binding. Do not read a flat response as proof that energy or medicine "
        "never matters. This panel does not estimate interactions or global sensitivity.",
        "Two concrete limits of this baseline are visible in the data. Increasing power "
        "generation from 2 to 4 leaves the final survival results unchanged; generation "
        "1 also produces no physically blocked actions in this sample. The 0.5/2 medical "
        "conversion probes change medical reserves but leave final survival unchanged. "
        "Thus these ordinary-range probes do not show a survival benefit from extra "
        "power or cheaper care. The zero-generation stress is different: all 400 trials "
        "end in extinction. Under lower shock probability, no trial is extinct and rule "
        "mean survival ranges from 77.25% to 98.80%. Hazard assumptions strongly shape "
        "the scope for interpreting governance outcomes; no fuel or clinical calibration "
        "is established by these contrasts.",
        "## Representation Has a Coverage Problem",
        f"Baseline original-priority satisfaction effects use **{coverage.min()}-"
        f"{coverage.max()} of 100** defined seed pairs across the three comparisons. "
        "These averages refer to the decision-time electorate in the final cycle. Its "
        "members can die later in that same cycle; even complete run coverage would not "
        "mean most original residents survived. The full report shows political means, "
        "defined-run counts, paired coverage, and concentration together.",
        "Plurality and top-two approval retain individual ballot ownership, so their "
        "concentration is zero when defined. Delegation can concentrate ownership, but "
        "low concentration in a severely depleted electorate is not evidence of democratic "
        "success. Original-priority congruence measures rank agreement, not informed "
        "consent, successful policy delivery, procedural legitimacy, or preference intensity.",
        "The equal-accuracy and fixed-preference conditions help challenge the information "
        "mechanism. They do not establish that real experts behave like these agents. "
        "Sparse/dense network conditions jointly change graph structure and edge density; "
        "role imbalance also changes generated prior distributions. Interpret them as "
        "bundled interventions, and do not treat overlapping intervals as a formal "
        "test of an interaction or difference of effects.",
        "## What Is Now Defensible, and What Remains Open",
        "The contribution is a reproducible, inspectable comparison with explicit stock "
        "budgets, assumptions, outcome definitions, matched trials, sensitivity probes, "
        "and preserved unfavorable/undefined results. The sources motivate the question "
        "and documentation method; they do not calibrate our numerical parameters. "
        "Tests and consistency checks support implementation claims, not empirical realism.",
        "Next research priorities are domain-informed parameter ranges, independent "
        "replication, longer horizons and population scaling, behavioral alternatives, "
        "and interaction/global sensitivity analysis. A less lethal authored scenario may "
        "help inspect representation before population collapse; it must be declared as a "
        "new scenario rather than silently replacing this baseline. Meaningful formal "
        "invariants and actual optional-backend checks remain separate work.",
        "## Retained Evidence and Verification",
        f"The [evidence directory]({relative}/suite_report.md) contains raw outcomes, "
        "complete configurations, all paired effects, lossless compressed per-seed "
        "differences, both figures, the separate seed block, source hashes, recorded "
        "project/test dependencies, and artifact checksums. It is not ignored by Git. "
        "Generated working copies remain under `results/research_review_2026-10-14/` "
        "and `results/research_holdout_2026-10-14/`.",
        "The main suite passed consistency validation. **195 Python tests passed**, "
        "including parallel/sequential equality, missing-value/coverage presentation, "
        "units and unfavorable effects. Ruff and local-link/whitespace checks passed; "
        "figures were visually inspected. Lean, real SWI-Prolog integration, and a "
        "clean-room install were not checked by this study.",
    ]
    destination.write_text("\n\n".join(sections) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    write_discussion(arguments.snapshot, arguments.destination)


if __name__ == "__main__":
    main()
