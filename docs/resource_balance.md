# Vault 47 Resource Balance

The baseline models an isolated colony testing collective self-government under
finite supplies. Its Fallout-inspired setting gives the experiment context;
imagined lunar bases and long-duration space missions motivate the same question.
This update adds context and changes scenario assumptions, without adding shifts,
factions, or an incident engine.

The calibration results on this page are historical, from before the
2026-10-14 [physical accounting revision](physical_accounting.md). Re-running
these commands now uses new mechanics, including for the archived scenarios.

## Why the Original Budget Failed

With 40 residents, the original scenario consumed 32 food and 28 water units per
decision cycle. Farming produced 14 food and consumed another 3 water;
exploration produced at most 14 food and 10 water. Even selecting the largest
possible gain every cycle could not replenish consumption at full population.
The earlier eight-condition review recorded 411 extinctions among 640 runs.
Those outcomes cannot be attributed solely to governance.

## Declared Baseline Assumptions

| Quantity | Original | Rebalanced baseline |
| --- | ---: | ---: |
| Food use per living resident/cycle | 0.80 | 0.20 |
| Water use per living resident/cycle | 0.70 | 0.15 |
| Medicine use per living resident/cycle | 0.08 | 0.04 |
| Farming food gain | 14 | 14 |
| Farming water change | -3 | +12 |

Food and water consumption now represent **net draw on reserves after routine
recovery**, rather than gross biological requirements. The farming policy
bundles hydroponic food production and additional water recovery. These abstract
units are explicit design assumptions, not measured recycling efficiencies.
Other policy impacts, mortality penalties, information accuracy, and voting
algorithms are unchanged. Policy effects remain community-wide; resizing the
population does not automatically resize production.

For 40 residents, a ten-cycle schedule of six farming, three medicine, and one
defense action supplies 84 food, 72 water, and 24 medicine against demand of
80, 60, and 16 respectively, before the new stock-budgeted treatment spending. This leaves room for medical and security decisions;
it does not guarantee that imperfectly informed voters find that schedule.
Exploration remains an uncertain alternative with injury risk. The first
adjustment changed the resource budget without targeting an extinction count.
The subsequent difficulty revision explicitly targets roughly 50 or more total
extinctions among the 400 calibration runs, at the project owner's request.
This is a scenario-design objective, not empirical calibration or evidence for
a favored voting rule. No rule's ranking is a selection target.

The current baseline retains this resource budget but increases external shock
probability from 0.05 to 0.22. Per-shock losses are now 12 food, 10 water,
4 medicine, and 6 security units, with 0.025 direct health damage. This creates
failure through adverse conditions while preserving an available no-shock
production schedule. The low-hazard, zero-observed-extinction adjustment is
archived as `data/scenarios/shelter_alpha_low_hazard.json`.

The suite's environmental-shock condition now uses probability 0.30 with the
same losses. This intentional preset change keeps stress conditions distinct
from the baseline; old suite figures require their original preset (0.18).

The original JSON is preserved as
[`shelter_alpha_legacy.json`](../data/scenarios/shelter_alpha_legacy.json).
The default file and technical identifier remain Shelter Alpha for compatibility;
its description now identifies the Vault 47 narrative. The suite retains its
separate severe-scarcity consumption overrides.

## Verification and Reproduction

The current feasibility test executes the schedule for 40 cycles using the
baseline energy reserve of 50, bounded routine replenishment, stock-budgeted
treatment, no external shocks, and the existing background health damage.
Every scheduled action must pass the actual affordability gate.
All original residents survive and food, water, and medicine remain positive.
This demonstrates an available response under stated conditions, not an optimal
policy or unlimited sustainability.

Run the matched-seed baseline comparisons:

```bash
pcds compare --scenario data/scenarios/shelter_alpha_legacy.json --runs 100 --steps 40 --seed 42 --output results/balance_before.csv
pcds compare --scenario data/scenarios/shelter_alpha.json --runs 100 --steps 40 --seed 42 --output results/balance_after.csv
pcds suite --runs 20 --steps 40 --seed 42 --output-dir results/balance_revision/suite
python -m pytest
```

The baseline comparison uses four rules and seeds 42–141: 400 runs per budget.
The suite uses eight conditions, four rules, and seeds 42–61: 640 runs.
Generated CSVs and suite metadata are stored under the ignored `results/`
directory. Read extinction counts together with surviving population and health;
having one survivor is not a successful colony.

The **superseded low-hazard adjustment** was recorded on 2026-10-13, at 40
cycles and 40 initial residents; the following figures do not describe the
current higher-hazard baseline:

| Rule | Original extinctions / 100 | Rebalanced extinctions / 100 | Original mean survival | Rebalanced mean survival | Rebalanced population health |
| --- | ---: | ---: | ---: | ---: | ---: |
| Plurality (`majority`) | 36 | 0 | 2.38% | 93.75% | 0.650 |
| Approval | 76 | 0 | 0.98% | 100.00% | 0.771 |
| Expert delegation | 36 | 0 | 2.40% | 95.13% | 0.693 |
| Liquid democracy | 36 | 0 | 2.38% | 92.55% | 0.656 |

The baseline comparison has **184/400 original extinctions and 0/400 after
rebalancing**. External trace digests match for every corresponding rule/seed
across budgets. These 400-run baseline counts differ from the earlier 640-run
eight-condition suite; they are not interchangeable. Zero observed extinctions
does not establish zero extinction probability or survival beyond this horizon.
Rule rankings are conditional on this budget and assessment model.

The rebalanced eight-condition suite validated all 640 runs and recorded
**44 extinctions**, compared with 411 in the earlier original-budget suite.
The new extinctions occur under fixed preferences (29/80), environmental shocks
(12/80), and severe scarcity (3/80). Severe scarcity still leaves only 9.03% of
the original population alive on average; environmental shocks leave 22.94%.
Low extinction counts therefore do not imply that the stress conditions became
successful colonies. Other conditions recorded no total extinctions.

All **142 Python tests**, Ruff, and whitespace checks passed. The suite's
validation record contains no errors or warnings. Lean and real SWI-Prolog were
not checked as part of this scenario-only update.

## Current Difficulty Revision

The calibration compared two hazard probabilities with identical loss sizes:
0.18 produced 34/400 extinctions; 0.22 produced **58/400**, so 0.22 was selected.
The seeds were 42-141, with 100 runs per rule, 40 residents, and 40 cycles.

| Rule | Extinctions / 100 | Mean survival | Population health |
| --- | ---: | ---: | ---: |
| Plurality (`majority`) | 17 | 14.33% | 0.048 |
| Approval | 7 | 25.83% | 0.085 |
| Expert delegation | 16 | 14.95% | 0.056 |
| Liquid democracy | 18 | 14.10% | 0.053 |

An independent seed range (1042-1061, 20 runs per rule) recorded 5/80
extinctions: plurality 3, approval 0, expert delegation 2, liquid democracy 0.
This shows that the requested count is a calibration-sample difficulty target,
not a guaranteed rate on other samples. The holdout did not select parameters.

The requested extinction count is met, but the baseline is still harsh: average
survival is only 14-26%, and conditional survival is not colony success. Future
balancing should consider population losses and recovery, not optimize only the
binary extinction count. Results from these selected seeds are design evidence;
they do not establish general superiority of one governance mechanism.

Raw candidate/holdout results, paired differences, effects, and calibration
metadata are in `results/balance_revision/`. Metadata records the target and
selected scenario; both candidate configurations are retained. The existing
no-shock finite-horizon feasibility test still passes for the revised baseline.
All 142 Python tests, Ruff, and whitespace checks passed after the revision.

The revised eight-condition suite validated 640 runs with no errors or warnings
and recorded 186 extinctions: baseline 20/80, equal accuracy 13/80, expertise
imbalance 16/80, fixed preferences 57/80, high trust 16/80, low trust 14/80,
environmental shocks 29/80, and severe scarcity 21/80. Its baseline uses only
seeds 42-61, so its extinction rate differs from the 100-seed calibration.
The stronger shock condition leaves 5.63% of the original population alive on
average; severe scarcity leaves 4.00%. Reports and complete scenario metadata
are in `results/balance_revision/suite/`.

## Accounting Revision

These gaps are now addressed by [physical accounting](physical_accounting.md):
bounded routine energy generation, upfront input checks, and proportional
stock-budgeted treatment. The recorded extinction counts above precede this
revision. They remain historical evidence, not results for the new engine.
Fuel, maintenance, and empirical calibration remain outside scope.

Existing numerical outputs must be regenerated for the new baseline. Randomness
keys and metric definitions are unchanged; within each budget, the mechanisms
still share external draws. Comparing the two budgets changes assumptions and
is not an estimate of the effect of governance alone.
