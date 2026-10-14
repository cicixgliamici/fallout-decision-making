# Methods

The artifact compares voting mechanisms with seeded stochastic simulation.

Here, a seed identifies a repeatable trial and a trajectory is its sequence of
rounds. Start with the [walkthrough](walkthrough.md) for the process or the
[glossary](glossary.md) for statistical terms. This page explains experimental
control and uncertainty, not empirical validation of the model.

Each run starts from a JSON scenario. Agents are generated or loaded, a directed
trust graph is constructed, and the chosen voting rule selects a policy at each
step. The same random seed schedule gives mechanisms identical initial
populations and trust graphs. Private assessment noise uses streams keyed by
seed, round, agent name, and policy, separate from physical dynamics. The same
keys reproduce the same noise draws across rules, although observations differ
when the underlying states diverge. Environmental shocks are keyed only by seed
and round; background health damage is keyed by seed, round, and agent name.
Potential exposure is sampled for every original agent, including dead members,
so mortality cannot shift another agent's draws. Only living agents receive the
damage. Policy effects have separate keys for policy, resource, and agent.
The same policy applied to the same agent in the same round has the same random
draw, although actual treatment can depend on their current health.

All rules therefore encounter identical external draws for a given seed and
scenario, even when their selected policies and survivor counts diverge.
Resource consumption, scarcity damage, and survival remain endogenous outcomes
and can differ. `event-keyed-v1` records the randomness scheme; historical
outputs from the former shared stream must be regenerated.

The implemented mechanisms are intentionally simple baselines:

- majority: first-place plurality with deterministic tie-breaking;
- approval: top-k approval, default k=2;
- expert delegation: delegate to the most trusted eligible expert for the
  voter's preferred topic;
- liquid democracy: bounded delegation chains with cycle fallback.

Delegation ignores dead, sanctioned, and unknown recipients even when historical
trust links remain in the graph. An agent without an eligible trusted expert
votes directly. Liquid democracy follows the most trusted eligible expert at
each hop: revisiting an agent restores the original voter's ballot, while reaching
the depth limit uses the current representative. Equal-trust choices retain graph
edge order. With no eligible voters, all rules retain the farming default so
fixed-length trajectories can still be recorded after extinction.

Results should be reported with raw data, means, confidence intervals, and the
exact scenario configuration. The `stock-budgeted-v2` physics schema identifies
bounded power generation, action affordability, and stock-budgeted treatment.
These change physical outcomes and assessments: regenerate older outputs.
Random event keys and metric definitions are unchanged. Pairing rejects mixed
physics schemas when that column is supplied; historical files without it must
be kept separate. See [physical accounting](physical_accounting.md).

The suite adds a fixed-preference baseline and an equal-accuracy comparison to
the scarcity/network conditions. Equal accuracy sets specialist accuracy to
general accuracy, including per-agent overrides, while retaining roles, initial
priorities, and trust. It isolates the specialist information advantage within
the adaptive model. Fixed mode isolates the replacement of static ballots as a
whole; it does not isolate an individual scoring assumption.

## Paired Inference

For each experiment, metric, and rule, the elementary observation is:

```text
difference(seed) = outcome(rule, seed) - outcome(majority, seed)
```

Pairing uses `(experiment, run_id, seed)`. Duplicate seeds/run identifiers,
missing baselines, incomplete pairs, invalid non-finite metrics, and mismatched external
trace digests are rejected. The raw results store each run's shock count and a
SHA-256 digest of the full external draw trace. Round snapshots retain the
individual draws; metadata records the scheme and scenario configuration.

The effects table reports the mean difference, sample standard deviation of
differences, standard error, and a 95% percentile bootstrap interval. Each
bootstrap draw resamples the seed-level differences with replacement, then takes
their mean. The endpoints are the 2.5th and 97.5th percentiles of 2,000 such
means. Bootstrap randomness is separate and keyed by experiment, rule, and
metric, making row reordering irrelevant. No trajectories or agents within a
seed are treated as independent replications.

At least two defined pairs are needed; a single-run smoke test reports null interval
endpoints rather than zero-width uncertainty. Constant observed differences
can produce a degenerate interval with multiple pairs. Small-sample and
degenerate bootstrap intervals need cautious interpretation: they do not prove
the population effect is known exactly. Rule-level summary intervals retain
the normal approximation and are descriptive, not intervals on rule differences.

Conditional survivor-health, satisfaction, and power outcomes remain undefined
without their corresponding population. Their differences retain all matched
seed rows, while effect estimates use pairs defined in both rules and report
coverage explicitly. Missing simulation pairs remain errors. Interpretation of
these selected subsets must include all-seed survival/population-health outcomes;
see [metric definitions](metrics.md).

## Research Design and Evidence Level

The [study protocol](study_protocol.md) states the exploratory comparisons,
primary outcomes, physical sensitivity ranges, reused seed block, and comparison
family. It was written after earlier development runs and is not preregistration.
The [research basis](research_basis.md) distinguishes the literature motivating
the question from the uncalibrated numerical assumptions. The
[ODD specification](model_specification.md) makes state, timing, and submodels
inspectable. None establishes empirical validation or family-wide error control.

The generated report leads with survival percentages, extinction counts,
population health, and active-versus-inactive execution diagnostics. Its baseline
figure and paired table use signed differences with confidence intervals and
coverage; a separate conditional table shows political means and defined-run
counts. All original numerical CSVs remain available for detailed audit.
