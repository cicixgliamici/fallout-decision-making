# Project Status and Review Readiness

Latest documentation and Python regression check: **2026-10-15**. Historical
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
| Prolog | Complete governance decisions and witnesses, matched Python comparisons, 112 real SWI-Prolog checks | Finite conformance coverage; native Windows SWI-Prolog was not checked. |
| Lean | Explicit library build, 17 new invariant/supporting theorems, and kernel-checked concrete governance certificates | JSON/literal adapter and universal runtime equivalence are not proved; physics is outside scope. |

## Lean Explanation Pass: 2026-10-15

- Added English explanations across the five maintained Lean files: data types,
  ordered expert selection, exact comparisons, delegation and tallying, permission
  overrides, concrete conformance and the reasoning behind the proof tactics.
  Comments distinguish the introductory examples from the contract model and
  identify external validation assumptions and remaining proof obligations.
- `lake build Wasteland` passed. A before/after comparison excluding comments
  and layout confirmed unchanged code and proof tokens in all five files. This
  pass added no theorem or mechanism and requires no numerical study rerun.
  Comment edits change source fingerprints; earlier certification receipts and
  evidence retain their original identities and have not been rewritten.

## First Lean Certificates: 2026-10-15

- **Partially implemented governance certification:**
  [the independent Lean model](../formal/lean/Wasteland/Governance.lean) computes
  contract-v1 decisions, including ordered greedy delegation, exact fractions,
  cycle/depth stopping, contributions, tally, deterministic winner, permissions
  and overrides. Its 17 new theorems prove selected invariants and supporting
  lemmas. In particular: bounded paths, cycle fallback, ballot count and voter
  coverage, winner maximality, tie preservation and selected-policy permission.
  Holder eligibility assumes next-hop closure; voter uniqueness assumes unique
  electorate identities. General declarative refinement remains open.
- Added [governance_lean.py](../src/pcds/governance_lean.py) and optional
  `pcds certify-governance`. It translates literal request/claim data, invokes the
  pinned Lean 4.19.0 library, and constructs a concrete `Conforms` proof with
  `by decide`, checked by the kernel. It does not call the Python semantic
  checker or use `native_decide`. Successful output includes readable proof
  source, compiled artifact and a receipt with hashes, source identity, axiom
  report and explicit scope. Failure cannot create a successful receipt.
- **Corrected the earlier build-evidence gap:** the library had no default
  target, so previous `lake build` success did not establish module compilation.
  Added a default target, changed the test to `lake build Wasteland`, required
  the compiled governance module, and fixed a standalone documentation-comment
  syntax error exposed in the older delegation file. The library now actually
  compiles. Historical evidence is retained with this correction, not relabeled.
- **309 ordinary Python tests passed** (117 native cases deselected), and
  **five separately selected Lean integration tests passed** (112 Prolog cases
  deselected), on Windows/Python 3.14.3. They check the explicit build, actual
  CLI proof/receipt, a rejected forged winner, eight valid rule/electorate cases,
  and proofs rejecting 15 altered witnesses. Cases include cycle fallback,
  tied trust, exact fraction transport, empty electorates, unusual names and
  reordered representative maps. Ruff and whitespace checks passed. The CI Lean
  job now selects all Lean tests and installs their Python dependencies; hosted
  CI was not observed.
- Produced a fresh response using actual SWI-Prolog 9.2.9/PySwip 0.3.3 in WSL,
  then certified it with Lean on Windows. The authored example contains an
  intermediate-node cycle and a forbidden winning policy. Retained
  [proof source and validation record](evidence/2026-10-15/lean_certification)
  document the exact inputs, hashes, environments and scope. The concrete proof
  reports the standard `propext` axiom; no custom axiom or `sorry` is introduced.
- JSON/schema validation, SHA-256 and faithful literal translation remain trusted
  Python responsibilities. Certification does not attest backend identity or
  prove arbitrary Python/Prolog executions, physical dynamics or empirical
  validity. The simulation does not automatically invoke Lean. Its mechanics,
  RNG keys and export schema are unchanged, so numerical studies need no
  regeneration for a mechanism change. No full research study or full native
  Prolog regression rerun was performed in this step; prior migration evidence
  retains its stated scope. See [the certification guide](lean_certification.md).

## Prolog Voting and Delegation Migration: 2026-10-15

- **Implemented:** the live simulator now uses the pure Prolog contract resolver
  when its native backend is available. Prolog owns eligibility, ordered expert
  selection, single-hop/liquid delegation, cycle/depth handling, contributions,
  tally, deterministic winner and post-election permissions. Every returned
  request-bound witness is checked independently before physical policy effects.
  This makes the governance procedure inspectable and separable from dynamics;
  no new physical or narrative mechanic was added.
- Added the exact snapshot adapter in `governance_prolog.py`, connected it to
  simulation and CLI, and retained `voting.py` as the migration reference.
  `--governance-resolver python_reference` on `run`, `compare` and `suite` keeps
  the previous resolver under the same institutional checks. `pcds govern
  --backend prolog` produces a standalone native decision/certificate and never
  falls back. Missing/version-mismatched backends and malformed/query/witness
  failures remain explicit errors. Optional startup fallback stays recorded.
- New round/event/CSV/suite provenance distinguishes the institutional backend
  from the actual `resolver`, `resolver_sha256` and `contract_version`. Pairing
  rejects mixed or partial identities while fully historical data stays readable.
  The existing scenario format, commands, RNG keys and Python-only default remain.
  Native snapshots enforce the declared contract domain. Certificates are checked
  each round but not retained in ordinary simulation exports.
- **296 ordinary Python tests passed**, with 113 native checks deselected;
  **112 real SWI-Prolog tests passed**, with one Lean check deselected, in
  WSL/Python 3.12.3 using SWI-Prolog 9.2.9 and PySwip 0.3.3. Coverage includes
  complete seeded snapshots, exact rational comparisons, trust/policy ties,
  cycles, depth limits, elders, unusual identities, permissions, empty/dead
  electorates, failed actions, full trajectories, parallel workers and CLI/suite
  metadata. Ruff and whitespace checks passed. Lean sources were unchanged and
  their separate build was not rerun; no new Lean theorem is claimed.
- The maintained [migration audit](../experiments/check_governance_migration.py)
  matched all **12 adaptive trajectory pairs / 480 rounds** across four rules
  and seeds 1, 42, 123, with eight residents and 40 rounds per trajectory.
  All recorded fields except backend identity matched, including effects,
  representative ownership, events and random draws. Its
  [retained record](evidence/2026-10-15/prolog_migration/migration_validation.json)
  includes complete inputs, source hashes and both runtime identities. The
  [native response](evidence/2026-10-15/prolog_migration/prolog_response.json)
  matches the published authored cycle/override example. Test evidence and its
  scope are in [checks.json](evidence/2026-10-15/prolog_migration/checks.json).
- Existing experiments retain their historical provenance. The matched checks
  support migration compatibility within their coverage, not universal equivalence
  or a claim that one institution performs better. Regenerate a study to describe
  its results as native Prolog executions. No full research suite or hosted CI was
  run. Python still owns private assessments, physics and witness checking; Lean
  soundness and connection to executable decisions remain future work.

The following dated sections retain the evidence and implementation boundaries
of their respective milestones.

## Governance Contract: 2026-10-15

- Implemented [contract version 1](governance_contract.md): decision-time input,
  full election/permission output, request-bound ballot witnesses, structured
  errors, and complete semantics for the current built-in profile. Published
  [request/response schemas and examples](../data/governance/v1).
- Added `governance_contract.py` and `governance_reference.py`. The producer
  wraps the existing Python voting resolver; an independent checker validates
  input binding, complete electorate/ballot coverage, greedy paths, cycle and
  depth stopping, all scores, deterministic ties, and post-election overrides.
- `pcds govern` and `pcds check-governance` expose this standalone boundary.
  They do not replace the live simulation path, load Prolog, or invoke Lean.
  Fractions preserve the exact numeric values of existing finite Python stocks
  and trust weights; no rounding or new physical mechanism was introduced.
- Preserved policy declaration order, outgoing-edge order on equal trust,
  fixed original delegation topics, original-voter cycle fallback, the three-hop
  budget, empty-electorate defaults, and permission overrides after tallying.
  The input domain explicitly excludes malformed rankings and custom k/depth
  settings; existing scenario/helper interfaces were not tightened.
- **287 ordinary Python tests passed**, with 18 native checks deselected;
  **17 real SWI-Prolog tests passed** in WSL/Python 3.12.3 with the pinned
  runtime. This includes one new contract-versus-core-rule integration test;
  delegation certificate production remains Python. The 79 contract tests cover
  actual adaptive-round comparisons, boundary values, CLI round trips, published
  schema/example consistency, and certificate tampering. Ruff and whitespace
  checks passed. Lean sources were unchanged and their separate build was not
  rerun in this step; the earlier dated Lean check remains its evidence.
- Existing numerical research outputs need no regeneration for a mechanic
  change: the live voting and simulation modules were not changed in this step.
  Source hashes include the new modules, so historical snapshots retain their
  recorded source identities. No full research study or hosted CI was run.
- The [worked request](../data/governance/v1/example_request.json) and
  [response](../data/governance/v1/example_response.json) demonstrate an
  intermediate-node cycle and a forbidden winning policy replaced after the
  vote. These are authored decision examples, not empirical results or a
  measured simulation trajectory. Validation provenance is retained in
  [the contract check record](evidence/2026-10-15/governance_contract_validation.json).
- Prolog production of these certificates and Lean soundness proofs are
  proposed next steps. The current witness is neither a Lean proof nor a
  backend attestation, and the checker does not verify physical dynamics.

## Native Integration Consolidation: 2026-10-15

- Implemented `--require-prolog` for `run`, `compare`, and `suite`, and matching
  Python API arguments. It implies enabled checks and rejects missing runtimes,
  mismatched versions, invalid files, or initialization failures with an explicit
  error. Query errors stop execution rather than switching backends mid-run.
- Fixed reference versions in [toolchains.toml](../toolchains.toml): SWI-Prolog
  9.2.9, PySwip 0.3.3, and Lean 4.19.0. PySwip dependency declarations and the
  Lean selector are pinned. The new CI configuration has separate Python,
  real-Prolog, and Lean jobs; the Prolog container also has a fixed image digest.
- New rounds, event logs, CSVs, terminal/text reports, and suite metadata identify
  the effective governance backend, mode, runtime versions, rule hash, and any
  fallback reason. Pairing rejects mixed governance identities within a condition.
  The legacy optional `--use-prolog` behavior remains available with recorded fallback.
- Corrected name quoting, cleared facts at their declared arities, preserved
  resource precision at permission thresholds, and checked predicates originate
  in the requested rule file. Process workers explicitly use spawn to avoid
  inheriting an initialized native interpreter on Unix.
- **208 ordinary Python tests passed**, with 17 native checks deselected.
  The process-worker regression passed again after selecting spawn explicitly.
  **16 real Prolog integration tests passed** on WSL Ubuntu/Python 3.12.3,
  against locally compiled SWI-Prolog 9.2.9 and PySwip 0.3.3. The source archive
  SHA-256 matched the official release. Pytest reported one shared-checkout
  cache-permission warning; assertions passed.
- **One separate Lean integration test passed** on Windows/Python 3.14.3:
  version 4.19.0 was checked and `lake build` succeeded. Ruff and
  `git diff --check` passed. Hosted CI, native Windows SWI-Prolog, and the full
  research study were not run.
- Retained a [three-round real-backend trace](evidence/2026-10-15/prolog_smoke.json)
  and [validation/environment record](evidence/2026-10-15/native_integration.json).
  These are integration evidence, not substantive governance findings.
- The default Python-only dynamics, scenario parameters, and random keys are
  unchanged. Prolog-enabled runs apply an additional institutional treatment;
  compare them separately from the historical Python-only study. New exports add
  backend columns; historical files do not establish native coverage. Source
  identities now include toolchain declarations and formal sources. Historical
  evidence is retained without relabeling its metadata.
- No new Lean theorem or Prolog delegation mechanism was introduced. Connecting
  certified decision semantics to Prolog execution remains proposed work.

## Python Explanation Pass: 2026-10-15

- Expanded English comments and docstrings across all 18 `src/pcds` modules
  and the three supplementary experiment scripts. Explanations cover ownership
  of state, round ordering, private assessments, ballot conservation, physical
  budgets, measurement denominators, paired inference, and presentation boundaries.
- Added a presentation-oriented reading route with concrete examples in the
  [code guide](code_guide.md#explaining-the-python-architecture-in-a-presentation).
- Compared every modified Python file with its Git HEAD version using ASTs
  with docstrings removed: executable structures are identical in all 21 files.
  No mechanics, parameters, interfaces, or random-event keys changed.
- **195 Python tests passed** (`python -m pytest -q`); Ruff checks of `src` and
  `experiments` and `git diff --check` passed.
- Numerical outputs do not need regeneration for this explanatory change.
  Source fingerprints include comments/docstrings, so their values change;
  retained evidence keeps its original provenance. Exact-source snapshot
  packaging requires the recorded revision or a new run against current sources.
- Large research suites, real SWI-Prolog integration, and Lean were not rerun.

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
