# Governance Rules and Optional Layers

This page distinguishes institutional permission from physical consequences.
A policy can be permitted by a rule while the physical model still has unrealistic
resource constraints. The [walkthrough](walkthrough.md) explains where these
checks occur in a round.

## What the Python Simulator Uses

Without `--use-prolog`, eligibility is checked in Python: members must be alive
and unsanctioned. Policy-admissibility checks from the optional bridge are not
applied. Python resolves trust-based delegation in every mode.

With `--use-prolog`, [PrologRuleEngine](../src/pcds/prolog_rules.py) mirrors current
members, trust links, and stocks into logical facts before checking eligibility
and policy permission. If SWI-Prolog, PySwip, or the rule file cannot be loaded,
the bridge sets `available` to false and uses its Python fallback. Enabling the
option therefore does not prove the real Prolog engine was used; inspect that
flag when testing the integration.

## Current Policy Permission

| Policy | Requirement in the optional rule layer |
| --- | --- |
| Farming | Always allowed. |
| Medicine | Always allowed. |
| Defense | Energy at least 2. |
| Exploration | Energy at least 2 and security at least 15. |

The thresholds are institutional assumptions, not a complete affordability
check. For example, default defense costs 4 energy units despite its permission
threshold of 2. Physical expenditure is floored at zero and does not universally
prevent action. The Python fallback mirrors these core permission thresholds;
real-engine equivalence still needs a separate integration check.

If a chosen policy is prohibited, the simulator takes the first allowed policy
in declaration order. Under the default rules this is farming. The fallback is
simple and deterministic, not an optimization of community outcomes.

## Declared Delegation Rules

[governance.pl](../rules/governance.pl) also declares role-based expertise and
`can_delegate/3`. These declarations illustrate logical rules but are not queried
by the Python delegation resolver. Their role map is not identical: Python also
treats elders as medicine specialists, while the Prolog declarations do not.
Do not claim that Prolog currently controls the simulator's delegation chains.

Generated member names use simple lowercase identifiers. The bridge's `_atom`
helper only replaces dashes; it is not a general quoting/sanitization function
for arbitrary authored names. Real-engine testing should use appropriate atom
identifiers and check the actual loaded backend.

## Lean's Different Role

The [Lean sources](../formal/lean/Wasteland) define a small policy set, formal
agents, ballots, score winners, and a direct delegation relation. Current proofs
largely unpack those definitions. They do not verify health dynamics, statistical
outputs, vote conservation, chain termination, or equivalence with Python.
The Lean toolchain is optional and currently uses a rolling `stable` selector;
pin and compile it separately before making reproducibility claims about that
layer.
