# Project Status and Review Readiness

Status snapshot: **2026-10-13**. This is a dated verification record, not a claim
that future changes automatically inherit these results.

## Current Position

The Python project is a functioning research prototype suitable for a technical
review or a discussion with an admissions board. It implements an interpretable
model and a reproducible experiment pipeline. It is not yet a completed,
empirically grounded scientific study.

| Area | Implemented evidence | Remaining boundary |
| --- | --- | --- |
| Simulation correctness | Death/exclusion handling, cycle fallbacks, population overrides, and vote conservation tests | Correct execution does not establish realistic dynamics. |
| Information and expertise | Adaptive rankings, private errors, specialist accuracy, and fixed/equal-accuracy comparisons | Accuracy levels and assessment heuristics are assumed. |
| Experimental control | Shared external draws, trace digests, seed pairs, and bootstrap intervals | Small samples, multiple comparisons, and conditional selection limit inference. |
| Metrics | Separate health, survival, satisfaction, and ballot control; explicit welfare assumptions | Normative indices do not define one universally best institution. |
| Prolog | Optional eligibility/admissibility bridge and Python fallback | Real-engine equivalence has not been established by the recorded Python-only check. |
| Lean | Small definitions and proofs that mainly unpack those definitions | No proof of delegation termination, vote conservation, or simulator correctness. |

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
Energy is not replenished
by current policies, and expenditure is floored at zero rather than universally
blocking actions. Medicine's healing effect is not constrained by stock or
patient-level allocation. These assumptions can dominate differences between
decision mechanisms. Further scenarios should expose this, not be tuned to make
a preferred mechanism win.

Next connect the research question and assumptions to relevant scholarship,
analyze substantive results and tradeoffs, and assess sensitivity beyond the
current presets. A reviewed bibliography has not yet been supplied. Before a
public artifact release, verify optional layers separately, pin/reconstruct the
environment, check installation outside the repository, and complete contributor
and citation metadata.

See [limitations](limitations.md), [artifact checklist](artifact_checklist.md),
and [presentation guide](presentation_guide.md) for the corresponding boundaries
and review narrative.
