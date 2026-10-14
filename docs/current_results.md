# Current Results and Discussion

Study snapshot: **2026-10-14**. Physics `stock-budgeted-v2`. The baseline was preserved; no parameter was retuned to make an institution win. This is a refreshed exploratory study, not empirical validation or a universal governance recommendation.

The main study runs **5,600 trajectories**, 100 seeds (42-141) per rule/condition, 14 conditions, 40 original residents, and 40 cycles. A separate 20-seed baseline block (10042-10061) adds **80 trajectories**. All comparisons use shared outside draws within each condition and seed. Main-study extinctions total **1308/5600** across mixed conditions; that aggregate is not a baseline extinction probability.

Start with the [readable full report](evidence/2026-10-14/suite_report.md), the [study protocol](study_protocol.md), and the [assumption register and primary bibliography](research_basis.md). The [ODD specification](model_specification.md) connects the conceptual model to executable submodels.

## What Happens in the Baseline

The clearest baseline material contrast is top-two approval versus plurality: **+14.28 survival percentage points**, with a pointwise 95% interval [9.33, 19.68]. The separate seed block points in the same direction, with wider uncertainty. Both delegation survival intervals cross zero in the baseline; their concentration intervals are above zero among defined decision-time electorates. This does not show a material delegation advantage here, and it does expose a representation tradeoff. It is not a general result about real institutions or all possible parameter settings.

| Rule | Survival % | Extinct / runs | Population health (0-100) |
| --- | ---: | ---: | ---: |
| Plurality | 14.52 | 13/100 | 5.34 |
| Top-two approval | 28.80 | 5/100 | 10.11 |
| Expert delegation | 13.30 | 14/100 | 4.81 |
| Liquid delegation | 13.30 | 10/100 | 4.78 |

Survival counts every original resident. Population health assigns zero to deaths. Extinction is a trial with no remaining residents; a trial with one survivor is non-extinct but is not a successful colony. Read these columns together rather than interpreting mean health among survivors as population-wide wellbeing.

## How Large Are the Differences?

![Baseline paired differences and uncertainty](evidence/2026-10-14/baseline_paired_effects.png)

Cells below show mean difference [95% percentile bootstrap interval]; defined/total seed pairs. Survival uses percentage points; health uses score points on a 0-100 scale. Differences are rule minus plurality, not relative percent gains. The separate block uses only 20 seeds, so its estimates are less precise and remain separate from the main 100-seed results.

| Rule minus plurality | Baseline survival | Baseline population health | Separate-block survival |
| --- | --- | --- | --- |
| Top-two approval | 14.28 [9.33, 19.68]; 100/100 | 4.77 [2.77, 7.25]; 100/100 | 10.50 [3.50, 18.00]; 20/20 |
| Expert delegation | -1.22 [-3.02, 0.43]; 100/100 | -0.53 [-1.30, 0.24]; 100/100 | 1.12 [-1.75, 4.38]; 20/20 |
| Liquid delegation | -1.22 [-3.88, 0.98]; 100/100 | -0.56 [-1.35, 0.12]; 100/100 | 3.38 [-0.87, 8.00]; 20/20 |

An interval crossing zero leaves the direction unresolved at this precision; it does not establish equivalence. Excluding zero is pointwise exploratory evidence within this model. There is no multiplicity adjustment across the 84 primary material contrasts, and the development seed block was reused. Neither result licenses a general claim that delegation or direct voting is superior.

## Why Physical Assumptions Matter

![Survival across all conditions](evidence/2026-10-14/survival_by_condition.png)

| Condition | Survival range across rules % | Extinct / runs | Blocked / active cycles |
| --- | ---: | ---: | ---: |
| Authored baseline | 13.30-28.80 | 42/400 | 0/15525 |
| No energy replenishment | 0.00-0.00 | 400/400 | 1563/11506 |
| Energy replenishment: 1 | 13.28-28.62 | 44/400 | 0/15517 |
| Energy replenishment: 4 | 13.30-28.80 | 42/400 | 0/15525 |
| Medicine / health point: 0.5 | 13.30-28.80 | 42/400 | 0/15525 |
| Medicine / health point: 2 | 13.30-28.80 | 42/400 | 0/15525 |
| Lower shock probability (0.05) | 77.25-98.80 | 0/400 | 0/16000 |
| Higher shock probability (0.30) | 9.10-12.03 | 91/400 | 0/14825 |

Each sensitivity row changes one physical parameter around the authored baseline; the range describes the four rule means, not an uncertainty interval. Initial stocks, losses, and all other inputs stay fixed in those probes. Full per-rule values and paired effects appear in the report. The fixed no-shock production schedule remains evidence of finite-horizon feasibility, not evidence that voters find an optimal strategy or that every death is institutionally avoidable.

Blocked actions have no policy effects. Post-extinction recording cycles are counted separately, so extinction does not inflate the action-failure rate. A parameter can have little effect in the tested range when its physical constraint is rarely binding. Do not read a flat response as proof that energy or medicine never matters. This panel does not estimate interactions or global sensitivity.

Two concrete limits of this baseline are visible in the data. Increasing power generation from 2 to 4 leaves the final survival results unchanged; generation 1 also produces no physically blocked actions in this sample. The 0.5/2 medical conversion probes change medical reserves but leave final survival unchanged. Thus these ordinary-range probes do not show a survival benefit from extra power or cheaper care. The zero-generation stress is different: all 400 trials end in extinction. Under lower shock probability, no trial is extinct and rule mean survival ranges from 77.25% to 98.80%. Hazard assumptions strongly shape the scope for interpreting governance outcomes; no fuel or clinical calibration is established by these contrasts.

## Representation Has a Coverage Problem

Baseline original-priority satisfaction effects use **80-86 of 100** defined seed pairs across the three comparisons. These averages refer to the decision-time electorate in the final cycle. Its members can die later in that same cycle; even complete run coverage would not mean most original residents survived. The full report shows political means, defined-run counts, paired coverage, and concentration together.

Plurality and top-two approval retain individual ballot ownership, so their concentration is zero when defined. Delegation can concentrate ownership, but low concentration in a severely depleted electorate is not evidence of democratic success. Original-priority congruence measures rank agreement, not informed consent, successful policy delivery, procedural legitimacy, or preference intensity.

The equal-accuracy and fixed-preference conditions help challenge the information mechanism. They do not establish that real experts behave like these agents. Sparse/dense network conditions jointly change graph structure and edge density; role imbalance also changes generated prior distributions. Interpret them as bundled interventions, and do not treat overlapping intervals as a formal test of an interaction or difference of effects.

## What Is Now Defensible, and What Remains Open

The contribution is a reproducible, inspectable comparison with explicit stock budgets, assumptions, outcome definitions, matched trials, sensitivity probes, and preserved unfavorable/undefined results. The sources motivate the question and documentation method; they do not calibrate our numerical parameters. Tests and consistency checks support implementation claims, not empirical realism.

Next research priorities are domain-informed parameter ranges, independent replication, longer horizons and population scaling, behavioral alternatives, and interaction/global sensitivity analysis. A less lethal authored scenario may help inspect representation before population collapse; it must be declared as a new scenario rather than silently replacing this baseline. Meaningful formal invariants and actual optional-backend checks remain separate work.

## Retained Evidence and Verification

The [evidence directory](evidence/2026-10-14/suite_report.md) contains raw outcomes, complete configurations, all paired effects, lossless compressed per-seed differences, both figures, the separate seed block, source hashes, recorded project/test dependencies, and artifact checksums. It is not ignored by Git. Generated working copies remain under `results/research_review_2026-10-14/` and `results/research_holdout_2026-10-14/`.

The main suite passed consistency validation. **195 Python tests passed**, including parallel/sequential equality, missing-value/coverage presentation, units and unfavorable effects. Ruff and local-link/whitespace checks passed; figures were visually inspected. Lean, real SWI-Prolog integration, and a clean-room install were not checked by this study.
