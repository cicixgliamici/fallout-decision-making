# Exploratory Study Protocol

Analysis plan: **2026-10-14**. This follows inspection of earlier small runs and
historical difficulty calibration; it is not preregistration or independent
confirmation of hypotheses selected without seeing data. Physics remains
`stock-budgeted-v2`; this study changes experimental coverage and presentation,
not simulation mechanics or baseline parameters.

## Questions and Outcomes

| Question | Comparison | What the result can show |
| --- | --- | --- |
| Does a delegated rule change material outcomes? | Expert/liquid delegation minus plurality within the same condition and seed. Top-two approval is an additional direct-voting comparator. | Direction and size of differences in this specified model. No universal institution ranking. |
| Does specialist information matter? | Read rule effects in the baseline and equal-accuracy ablation. | Sensitivity to the information advantage. Comparing two interval plots alone is not a statistical test of a difference of effects. |
| What is the representation cost? | Original-priority congruence and actual ballot concentration, alongside material outcomes. | An explicit descriptive tradeoff, conditional on the defined electorate; not a complete measure of legitimacy. |
| Are conclusions fragile to physical assumptions? | One-factor energy, treatment-cost, and hazard probes around the same baseline. | Dependence in the tested range; not global sensitivity or interaction identification. |

Primary material outcomes are final survival rate and final population health,
which include all original residents and remain defined after extinction.
Extinction counts accompany them, without redefining one survivor as success.
Original-priority satisfaction and ballot concentration are key secondary
outcomes. Survivor health, current satisfaction, reserves, and normative welfare
profiles remain available in the full exports; no outcome is dropped because its
result is unfavorable.

## Conditions Fixed Before This Expanded Run

The original eight conditions remain unchanged: authored baseline, fixed
preferences, equal accuracy, severe consumption, higher shocks, sparse trust,
dense trust, and role imbalance. The identifier `moderate_scarcity` is retained
for compatibility, but is displayed as **Authored baseline**: its hazard level
and mortality do not justify calling its outcomes moderate.

`--sensitivity` adds six explicitly declared probes:

| Condition | Change from baseline | Other parameters |
| --- | --- | --- |
| `energy_zero` | Energy replenishment 0 rather than 2 | Unchanged; initial energy remains 50. |
| `energy_low` | Energy replenishment 1 | Unchanged. |
| `energy_high` | Energy replenishment 4 | Unchanged. |
| `treatment_low_cost` | Medicine per summed health point 0.5 rather than 1 | Unchanged. |
| `treatment_high_cost` | Medicine per summed health point 2 | Unchanged. |
| `low_hazard` | Shock probability 0.05 rather than 0.22 | Shock loss magnitudes unchanged; higher-shock condition already uses 0.30. |

The ranges are transparent engineering-style stress probes, not data-derived
confidence ranges. There is no factorial crossing and no adjustment to select
a preferred rule's win. Sparse/dense trust conditions change topology and edge
probability jointly; role imbalance also changes generated prior distributions.
They must be interpreted as packages, not pure single-variable interventions.

## Replication, Pairing, and Interpretation

The expanded run uses **100 replications per rule/condition**, seeds **42-141**,
40 original residents, and 40 cycles: **5,600 trajectories** across 14 conditions
and four rules. Those seeds overlap earlier development runs; this is refreshed
exploratory evidence, not a held-out validation sample. Each seed is a whole
community history. Residents and cycles are not independent replications.

Before reading the expanded results, an additional separate baseline seed block
was specified: 20 replications per rule, seeds 10042-10061, 40 cycles (**80
additional trajectories**). It is retained separately to examine seed-block
stability, not pooled to improve a chosen effect or described as empirical
validation. Its intervals are less precise than the main 100-seed analysis.

Within a condition, rules share population, trust construction, and keyed
outside draws. Matching trace digests is checked. Subtract each plurality outcome
from the corresponding rule outcome before calculating means and 95% percentile
bootstrap intervals (2,000 seed resamples). Preserve every seed and expose
undefined conditional differences with defined/total pair counts.

Intervals are pointwise, approximate, and unadjusted for multiple comparisons.
The two primary metrics alone produce 84 non-baseline rule/condition contrasts;
selection among many intervals can overstate evidence. Crossing zero is not
equivalence; excluding zero is not proof of a universally superior institution.
This study does not use p-values or claim family-wide error control.

Do not equate cross-condition changes to causal effects of one altered parameter
when other inputs change. A low-hazard condition has a different realized shock
sequence; external-trace equality is required across rules within it, not between
different shock-probability conditions.

## Reproduce and Audit

```bash
pcds suite --sensitivity --workers 4 --runs 100 --steps 40 --seed 42 --output-dir results/research_review_2026-10-14
```

The report now includes readable tables, a survival heatmap, baseline paired
intervals, extinction counts, execution diagnostics, and conditional coverage.
CSV files retain every metric and observation. Metadata embeds each resolved
configuration, dependency versions, source-content hashes, and analysis choices.
Source hashes include local uncommitted code rather than attributing such work
to an unchanged Git revision. Normalize source line endings before hashing.

The [current results](current_results.md) interpret this run. A compact evidence
snapshot is retained in the repository; full per-seed differences can be
regenerated and remain under the ignored `results/` directory. Keep configuration,
raw data, effects, figures, validation, and metadata together when sharing.
The listed hashes identify source contents but do not archive the runtime itself.
