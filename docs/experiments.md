# Experiments

Use `run` to inspect one trajectory, `compare` to compare rules in one scenario,
and `suite` to repeat the comparison across predefined conditions. A replication
is a whole trajectory for one rule and seed, not one member or round. See the
[walkthrough](walkthrough.md) before interpreting the output and the
[reproducibility guide](reproducibility.md) for setup requirements.

Run a small comparison:

```bash
pcds compare --steps 30 --runs 20 --output results/comparison.csv
```

Run the reviewer-oriented suite:

```bash
pcds suite --sensitivity --workers 4 --steps 40 --runs 100 --seed 42 --output-dir results/research_review_2026-10-14
```

The default suite retains eight conditions. `--sensitivity` adds six physical
probes (energy generation 0/1/4, treatment cost 0.5/2, and shock probability
0.05), for 14 conditions total. See the [study protocol](study_protocol.md)
for the rationale, fixed ranges, and inference limits.

The original conditions are:

- authored baseline (legacy identifier `moderate_scarcity`; outcomes can be severe);
- fixed-preference baseline;
- adaptive evaluation with equal specialist and general accuracy;
- severe scarcity;
- environmental shocks;
- low-trust and high-trust networks;
- expertise imbalance.

For each condition, the artifact stores raw per-run results, aggregate means,
approximate 95% confidence intervals, metadata, and a Markdown report. The
expected interpretation is multidimensional: assess survival and population
health alongside conditional health, preference congruence, concentration, and
reserves. A low dispersion/concentration value alone is not a favorable outcome.

Raw results also record final assessment error and the total number of
full-ranking changes across agents and rounds. Metadata embeds the resolved base
scenario and every experiment configuration, including information parameters.
These diagnostics do not replace outcome metrics or demonstrate that experts
always govern better.

Both `compare` and `suite` now write per-seed paired differences and paired
effect summaries against majority. For `comparison.csv`, the additional files
are `comparison_paired_differences.csv` and `comparison_effects_vs_majority.csv`.
The suite uses `suite_paired_differences.csv` and `suite_effects_vs_majority.csv`.

Effects retain the signed `absolute_delta` column (an additive difference, not
an absolute value) and add `n_pairs`, `paired_std`, `paired_standard_error`,
`ci95_lower`, `ci95_upper`, `ci_method`, and `bootstrap_resamples`. Positive
differences raise survival, health, satisfaction, welfare, and resilience;
negative differences reduce dispersion and ballot concentration. Delegated vote
share has no preferred direction. Intervals describe uncertainty in the mean
paired difference, not overlap between separate rule-level confidence intervals.
With one pair, interval endpoints are blank in CSV outputs.

Conditional metrics can be undefined after extinction or loss of the electorate.
Effects add `n_seed_pairs`, `n_undefined_pairs`, `estimand`, and
`preferred_direction`. Their `n_pairs` counts only pairs defined in both rules;
all seed rows remain in the differences export. The dashboard and summaries show
defined-run counts to expose survivor/electorate selection.

Raw results export welfare contributions and three prespecified weight profiles;
profiles also receive paired effect intervals. Metadata embeds weights, resource
references, profile definitions, directions, and `separate-outcomes-v1`. See
[metrics.md](metrics.md) for the normative rationale and interpretation limits.

## Which File Answers Which Question?

| Suite output | What it contains | How to use it |
| --- | --- | --- |
| `suite_report.md` | A reading guide, readable outcome/paired tables, figures, coverage, and interpretation limits. | Start here, reading survival and health beside representation. |
| `suite_raw.csv` | Final outcomes and diagnostics for each rule/condition/seed. | Inspect individual trials rather than only averages. |
| `suite_paired_differences.csv` | Baseline value, rule value, and their difference for each metric and matched seed. | Check the elementary observations supporting an effect estimate. |
| `suite_effects_vs_majority.csv` | Mean differences, intervals, directions, and defined-pair coverage. | Assess one stated comparison and its uncertainty. |
| `suite_summary.csv` | Means, descriptive interval half-widths, and defined-run counts by rule/condition. | Do not treat separate-rule intervals as intervals on differences. |
| `suite_metadata.json` | Scenario settings, versions, schemas, and analysis choices. | Keep this with shared results so assumptions can be reconstructed. |
| `survival_by_condition.png` | Survival means on a fixed 0-100 scale. | Compare condition dependence without an overall institution ranking. |
| `baseline_paired_effects.png` | Four baseline outcomes with paired intervals and pair coverage. | Distinguish estimated direction from uncertainty and selection. |
| `suite_validation.json` | Consistency checks and warnings. | PASS means those checks succeeded, not that assumptions are realistic. |

The CLI `run` prints a final summary; suite CSV files do not archive every round.
The Python `run_simulation` function returns round-by-round records, including
ballot traces. The [code guide](code_guide.md) shows how to inspect those records.

Dashboard numbers are rounded. `n` beside a conditional mean counts defined runs,
while `n_pairs` in an effect table counts seeds defined under both compared rules.
These counts need not be equal. For example, high health among a few surviving
runs is not evidence of high health across every initial community.

The metadata also records normalized source-content SHA-256 hashes, including
uncommitted code, and the primary outcome set. Charts and the report are generated
from the same validated tables and do not alter trajectories. See
[current results](current_results.md) for the dated interpretation and retained
evidence snapshot. Verbose CSV dumps remain separate downloads.
