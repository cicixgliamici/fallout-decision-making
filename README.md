# Post-Crisis Collective Decision Simulator

**Vault 47 — isolated colony governance experiment.** Forty residents live in a
Fallout-inspired underground Vault. The experimental premise is to investigate
how people can govern an isolated colony with finite supplies, incomplete
information, and competing needs: conditions also relevant to imagined lunar
bases and long-duration space missions. Different voting and delegation rules
face the same starting conditions and external pressures. Success is assessed
through survival, health, reserves, representation, and concentration of power.

Read [Setting and narrative design](Setting.md) for the fictional context.
The [Vault 47 protocol](docs/vault_protocol.md) introduces the colony experiment;
the [policy dictionary](docs/policy_dictionary.md) connects each Vault priority
to its implemented effects and limits.
Generate a factual terminal record with the
[deterministic report and event log](docs/event_reports.md).
The current implementation is a simulator; no playable shifts or incident
interface are introduced by this narrative framing.

A research prototype that asks how a community should make collective decisions
when food, water, medicine, energy, and security are limited. It compares direct
voting with delegation to trusted specialists, then measures the consequences
for survival, health, preferences, and control of votes.

An **agent** is a simulated community member. A **policy** is the action chosen
for one round. A **scenario** is a JSON file describing the starting community
and the assumptions used by the model. The post-crisis setting makes the
problem concrete; the project provides a model for investigation rather than
predictions about real communities.

## Start Reading Here

| Your purpose | Recommended document |
| --- | --- |
| Enter the Vault setting and understand its choices | [Experiment protocol](docs/vault_protocol.md), [policy dictionary](docs/policy_dictionary.md) |
| Follow a simulated colony's decisions and incidents | [Deterministic reports and event records](docs/event_reports.md) |
| Understand the project without reading code | [Plain-language walkthrough](docs/walkthrough.md) |
| Explain it to a reviewer or admissions board | [Presentation guide](docs/presentation_guide.md) |
| See what is ready and what still needs work | [Project status](docs/project_status.md) |
| Follow the implementation | [Code reading guide](docs/code_guide.md) |
| Understand terms such as seed, bootstrap, and concentration | [Glossary](docs/glossary.md) |
| Examine the assumptions and measurements | [Model](docs/model.md), [metrics](docs/metrics.md), [methods](docs/methods.md) |
| Run and reproduce experiments | [Reproducibility](docs/reproducibility.md), [experiment outputs](docs/experiments.md) |

## Research Question

Under scarcity, when do delegation mechanisms improve material outcomes, and
what happens to preference satisfaction and concentration of voting power?

This connects political and social questions about representation, trust, and
expertise with computer science through simulation, voting algorithms,
reproducible experiments, and a small formal specification. Strategic voting,
coalitions, and equilibria are future extensions, not implemented game-theory
results. See [research question](docs/research_question.md).

## What Happens in One Round

1. Members estimate current needs and policy effects using imperfect information.
2. They update their policy rankings; specialists usually have more accurate
   estimates in their own domain under the default settings.
3. Eligible members vote directly or delegate according to the selected rule.
4. The chosen policy changes stocks and health. Consumption and environmental
   pressure then affect the community.
5. The simulator records both material outcomes and decision-time representation.

The four policies are farming, medicine, defense, and exploration. Their effects
are scenario assumptions. Expertise changes information quality, not the actual
productivity of a policy. More accurate information does not guarantee a better
collective outcome.

## Decision Rules

| CLI name | Meaning |
| --- | --- |
| `majority` | First-choice plurality: the policy with the most first-place votes wins. It need not receive more than half the votes. The identifier is retained for compatibility. |
| `approval` | Each member approves their two highest-ranked policies; the largest approval total wins. |
| `expert_delegation` | A member transfers their vote to the most trusted eligible specialist for their current first-choice policy, when one exists. |
| `liquid_democracy` | Delegation follows a bounded chain of eligible specialists; cycles restore the original vote. |

Equal policy scores use declaration order as the tie-breaker. With no eligible
voters, the code selects farming as a recording default; that is not an election
result. Fixed-length trajectories continue after extinction so comparisons keep
the same observation horizon.

## Install and Try It

Run commands from the repository root. Python 3.11-3.13 remain the recommended
range; the recorded review check also passed on Python 3.14.3. That is a checked
environment, not a guarantee for every dependency version or operating system.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate  # Linux/macOS
python -m pip install -e ".[dev]"
python -m pytest
```

```bash
pcds run --rule majority --steps 5 --agents 8 --seed 42
pcds run --rule expert_delegation --steps 5 --seed 42 --report results/vault47/report.txt --event-log results/vault47/events.json
pcds compare --steps 2 --runs 2 --agents 8 --output results/smoke.csv
pcds suite --runs 20 --steps 40 --seed 42 --output-dir results/review_snapshot
```

The first two commands are small demonstrations. The suite takes longer and
writes raw data, per-seed differences, summaries, confidence intervals,
configuration metadata, validation results, and a Markdown report. The default
suite uses 100 replications per rule and condition; the command above uses 20.

`--agents N` replaces a generated population size. Without it, the scenario
controls population size (40 in Shelter Alpha). Named-agent scenarios reject
resizing because their identities and trust links are part of the input.

## Reading Results Responsibly

Rules share initial conditions and external random events for a given seed and
scenario. Comparisons subtract outcomes within each seed before estimating
uncertainty. Confidence intervals describe variability within this model; they
do not validate the model's assumptions.

Read survival, survivor/population health, preference satisfaction, and actual
ballot concentration together. Welfare weights and resource reference stocks
are configurable under `parameters.metrics`. The report also scores identical
outcomes under three alternative weight profiles. Undefined conditional outcomes
remain blank, with the number of usable runs and pairs shown explicitly.

Adaptive assessments are configured under `parameters.decision`. Use
`"mode": "fixed"` for static rankings, or equal specialist/general accuracy to
remove the information advantage. The suite includes these comparisons.

The earlier check on 2026-10-13 validated 640 simulations at 40 rounds;
411 ended without survivors under the original resource budget. The baseline
now uses lower net consumption and a combined food-production/water-recovery
policy, with a subsequent hazard revision recording 58 extinctions among 400
baseline trials. See [resource balance](docs/resource_balance.md) for the rationale and
new checks, and [project status](docs/project_status.md) for verification scope.

See [context architecture](docs/context_architecture.md) for the
connection between reusable mechanics, scenario assumptions, and narrative
profiles. Deterministic text reports and replaceable vocabulary profiles are
implemented; specific infrastructure incidents remain future work.

## Components and Their Actual Scope

| Component | Responsibility | Boundary |
| --- | --- | --- |
| Python | Community generation, private assessments, voting, physical dynamics, metrics, experiments, and CLI | The main runnable research prototype. |
| Prolog | Optional voting-eligibility and policy-admissibility checks | Delegation resolution stays in Python; declared Prolog delegation predicates are not called by that resolver. |
| Lean 4 | Small definitions of ballots, winners, and a delegation relation | Current proofs largely unpack definitions; they do not verify the simulator or its results. |

Without `--use-prolog`, governance admissibility checks are not applied. When
that option is enabled, the bridge uses a Python fallback if Prolog cannot be
loaded. Optional integration details are in [governance rules](docs/rules.md).
To check the Lean sources separately, an installed Lean toolchain is needed:

```bash
cd formal/lean
lake build
```

## Repository Map

```text
src/pcds/              implementation and command-line interface
rules/                 optional Prolog rules
formal/lean/           small Lean specification
experiments/           supplementary plotting script
docs/                  explanations, assumptions, methods, and review notes
tests/                 Python unit and integration tests
data/scenarios/        scenario inputs
```

## Claims and Evidence

| Claim | Evidence |
| --- | --- |
| Different rules face identical external draws for a given seed and scenario. | `tests/test_randomness.py`, recorded external-trace digests |
| Effects use matched seeds with explicit uncertainty and coverage. | `tests/test_paired_analysis.py`, paired CSV exports |
| Expertise changes assessment accuracy and rankings can respond to needs. | `tests/test_assessment.py`, `src/pcds/assessment.py` |
| Metrics expose welfare assumptions and actual ballot control. | `tests/test_metrics.py`, `tests/test_voting.py`, `docs/metrics.md` |
| Optional governance and formal sources have deliberately limited scope. | `docs/rules.md`, `formal/lean/Wasteland/*.lean` |

See [limitations](docs/limitations.md) before interpreting results. Outputs using
a different randomness or metric schema must be regenerated. Recommended review
work includes scenario calibration, a literature-grounded research argument,
analysis of substantive results, and separate verification of optional layers.
