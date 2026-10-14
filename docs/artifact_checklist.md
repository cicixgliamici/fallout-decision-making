# Review Checklist

This checklist separates implementation evidence from research and release work.
Check marks mean the feature exists and has Python evidence where applicable;
they do not imply empirical validation or verification of optional backends.
See [project status](project_status.md) for the dated check and exact configuration.

## Implemented and Checked Python Features

- [x] Package metadata and a CLI entry point are declared.
- [x] CLI smoke commands execute through the Python test harness.
- [x] Seeded runs can be reproduced.
- [x] External draws match across rules despite policy and mortality differences.
- [x] Paired comparisons reject missing/duplicate simulation pairs.
- [x] Conditional outcomes retain missing values and expose pair coverage.
- [x] Expertise affects private assessment accuracy; rankings can adapt to needs.
- [x] Survival, health, satisfaction, and actual ballot control are separated.
- [x] Welfare contributions, configurable priorities, and sensitivity profiles are exported.
- [x] Scenarios, metadata, validation results, and reports support reproduction.
- [x] Plain-language, code-reading, and presentation guides explain the model.

## Present but Requiring Separate Verification

- [ ] Verify actual SWI-Prolog integration and agreement with the intended fallback scope.
- [ ] Pin and compile the Lean toolchain; state the narrow meaning of its current proofs.
- [ ] Test package installation and resource discovery outside the source checkout.
- [ ] Pin or reconstruct a complete environment for an artifact release.
- [ ] Complete contributor/citation metadata before public publication.

## Research Work Remaining

- [x] Add bounded energy generation, atomic input affordability, and stock-budgeted treatment.
- [ ] Examine sensitivity, empirical plausibility, and scenario viability under these rules.
- [x] Supply a focused inspected primary-source bibliography and an explicit assumption register.
- [ ] Extend the literature review and obtain domain-specific empirical grounding.
- [x] Supply a dated exploratory results discussion with effects, uncertainty, coverage, and representation tradeoffs.
- [ ] Obtain independent replication and external/domain validation for an applied claim.
- [x] Declare a one-factor physical sensitivity panel without tuning a preferred rule to win.
- [ ] Extend sensitivity to interactions, alternative behavioral rules, population sizes, and longer horizons.

## Small Local Check

Run from the repository root after installation:

```bash
python -m pytest
pcds run --steps 2 --agents 8
pcds compare --steps 2 --runs 2 --agents 8 --output results/smoke.csv
```

These short commands verify the pipeline. They do not support a substantive
mechanism ranking. Longer reproduction commands are in [reproducibility](reproducibility.md).
