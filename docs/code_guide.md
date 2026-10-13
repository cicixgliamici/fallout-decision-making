# Code Reading Guide

Start with the [walkthrough](walkthrough.md). Then follow the modules below;
reading every file in repository order is unnecessary.

## From an Input to a Recorded Outcome

| File | What to look for | Question it answers |
| --- | --- | --- |
| [scenarios.py](../src/pcds/scenarios.py) | `Scenario`, `load_scenario` | What comes from the input file, and which defaults are supplied? |
| [models.py](../src/pcds/models.py) | `Agent`, `PolicyImpact`, `SimulationParameters`, `RoundResult` | What information is stored, and which values are constrained? |
| [factory.py](../src/pcds/factory.py) | `create_agents_for_scenario`, `create_trust_graph_for_scenario` | How are members and trust relationships constructed? |
| [simulation.py](../src/pcds/simulation.py) | `run_simulation` | In what order do observation, voting, policy effects, and environmental pressure happen? |
| [assessment.py](../src/pcds/assessment.py) | `assess_policy`, `update_preferences` | How can imperfect information change a member's current ranking? |
| [voting.py](../src/pcds/voting.py) | `voting_outcome`, `_resolve_delegate` | Which policy wins, and who actually controls each original ballot? |
| [randomness.py](../src/pcds/randomness.py) | `event_rng`, `sample_environment` | How do different mechanisms share external conditions? |
| [metrics.py](../src/pcds/metrics.py) | `welfare_components`, `preference_satisfaction`, `delegation_power` | Which quantities are measured, and whose outcomes count? |

An underscore at the start of a function name marks an internal helper.
`run_simulation` assembles the process; its helpers keep specific calculations
separate. `models.py` uses Pydantic to read typed data and check declared bounds;
that validation does not establish that assumptions are realistic.

## From Trajectories to Comparisons

[compare_rules](../src/pcds/simulation.py) runs the mechanisms using the same seed
schedule and exports their final outcomes. It does not calculate paired
confidence intervals by itself.

[paired_analysis.py](../src/pcds/paired_analysis.py) matches rows by experiment,
run, and seed, subtracts within each pair, and estimates uncertainty by
resampling those differences. It preserves rows with undefined conditional
outcomes and reports how many pairs support each estimate.

[experiments.py](../src/pcds/experiments.py) applies the eight predefined
conditions, validates outputs, and writes data, metadata, and a report.
[metric_definitions.py](../src/pcds/metric_definitions.py) centralizes the metric
names, interpretation directions, and which quantities may be undefined.
[cli.py](../src/pcds/cli.py) connects these functions to the `pcds` commands.

## Important Values to Follow

- `agents`: all original members, including those who later die. Keeping them
  preserves the original denominator and their event identities.
- `eligible_agents`: the current decision-time electorate, a subset of members.
- `state`: shared stocks, updated in place during a trajectory.
- `parameters`: assumptions about effects, consumption, information, and reporting.
- `priors`: original policy rankings, retained when current rankings change.
- `outcome.representatives`: original voter to terminal ballot-holder mapping.
- `results`: one `RoundResult` per step, even after extinction.

Satisfaction is measured before effects. Survival and health are measured
afterward. Their denominators are intentionally different; do not move either
measurement across those stages without reconsidering its meaning.

## How to Change Assumptions Responsibly

Use a separate JSON scenario for alternative resource budgets, impacts,
information quality, or welfare weights. Do not alter voting code simply to
make a preferred mechanism win. Keep the baseline configuration and seed
schedule when making a controlled comparison.

Some fields are descriptive or reserved: `Scenario.policies` does not currently
restrict the four-policy action space, and sanctions have no endogenous update
process. Explicit trust edges supplement generated edges. These details matter
when constructing a hand-authored scenario; see [limitations](limitations.md).

## Optional Layers and Tests

[prolog_rules.py](../src/pcds/prolog_rules.py) bridges to the optional
[governance rules](../rules/governance.pl). Python still resolves delegations.
The [Lean directory](../formal/lean/Wasteland) contains definitions and small
proofs; it is not a translation or verification of the simulation.

Use tests as concrete examples: [assessment tests](../tests/test_assessment.py)
cover information and changing needs; [voting tests](../tests/test_voting.py)
cover delegation; [randomness tests](../tests/test_randomness.py) cover shared
external events; [metric tests](../tests/test_metrics.py) cover interpretation
pitfalls; [paired-analysis tests](../tests/test_paired_analysis.py) cover
statistical alignment and undefined outcomes. Passing them is evidence about
implementation behavior, not empirical validity.


## Inspect a Few Rounds in Python

After installation, save or run this small example from the repository root:

```python
from pcds.simulation import run_simulation

trajectory = run_simulation("liquid_democracy", steps=5, n_agents=8, seed=42)
for observation in trajectory:
    print(
        observation.step + 1,  # Stored steps start at zero; display rounds from one.
        observation.selected_policy.value,
        observation.survivors,
        observation.eligible_voters,
    )
```

Each printed line shows the round, selected policy, end-of-round survivors, and
members eligible before its effects. They can differ if someone dies during that
round. Inspect `observation.vote_representatives` to follow a delegated ballot
and `observation.welfare_components` to see the material score's contributions.
