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
| [events.py](../src/pcds/events.py) | `SimulationEvent`, `EventRecorder` | Which ordered physical facts are captured when recording is enabled? |
| [narrative.py](../src/pcds/narrative.py) | `NarrativeProfile`, `render_report`, `export_event_log` | How do the same records produce different presentations without changing outcomes? |
| [metrics.py](../src/pcds/metrics.py) | `welfare_components`, `preference_satisfaction`, `delegation_power` | Which quantities are measured, and whose outcomes count? |

An underscore at the start of a function name marks an internal helper.
`run_simulation` assembles the process; its helpers keep specific calculations
separate. `models.py` uses Pydantic to read typed data and check declared bounds;
that validation does not establish that assumptions are realistic.

## Explaining the Python Architecture in a Presentation

English module docstrings describe each component's responsibility; inline
comments explain the model choices at the point where they take effect. The
following route connects a short oral explanation to concrete code:

1. **Inputs:** show `Scenario` and `CommunityState`. The JSON file declares the
   population, initial stocks, and assumptions; Pydantic checks declared types
   and bounds. The loaded scenario can override the Python parameter defaults.
2. **One round:** follow the four stage comments in `run_simulation`: prepare
   exposure and stocks, form rankings and vote, apply physical effects, record
   measurements. Mutable agents and stocks belong to that trajectory.
3. **Individual judgment:** show `assess_policy`. Private estimates balance
   reserves, healing, injury risk, and original priorities. Expertise narrows
   estimation error; this is a heuristic rather than an optimal planner.
4. **Collective choice:** show `VotingOutcome` and `_resolve_delegate`. Each
   original eligible ballot has one terminal holder. For example, a mapping
   `{"a": "b", "b": "b"}` gives `b` two votes, whose concentration can be measured.
5. **Fair comparisons:** show `event_rng` and `compare_rules`. Shared event
   identities preserve outside draws across rules; resulting stocks and health
   can diverge. One complete trajectory contributes one trial to inference.
6. **Interpretation:** show `population_health` and `build_paired_differences`.
   Deaths remain in the population-health denominator, and effects are computed
   within matched trials before estimating uncertainty. These comparisons remain
   conditional on the model assumptions.
7. **Presentation:** show `render_report`. Profiles change vocabulary around
   recorded facts, independently of the simulation's decisions and random draws.

The `experiments/` scripts are supplementary: one draws a welfare-only example,
one packages validated review evidence, and one writes the dated study discussion.
Their comments distinguish demonstration settings and historical interpretation
from the general research pipeline.

Comments and docstrings do not change numerical mechanisms. They do change the
source-content hashes recorded by `source_fingerprints`, which intentionally
includes explanatory text. Existing evidence keeps its original provenance;
packaging an old run against edited sources can fail the exact-source check.
Reproduce the recorded source revision or generate a new run when packaging a
new snapshot, rather than replacing historical hashes.

## Physical Budgets

In `simulation.py`, `_replenish_energy` runs before assessments.
`_policy_block_reason` checks the inputs returned by `PolicyImpact.required_inputs`
before `_apply_policy` mutates any stock. `_apply_treatment` caps requests,
shares available medicine proportionally, and records actual expenditure.
`RoundResult.policy_executed` and `policy_block_reason` distinguish a selection
from successful execution. See [physical accounting](physical_accounting.md)
for the ordering, parameter rationale, and a runnable example.

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

The [versioned governance contract](governance_contract.md) is a standalone
decision boundary used by the native simulation path.
[governance_contract.py](../src/pcds/governance_contract.py) validates snapshots
and defines request/response/certificate schemas;
[governance_reference.py](../src/pcds/governance_reference.py) wraps the existing
reference resolver and independently checks witnesses from either producer.
[governance_prolog.py](../src/pcds/governance_prolog.py) transports exact snapshots
to [governance_decision.pl](../rules/governance_decision.pl), which produces the
complete decision without Python voting callbacks. `pcds govern --backend prolog`
and `pcds check-governance` expose this boundary without claiming Lean certification.

[prolog_rules.py](../src/pcds/prolog_rules.py) bridges to the optional
[governance rules](../rules/governance.pl). A loaded native backend uses the pure
Prolog resolver by default; `--governance-resolver python_reference` preserves
the previous implementation with identical institutional checks for comparison.
The [Lean decision model](../formal/lean/Wasteland/Governance.lean) computes the
contract independently and proves selected invariants. [governance_lean.py](../src/pcds/governance_lean.py)
translates data into a concrete `Conforms` proposition and invokes pinned Lean
through `pcds certify-governance`. The kernel checks `by decide`; no Python
semantic acceptance is trusted. See [certification scope](lean_certification.md)
for the JSON/translation trust boundary and remaining proofs.

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
