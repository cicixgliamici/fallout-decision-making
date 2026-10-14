# Project Status and Review Readiness

Latest documentation and Python regression check: **2026-10-14**. Historical
calibration records are dated **2026-10-13**; the new accounting check below
is dated **2026-10-14**. Each verification applies
only to its stated configuration and scope.

## Current Position

The Python project is a functioning research prototype suitable for a technical
review or a discussion with an admissions board. It implements an interpretable
model and a reproducible experiment pipeline. It is not yet a completed,
empirically grounded scientific study.

| Area | Implemented evidence | Remaining boundary |
| --- | --- | --- |
| Simulation correctness | Death/exclusion handling, cycle fallbacks, population overrides, and vote conservation tests | Correct execution does not establish realistic dynamics. |
| Information and expertise | Adaptive rankings, private errors, specialist accuracy, and fixed/equal-accuracy comparisons | Accuracy levels and assessment heuristics are assumed. |
| Experimental control | Shared external draws, trace digests, seed pairs, bootstrap intervals, and parallel/sequential equality checks | Pointwise intervals, multiple comparisons, and conditional selection limit inference. |
| Metrics | Separate health, survival, satisfaction, and ballot control; explicit welfare assumptions | Normative indices do not define one universally best institution. |
| Research argument | Primary-source motivation, assumption register, ODD specification, and exploratory protocol | No empirical calibration or comprehensive global sensitivity study. |
| Reporting | Readable outcome/paired tables, figures, coverage, and source provenance | Visual clarity does not establish external validity. |
| Prolog | Optional eligibility/admissibility bridge and Python fallback | Real-engine equivalence has not been established by the recorded Python-only check. |
| Lean | Small definitions and proofs that mainly unpack those definitions | No proof of delegation termination, vote conservation, or simulator correctness. |

## Refreshed Research Study: 2026-10-14

The [current results and discussion](current_results.md) is now the main reviewer
entry point, with a [retained evidence snapshot](evidence/2026-10-14/suite_report.md).
The [research basis](research_basis.md) supplies inspected primary sources and an
assumption register; the [ODD specification](model_specification.md) and
[study protocol](study_protocol.md) expose the model and exploratory design.

- Regenerated **5,600 trajectories**: 14 conditions, four rules, 100 seeds per
  rule/condition (42-141), 40 cycles, 40 initial residents. The optional physical
  panel probes energy generation, treatment conversion costs, and lower hazards.
- A separate baseline block adds **80 trajectories**, seeds 10042-10061;
  it is analyzed separately and is not empirical validation.
- Main and separate-block consistency checks pass with **no errors or warnings**.
  The main outputs contain 56 summary rows, 784 effect rows, and 78,400 per-seed
  metric differences. There are 1,308 extinctions across mixed main conditions;
  the baseline alone records 42/400.
- Baseline survival means are 14.525% plurality, 28.80% top-two approval,
  and 13.30% for each delegation rule. Approval minus plurality is +14.275
  percentage points, with a pointwise 95% interval [9.325, 19.67625]. Both
  delegation survival intervals cross zero; concentration increases among their
  defined comparison electorates. See the results discussion for coverage,
  selection, multiple-comparison, and interpretation limits.
- No-generation trials all end in extinction (400/400). Lower-hazard trials
  have no extinctions, with rule mean survival 77.25-98.80%. Higher generation
  and the tested 0.5/2 medical conversion costs leave survival unchanged; this
  does not establish that these constraints are irrelevant outside the range.
- **195 Python tests passed**, including parallel/sequential output equality,
  sensitivity construction, report units, missing outcomes and coverage. Ruff,
  whitespace, local links, source/artifact hashes, archive reconstruction, and
  final visual inspection passed. An independent seed-42 replay matches all
  four corresponding main-study rows exactly.
- The report now separates readable tables/figures from full CSV downloads.
  Metadata includes complete condition configurations and normalized source
  hashes identifying uncommitted code. The approximately 4.5 MB evidence snapshot
  preserves raw outcomes and losslessly compressed differences outside ignored
  result directories, with recorded project/test dependencies and checksums.
- The baseline mechanics/parameters were preserved; condition execution can use
  independent processes (`--workers 4`) without changing seed ownership or row
  order. Earlier small runs remain historical; the new study supersedes their
  precision, not the scope of the model. Real SWI-Prolog, Lean, and clean-room
  installation were not checked.

## Documentation and Regression Check: 2026-10-14

- Separated AI coding instructions into root `AGENTS.md`; `Setting.md` now
  contains narrative design without the operational agent section.
- Added a [reader index](README.md) and a [development roadmap](roadmap.md),
  replacing the setting document's partly superseded milestone list.
- Re-ran the Python suite: **156 tests passed** (`python -m pytest -q`).
- Local Markdown file links resolve; `git diff --check` passed.
- No simulation code, scenario parameters, or numerical outputs changed.
  Existing numerical outputs do not need regeneration for this documentation update.
- This check did not re-run the large research suites, Ruff, Lean, or real
  SWI-Prolog integration. Earlier calibration records below retain their dates.

## Physical Accounting Revision: 2026-10-14

Bounded routine power generation now precedes assessment. All policy inputs
must be affordable before any effects occur, and treatment spends post-production
medical stock in proportion to actual health recovery. Limited supply scales all
patient requests by a common fraction. Adaptive assessments estimate these
constraints. See [physical accounting](physical_accounting.md) for parameters,
ordering, rationale, and the committed two-resident demonstration.

- Physics schema is `stock-budgeted-v2`; events use `simulation-events-v2`.
  CLI commands remain available, but physical outcomes and assessment scores
  change. Regenerate previous numerical results, including archived scenarios.
- Python regression suite: **186 tests passed**. Ruff, whitespace checks, and
  local Markdown file links passed. Tests include zero/exact/insufficient inputs,
  atomic failure, capped generation, stock-budgeted proportional care, patient
  ordering, replay, recording independence, and mixed-physics rejection.
- The 40-cycle no-shock prescribed schedule uses the baseline energy reserve,
  actual replenishment, and medical spending; all 40 residents survive and every
  scheduled action executes. This is finite-horizon feasibility, not indefinite
  sustainability or a claim that a voting mechanism finds the schedule.
- A small eight-condition suite uses seeds 42-46, five replications per rule,
  four rules, and 40 cycles: **160 runs**, 32 summary rows. Validation passes
  with the expected warning that fewer than 20 replications give limited
  confidence-interval evidence. Outputs and metadata are in
  `results/accounting_revision/suite/` (ignored by Git).
- The small suite records **71 extinctions out of 160**. Its baseline records
  7/20 extinctions and mean survival of 4-5.5% across rules. The new accounting
  does not make the severe baseline benign. These are small-sample diagnostics,
  not a mechanism ranking or a replacement for the old 400-run calibration.
- The runnable demonstration generates `results/accounting_demo/report.txt`
  and `events.json`: the first action is blocked by energy, the next restores
  0.02 total health using exactly the 0.02 medical units produced that cycle.
- Real SWI-Prolog and Lean were not run. No fuel, maintenance, infrastructure
  failure, or clinical protocol has been added.

## Earlier Verification: Original Resource Budget

- 140 Python tests passed; Ruff and whitespace checks passed.
- The suite used Shelter Alpha, seeds 42-61, 20 replications per rule/condition,
  four mechanisms, eight conditions, and 40 rounds per trajectory.
- It validated 640 raw runs, 32 rule/condition summary rows, 8,960 per-seed
  metric differences, and 448 paired-effect rows.
- Physical outcomes and external trace digests matched the preceding controlled
  suite after the metric changes. Reporting did not alter the simulated decisions.
- 411 runs ended without survivors. Undefined conditional outcomes were retained
  with explicit coverage rather than imputed as favorable or zero values.

The checked environment was Python 3.14.3, NumPy 2.3.5, NetworkX 3.6.1,
Polars 1.40.1, and Pydantic 2.13.4. These are recorded versions, not pinned
installation requirements. Lean compilation and real SWI-Prolog integration
were not part of that verification.

Inspect the archived resource budget with the current suite from the repository
root (the historical environmental-shock preset was 0.18; it is now 0.30):

```bash
pcds suite --scenario data/scenarios/shelter_alpha_legacy.json --runs 20 --steps 40 --seed 42 --output-dir results/review_snapshot
```

The result directory is ignored by Git. Keep generated metadata with any report
you share; this summary does not replace its raw data. Python 3.11-3.13 remain
the recommended installation range, while 3.14.3 is the recorded checked runtime.

## Superseded Low-Hazard Baseline Verification

Also recorded on **2026-10-13**, after the narrative/context and scenario update:

- 142 Python tests passed, including a finite-horizon budget-feasibility test;
  Ruff and whitespace checks passed.
- The baseline comparison used 100 seeds per rule (42–141), 40 cycles, and 40
  initial residents. Total extinctions fell from 184/400 to 0/400; mean survival
  under the new budget ranges from 92.55% to 100%, depending on the rule.
- External trace digests match between corresponding original/new baseline runs.
- The eight-condition suite validated 640 runs, with no validation warnings or
  errors, and recorded 44 extinctions. Severe scarcity retains only 9.03% of the
  initial population on average; zero extinction is not the definition of success.
- Complete new suite outputs and configurations are in `results/balanced_review/`;
  matched baseline CSVs and configurations are in `results/balance_check/`.
- Optional Lean and real SWI-Prolog checks were not run for this update.

See [resource balance](resource_balance.md) for assumptions, per-rule results,
reproduction commands, and the archived original scenario. Previous baseline
outputs must be regenerated rather than pooled with the new configuration.

The zero-extinction adjustment is now archived as
`data/scenarios/shelter_alpha_low_hazard.json`; its verification above is
historical. The current baseline raises external losses and fault frequency.
The proposed reusable connection between scenario mechanics and narrative
profiles is described in [context architecture](context_architecture.md).

## Current Difficulty Revision Verification

- The owner requested roughly 50 or more extinctions among 400 baseline cases.
  Hazard candidates 0.18 and 0.22 yielded 34 and 58 respectively; 0.22 is now
  selected, without choosing a favored voting rule.
- The 400 calibration runs use seeds 42-141, 40 residents, and 40 cycles.
  Average survival remains low (14-26%); this is a severe baseline, not evidence
  that every non-extinct colony succeeds.
- An independent holdout (seeds 1042-1061) records 5/80 extinctions. The requested
  count is therefore a sample difficulty target, not a guaranteed probability.
- 142 tests, Ruff, and whitespace checks pass after the change; the feasible
  no-shock production schedule remains available.
- Metadata and raw/paired outcomes are in `results/balance_revision/`.
- The environmental-shock suite preset is now 0.30, keeping it stronger than
  the 0.22 baseline. Previous suite outputs require their original preset.
- The revised eight-condition suite validated 640 runs without errors or
  warnings, recording 186 extinctions; complete outputs and configurations are
  in `results/balance_revision/suite/`.

## Deterministic Narrative and Event Verification

Also recorded on **2026-10-13**:

- Neutral, ordered event recording is opt-in; deterministic text reports support
  Vault 47, neutral, and custom JSON vocabulary profiles.
- All pre-existing round fields exactly matched a saved pre-change trajectory
  under four voting rules, 40 cycles, and seed 42 with recording enabled.
- Tests check recording-on/off equality, replay, resource/health reconstruction,
  stock floors, shortage timing, extinction, institutional overrides, and
  unchanged event exports across presentation profiles.
- 156 Python tests passed; Ruff and whitespace checks passed.
- A five-cycle, seed-42 expert-delegation example is available in
  `results/vault47/report.txt` and `results/vault47/events.json`.
- CSV metrics and physical assumptions are unchanged; previous numerical
  outputs need no regeneration for this observational addition.
- Real SWI-Prolog and Lean were not checked; the new override test uses a
  controlled bridge double.

See [event reports](event_reports.md) for commands, schema, and reuse details.

## Main Research Work Remaining

The baseline now offers a feasible finite-horizon food/water/medicine schedule
through explicit scenario assumptions; see [resource balance](resource_balance.md).
The original deficit-heavy scenario remains archived for comparison. This
adjustment does not establish empirical validity or indefinite sustainability.
Bounded routine power, upfront affordability, and proportional stock-budgeted
care are now implemented; see [physical accounting](physical_accounting.md).
Fuel, maintenance, and clinical treatment protocols remain abstract. Further
scenarios should examine sensitivity to generation, conversion cost, and input
constraints without tuning a preferred mechanism to win. Historical calibration
counts below the earlier checks do not describe the revised physical model.

The [research basis](research_basis.md) now connects the question to inspected
primary sources and records authored assumptions. The [ODD specification](model_specification.md)
and [study protocol](study_protocol.md) make the model and experimental design
inspectable; [current results](current_results.md) provides the substantive
results discussion and retained evidence. These are an initial exploratory study,
not empirical validation or an exhaustive literature review.

Remaining research includes domain-informed parameter ranges, broader behavioral
and population sensitivity, interactions, and independent replication. Before a
public artifact release, verify optional layers separately, test a reconstructed
clean environment and installation outside the repository, and complete contributor
and citation metadata. The recorded project/test dependency snapshot identifies
the checked environment but does not establish a portable lockfile or clean-room install.

See [limitations](limitations.md), [artifact checklist](artifact_checklist.md),
and [presentation guide](presentation_guide.md) for the corresponding boundaries
and review narrative.
