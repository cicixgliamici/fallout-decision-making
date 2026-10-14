# Research Basis and Assumption Register

This is an exploratory computational study of institutions in a hypothetical
closed community. Its contribution is an inspectable comparison of decision
mechanisms under stated assumptions. It does not estimate what a real Vault,
lunar base, or human population would do. Numerical parameters are authored,
not fitted to empirical observations.

## Why This Question Is Worth Modeling

Information can be distributed unevenly while each person has a legitimate
claim to representation. Delegation might aggregate useful knowledge and also
concentrate ballot control. The experiment makes this tension explicit by
keeping material outcomes and representation as separate measurements.

Kahng, Mackenzie, and Procaccia study delegation under a binary correct-answer
model and find limits to guarantees from local delegation. Their result motivates
our refusal to assume expert delegation wins; it is not a theorem about our
four-action, repeated, resource-constrained model. [Primary paper](https://ojs.aaai.org/index.php/AAAI/article/view/11468).

Goelz and colleagues study how delegation can concentrate influence and examine
alternative delegation options. This motivates measuring actual ballot ownership.
Our maximum-share and concentration measures are descriptive, and we do not
implement their optimization algorithm. [Primary paper](https://arxiv.org/abs/1808.01906).

## Methodological Foundations

| Source | What we adopt | What it does not justify |
| --- | --- | --- |
| Epstein (2008), [Why Model?](https://www.jasss.org/11/4/12.html) | An explicit exploratory purpose distinct from prediction. | Realism of our parameters or empirical conclusions about institutions. |
| Grimm et al. (2020), [ODD protocol, second update](https://www.jasss.org/23/2/7.html) | A structured description of purpose, state, scheduling, design concepts, initialization, inputs, and submodels. See [model specification](model_specification.md). | Certification or validation merely from using the format. |
| Sargent (2011), [Verification and Validation of Simulation Models](https://www.informs-sim.org/wsc11papers/016.pdf) | Separate program correctness, conceptual assumptions, and evidence of accuracy for an intended application. | Calling passing unit tests empirical validation. |
| ten Broeke, van Voorn, and Ligtenberg (2016), [Which Sensitivity Analysis Method Should I Use for My Agent-Based Model?](https://www.jasss.org/19/1/5.html) | Interpret sensitivity in relation to model mechanisms and purpose. | Treating a few one-factor probes as a global sensitivity analysis. |

These primary sources were inspected on 2026-10-14. This is a focused starting
bibliography, not an exhaustive systematic review. A future empirical application
needs domain data and specialist review in addition to these methodological sources.

## Assumption Register

Every row below is a modeling choice, not an estimated property of real people.
Values describe the current Shelter Alpha baseline unless otherwise stated.

| Assumption | Reason for the current choice | Evidence and challenge |
| --- | --- | --- |
| 40 residents, 40 cycles; no spatial layout or calendar duration | Keep repeated choices and individual ballots inspectable. | Tests cover population changes; results are finite-horizon and population-specific. Longer horizons and scaling remain open. |
| Four mutually exclusive priorities | Make the opportunity cost of collective attention explicit. | Policies are aggregate actions, not a schedule of all ordinary work. An arbitrary action registry is not implemented. |
| Net food/water use 0.20/0.15 per resident; farming adds 14/12 | Provide at least one feasible prescribed response at full population rather than inevitable structural depletion. | A no-shock 40-cycle schedule preserves all 40 residents with actual accounting. This is feasibility, not ecological calibration or optimality. |
| Medicine production +8, routine use 0.04 per resident | Distinguish preparing medical supplies from background use and extra treatment. | Actual treatment spends stock. Conversion cost 0.5/1/2 is probed; no pharmaceutical production or clinical dose model is implied. |
| Power generation 2, capacity 50; costs 2 or 4 | Represent a bounded operating reserve and a larger security allocation cost. | Generation 0/1/2/4 is probed. No fuel, maintenance, or capacity sensitivity study is claimed. Initial reserves above capacity are preserved. |
| Treat below health 0.75; boost 0.08 with uniform variation; cost 1 per summed health point | Keep care allocation explicit with a finite stock budget and no patient-order preference. | Tests verify caps, spending and proportional rationing. Threshold, boost, and health-to-stock conversion are assumptions; clinical validation is absent. |
| Shock probability 0.22, fixed stock loss and health damage | Retain the owner's deliberately severe scenario, originally selected with an extinction-count target under the earlier engine. | This was scenario difficulty tuning, not empirical calibration. Do not retune to favor a rule; probe probabilities 0.05/0.22/0.30 and regenerate after mechanical changes. |
| Expertise accuracy 0.90 versus 0.55 | Give information quality an explicit mechanism without a productivity bonus. | Equal-accuracy ablation removes that advantage while retaining roles and priors. Accuracy is an error-spread parameter, not a probability of correctness. Correlated errors are absent. |
| Gaussian private signals, fixed original priorities, myopic reserve heuristic | Model imperfect assessment without claiming an optimal planner or validated psychology. | Fixed-ranking ablation addresses adaptation as a bundle. Noise, horizon, affordability score -1, and prior weight are still heuristic assumptions. Independent signals across scoring subcalculations do not form a coherent Bayesian stock belief. |
| Initial health normal(0.8, 0.15), clipped to [0.2, 1]; uniform roles unless configured | Provide synthetic heterogeneity, reproducible by seed. | Role imbalance changes more than the number of one specialist; initial priorities partly follow roles. Distributional and population-size sensitivity remain open. |
| Directed, static weighted trust; role-related generation and fixed delegation depth 3 | Make actual delegation paths inspectable without strategic learning. | Sparse/dense conditions jointly change topology and edge probability. They are network packages, not isolated causal tests of trust strength. |
| Elder as medicine specialist; engineer as defense specialist | Supply an explicit role-to-policy mapping for the finite action set. | An arbitrary domain abstraction, not a claim about professional competence. Role-map sensitivity remains open. |
| Deterministic policy-order tie-breaks and cycle fallback | Keep execution and original ballot ownership well defined. | Voting tests cover conservation, cycles, exclusions, and ties. Alternative tie-break/depth conventions remain open. |
| Survival/population health primary; political outcomes separate | Prevent a healthy minority or a depleted electorate from looking like general success. | Conditional outcomes show usable run and seed-pair counts. Coverage selection still limits interpretation. |
| Welfare weights 0.65 survival, 0.25 health, 0.10 reserves | Expose a declared crisis priority index rather than hiding a value judgment. | Three alternative weight profiles are exported. No welfare ranking defines an overall institutional winner. |

## What Is Verified, Explored, and Still Unvalidated

| Evidence level | Current evidence | Boundary |
| --- | --- | --- |
| Implementation verification | Tests for ballots, random streams, budgets, health and event reconstruction, paired alignment and reporting. | Tests can miss errors and do not establish empirical realism. |
| Internal model examination | Prescribed feasible schedule; controlled information/network comparisons; one-factor physical sensitivity panel. | Not exhaustive robustness, global sensitivity, or calibration. |
| Statistical estimation | Seed-matched effects with pointwise bootstrap intervals and explicit missingness. | Approximate intervals, multiple comparisons, model-defined uncertainty, and survivor/electorate selection. |
| Empirical validation | None against observed colony or human governance outcomes. | External predictions and policy recommendations are unsupported. |
| Formal/optional layers | Small Lean specification and optional Prolog checks. | No proof of the Python simulator; actual optional backends require separate verification. |

The defensible claim is conditional: changing a rule changes outcomes in this
specified simulation, and the direction and magnitude can depend on information,
network structure, and physical assumptions. Read the [study protocol](study_protocol.md)
and [current results](current_results.md) before generalizing that claim.
