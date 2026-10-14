# Development Roadmap

Planning snapshot: **2026-10-14**. The accounting milestone is implemented; remaining rows are proposed
priorities. See [project status](project_status.md) for dated verification and
[limitations](limitations.md) for interpretation boundaries.

## Current Foundation

The Python engine loads scenarios, creates residents and trust links, updates
rankings from imperfect assessments, resolves one of four voting mechanisms,
and applies policy and environmental effects. It records health, survival,
resources, preference satisfaction, and actual ballot ownership.

The CLI supports individual runs, repeated comparisons, and an eight-condition
experiment suite with paired differences, bootstrap intervals, coverage,
configuration metadata, and validation. Optional ordered events support factual,
deterministic Vault or neutral reports without changing numerical outcomes.

Prolog adds optional institutional checks with a Python fallback. Lean contains
small definitions and introductory proofs. Neither verifies the Python engine.

## Recommended Sequence

| Priority | Proposed work | Why it matters | Completion evidence |
| --- | --- | --- | --- |
| 1 (implemented) | Close physical accounting gaps | Bounded power generation, atomic affordability checks, and proportionally rationed medical spending now apply. | See [physical accounting](physical_accounting.md) for rules, tests, examples, and regeneration requirements. |
| 2 (initial study implemented) | Build a defensible research argument | Primary-source motivation, an assumption register, ODD specification, and exploratory sensitivity protocol are supplied. | See [research basis](research_basis.md), [study protocol](study_protocol.md), and [current results](current_results.md). Empirical calibration, wider sensitivity/interaction analysis, and independent confirmation remain open. |
| 3 | Author one infrastructure crisis | One traceable water-recovery failure makes the setting concrete without requiring a large event catalogue. | Validated scenario state, onset and recovery rules, explicit physical consequences, ordered events, and same-seed cross-rule comparisons. Reports must reflect modeled causes. |
| 4 | Add evolving trust, then social groups | Fixed trust limits questions about accountability and institutional adaptation. | Declared update and observation rules, bounded trust, deterministic replay, power-concentration metrics, and sensitivity checks. Faction labels remain descriptive until behavior is specified. |
| 5 | Add an inspection interface | A terminal or dashboard can help readers inspect ballots and consequences. | Readable state and event views, representative paths and same-seed replay; display does not alter outcomes. Keep automated research comparisons intervention-free. |
| 6 | Strengthen formal and release evidence | Reviewers need to know exactly what is verified and how to reproduce it. Packaging work can begin earlier. | Real SWI-Prolog checks, pinned/compiled Lean tooling, meaningful invariants with explicit correspondence to Python, reproducible dependencies, installation outside checkout, CI and complete citation metadata. |

## Scope Decisions Before Expanding

Prefer scenario parameters when a new colony uses the existing four policies.
Changing Vault labels to lunar-base labels is already possible through narrative
profiles; this does not create new physical mechanics. Arbitrary action sets
require an engine extension: policy identifiers and expertise mappings are
currently fixed, and the scenario's `policies` list does not restrict execution.

Introduce one mechanism at a time, stating its update order, observed inputs,
state changes, and measurements. Preserve an archived configuration when changing
the baseline. Mechanical changes require new experimental outputs; presentation
changes should preserve them and be checked for that invariant.

The accounting example is implemented. A useful next deliverable is one
crisis: scenario -> decision -> physical consequence -> factual report ->
matched comparison. More characters or UI screens alone do not close the
current research gaps.
