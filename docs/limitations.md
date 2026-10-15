# Limitations and Interpretation Boundaries

The project compares mechanisms inside explicit assumptions. It does not predict
real crises. The [status record](project_status.md) identifies checked behavior;
the [presentation guide](presentation_guide.md) explains how to state its scope.

## Material Dynamics Need Further Examination

The original 640-run review suite ended in extinction in 411 runs. Its archived
scenario consumes 28 water units per round for 40 members, while exploration
supplies at most 10. The default baseline now reduces net reserve consumption
and combines food production with water recovery; see
[resource balance](resource_balance.md). These are hypothetical design
assumptions, not empirically calibrated recycling rates. As members die,
consumption falls; mortality therefore still changes the later budget.

Policy effects, consumption, and health damage are assumed rather than fitted
to empirical observations. Energy now has bounded routine replenishment and
policy costs block unaffordable actions. Healing spends medicine in proportion
to actual recovery, with proportional rationing. Generation has no fuel or
maintenance model; the treatment threshold and medicine conversion are assumed,
not clinical estimates. Routine consumption is distinct from treatment spending
and still uses floors and shortage penalties. See [physical accounting](physical_accounting.md).
These are modeling choices, not evidence that a real institution would behave similarly.

## Information and Social Behavior Are Simplified

Information errors and specialist accuracy are assumed. Members use a stock,
healing, risk, and priority heuristic rather than an optimal or Bayesian planner.
Population and consumption settings are known; stocks and health summaries are
noisy. Policy-specific errors are independent, so correlated misinformation is
absent. Stock signals are resampled across scoring subcalculations rather than
maintained as one coherent posterior belief. Members do not foresee individual
shocks or realized exploration gains.

Trust does not learn or update, strategic manipulation and coalitions are not
implemented, and sanctions have no endogenous update process. Generated initial
priorities partly correlate with role. Explicit trust links supplement generated
links, and the scenario's `policies` list does not currently restrict the action
space. Manual rankings should include the four policies once each; not every
cross-field input requirement is enforced by the schema alone.

## Measurements Express Choices

Welfare weights and equal averaging of resource ratios are reporting conventions,
not measured universal utilities. The three alternative weight profiles illustrate
sensitivity without exhausting the possible weight space. Ordinal satisfaction
assumes equally spaced ranks. Low health dispersion can coexist with shared
illness or extinction. Ballot concentration excludes coercion, agenda-setting,
and broader informal influence. See [metric definitions](metrics.md).

## Statistical Uncertainty Has a Restricted Scope

Bootstrap intervals are approximate and can be unreliable with few defined seed
pairs. Multiple comparisons have no multiplicity adjustment. Conditional health
and political effects use subsets defined under both rules; those subsets can
be selected by the mechanisms and must be read beside all-seed survival and
population health. Matching external draws improves experimental control but
does not validate the model or eliminate every possible source of bias.

## Optional Layers and Release Readiness

Prolog now resolves the complete governance contract when its backend is loaded:
eligibility, delegation, tally, permissions and witnesses. Separate real-engine
tests compare these decisions and matched full trajectories with the retained
Python reference. The default Python test selection excludes native checks.
Finite differential coverage does not prove equivalence on every input. Lean now
proves selected invariants and certifies concrete translated witnesses, rather
than the whole simulator. See [certification scope](lean_certification.md).

The [governance contract](governance_contract.md) now supplies explicit input,
decision, witness, and error semantics with a standalone Python producer/checker.
Ordinary witnesses are not themselves Lean proofs or backend attestations.
`certify-governance` separately produces a kernel-checked concrete conformance
proof. General refinement, adapter correctness and runtime equivalence remain
open; JSON/schema validation, SHA-256 and literal translation are trusted.
Python still constructs snapshots, assesses preferences,
checks witnesses and applies physical effects. Per-round witnesses are checked
but not retained in ordinary simulation exports; standalone `govern` retains one.

Native reference versions and PySwip are pinned; other Python dependencies are
not fully pinned, and resource
paths assume a source checkout. Installation away from the checkout and complete
public-release metadata still need review. A focused [primary-source bibliography and assumption register](research_basis.md)
and [substantive results discussion](current_results.md) are now supplied.
This is not an exhaustive systematic review. Empirical validation, global
sensitivity/interaction analysis, and independent confirmation remain absent.
