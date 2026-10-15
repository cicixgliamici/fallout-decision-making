# Model Specification

This description uses the seven ODD elements in
[Grimm et al. (2020)](https://www.jasss.org/23/2/7.html). The format organizes
our own model; it does not establish its realism. Equations and parameter details
remain in [model](model.md), [physical accounting](physical_accounting.md), and
[metrics](metrics.md). The [assumption register](research_basis.md) explains why
the choices were made and how they are challenged.

## 1. Purpose and Patterns

Explore how direct voting and topic-based delegation affect survival, population
health, preference congruence, and concentration of ballot ownership under scarce
resources and imperfect information. Evaluation patterns are internal: conserve
original ballots, reproduce a seeded run, retain matched outside draws, respect
stock budgets, and allow a documented no-shock full-population schedule. These
are implementation/model checks, not fitted patterns observed in real colonies.

## 2. Entities, State Variables and Scales

| Entity | State | Scale |
| --- | --- | --- |
| Resident | Name, role, alive/sanctioned flags, health, risk aversion, cooperation, ordinal priorities, assessment scores, optional accuracy overrides. | One original person; health [0,1]; stable identity retained after death. |
| Trust network | Directed edges with trust weights. | Population graph; no geographic space or endogenous trust update. |
| Community | Food, water, medicine, energy, security. | Nonnegative abstract stocks/readiness; production is community-wide, routine use is per living person. |
| Decision | Eligible residents, current rankings, rule, original-ballot representative mapping, selected action and execution status. | One collective allocation per cycle. |
| Environment | Keyed shock draw and per-person potential background damage. | One cycle; drawn for all original identities to preserve comparisons. |
| Record | Before/after resource and health transactions, final metrics, optional neutral events. | Decision-time representation and end-of-cycle material observations are distinct. |

There is no geographic distance, real-day conversion, birth, immigration, rescue,
or population replacement. Default experiments use 40 original residents and 40
cycles. Death reduces subsequent consumption and changes future electorates.

## 3. Process Overview and Scheduling

For each cycle, sample the outside draw schedule, replenish bounded power if
any resident is alive, compute private assessments/rankings, determine eligibility,
and resolve the selected voting mechanism. Optional institutional checks may
replace a disallowed action. Record decision-time congruence and ballot ownership.

The physical gate checks all upfront inputs. A blocked action remains selected
but produces no effects. Otherwise debit costs, apply stock production/changes,
allocate stock-budgeted care proportionally, and apply policy injury risks.
Consume routine supplies using the then-living population. Check shortages,
apply shock losses and direct damage, add background damage, mark threshold
deaths, then measure end-state outcomes. Shock losses do not trigger a second
shortage check in the same cycle. See `run_simulation` and its helpers in
[simulation.py](../src/pcds/simulation.py).

Fixed-length observations continue after extinction, with a farming recording
default, no policy execution/generation, and undefined conditional outcomes.
This default is not an election result. A living but wholly excluded electorate
retains the existing recording default and physical handling; sanctions have
no endogenous update process in this study.

## 4. Design Concepts

- **Basic principles:** finite resource budgets, heterogeneous information,
  collective decisions, and explicit representation tradeoffs.
- **Emergence:** selected-policy sequences, mortality trajectories, and terminal
  ballot concentration follow from mechanisms and assumptions; outcomes are not
  scripted by narrative profiles.
- **Adaptation/objectives:** residents score estimated reserve benefits, healing,
  injuries, and stable prior priorities. This is a heuristic, not optimal control.
- **Learning/prediction:** rankings adapt to current needs, but trust and accuracy
  do not learn; reserve horizons define targets, not forward policy rollouts.
- **Sensing:** private noisy stocks, effects and health summaries; specialist
  accuracy reduces error spread for one domain. No foreknowledge of realized shocks.
- **Interaction/collectives:** one shared material state; topic-based delegation
  to trusted eligible specialists. No strategic coalitions or behavioral factions.
- **Stochasticity:** generated populations/trust, private errors, exploration
  gains, treatment boosts, injuries, shocks and background loss use recorded seeds.
- **Observation:** trajectories, paired final outcomes, actual ballot mappings,
  and opt-in events; narrative rendering cannot mutate state or consume randomness.

## 5. Initialization

Load a validated [scenario](../data/scenarios/shelter_alpha.json). Generated roles
are uniform unless relative role weights are supplied. Initial rankings are
shuffled, then promoted to place the role-related policy first with probability
0.55. This promotion does not imply exactly 55% of residents end with that first
choice because the shuffle can already place it first. Risk aversion and
cooperation are uniform [0,1); health is a clipped normal draw (mean 0.8, standard
deviation 0.15, bounds 0.2 and 1). Named residents may be authored instead.

Trust construction examines ordered distinct resident pairs with topology-specific
edge probabilities and weights uniform from 0.5 to 1, rounded to three decimals.
Explicit edges supplement/overwrite generated edges. These are synthetic
assumptions; they are not observations. Exact construction is in
[factory.py](../src/pcds/factory.py); initial stocks and parameters are embedded
in experiment metadata.

## 6. Input Data

Inputs are JSON configurations and seeds, not empirical time series. All four
policy identifiers remain executable regardless of the descriptive scenario
`policies` list. Recorded configurations expose base and condition overrides.
Optional Prolog checks are disabled in ordinary suite comparisons. There is no
external narrative or user intervention during a research trajectory.

## 7. Submodels

| Submodel | Definition and implementation |
| --- | --- |
| Private assessment | Noisy stock/effect scoring, perceived affordability, expected stock-budgeted healing; [assessment.py](../src/pcds/assessment.py), [model equations](model.md). |
| Voting/delegation | First-choice plurality, top-two approval, one-hop expertise delegation, depth-3 liquid chains with cycle fallback; [Prolog resolver](../rules/governance_decision.pl), retained [Python reference](../src/pcds/voting.py), [methods](methods.md). |
| Physical budgets | Upfront costs, bounded routine power, policy effects, proportional treatment and policy injuries; [accounting rules](physical_accounting.md). |
| External pressure | Routine consumption, fixed shortage penalties, keyed shocks and per-resident damage, irreversible threshold deaths; [simulation.py](../src/pcds/simulation.py). |
| Measurement | Separate survival, population/conditional health, congruence, ballot ownership, stocks and explicit normative welfare; [metrics](metrics.md). |
| Experimental inference | Match experiment/run/seed; subtract within each pair; percentile bootstrap over seed differences; [methods](methods.md), [study protocol](study_protocol.md). |

A complete reading combines this specification, the linked equations, actual
scenario configuration, and recorded source hashes. None of these substitutes
for empirical validation.
