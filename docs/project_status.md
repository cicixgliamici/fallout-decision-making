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

## Recorded Verification

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

Generate the same suite configuration from the repository root:

```bash
pcds suite --runs 20 --steps 40 --seed 42 --output-dir results/review_snapshot
```

The result directory is ignored by Git. Keep generated metadata with any report
you share; this summary does not replace its raw data. Python 3.11-3.13 remain
the recommended installation range, while 3.14.3 is the recorded checked runtime.

## Main Research Work Remaining

First examine whether the material dynamics offer genuinely different feasible
responses to scarcity. Initially, 40 members consume 28 units of water per round,
while the default exploration gain is between 0 and 10. Energy is not replenished
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
