# Connecting the Experiment and Its Setting

Status: neutral event recording, deterministic reports, and replaceable
vocabulary profiles are implemented. Further physical extensions are proposed.

The first documentation step is complete:
[Vault 47 experiment protocol](vault_protocol.md) and
[policy/resource dictionary](policy_dictionary.md). The next steps are also
implemented: [ordered events, profile loading, and deterministic rendering](event_reports.md).

Vault 47 investigates governance in an isolated colony with finite supplies.
The setting should explain the experiment's conditions and make its consequences
readable. The same mechanism should also support a lunar base, a polar station,
or a neutral research presentation.

## Three Responsibilities

| Layer | Owns | Example |
| --- | --- | --- |
| Simulation engine | Decision rules, state transitions, random event identities, and measurements | A shortage causes declared health damage; delegated ballots are resolved. |
| Scenario model | Starting population, stocks, production, consumption, hazards, and constraints | An isolated colony recovers water while producing food; a fault removes reserves. |
| Narrative profile | Location, institutional premise, labels, briefings, and factual report templates | The external resource-loss event appears as a recorded incident in the Overseer's archive. |

The engine receives validated mechanical inputs. It emits a trace. The narrative
profile reads that trace and produces text, with no access to mutate simulation
state or consume its random streams. A scenario may be paired with several
profiles: Vault 47, lunar colony, and a neutral presentation can describe the
same mechanics and obtain identical numerical results.

The current scenario schema already configures population, trust, resources,
policy impacts, and shocks. Profiles are loaded separately by the presentation
module, and the engine optionally records neutral events. Its four policy
identifiers are fixed in a Python enum, so reuse is
currently limited to scenarios expressible with those actions. Arbitrary domains
would later require a validated action registry and configurable expertise
mapping; that is a separate engine extension.

## Make the Fiction Explain the Assumptions

Start the experiment with a short protocol defining:

- Why this colony is isolated and cannot call for routine rescue.
- What its reserves, abstract resource units, and recovery rates mean.
- Which needs compete for the collective decision budget.
- What residents know and what specialists estimate more accurately.
- What the analyst measures: survival, health, reserves, representation, and power.

Explain that one selected policy is a colony-wide priority allocation. Routine
life support is abstracted into the net consumption budget; residents do not
stop eating or working whenever another policy wins. Simulation cycles need
not be presented as work shifts or assigned a calendar duration.

Use a compact scenario manifest and a separate narrative profile. Future
mechanical identifiers should remain neutral (for example, a water reserve
loss); the profile supplies a Vault-specific title. Label a cause as fictional
interpretation unless the trace actually identifies the failed subsystem.
The current generic shock affects several reserves at once and cannot truthfully
be presented as a specifically simulated purifier failure.

## A Shared Trace Is the Connection

The existing round results record selected policy, final resources, survivors,
health, preferences, representative ownership, and external draws. A first
renderer can already produce factual summaries from those records.

Neutral, typed event records now provide explicit ordering:
policy applied, resource change, external shock, shortage, treatment, injury,
and death. They record before/after values and modeled causes when applicable. A
resource total alone cannot distinguish consumption from an incident loss.
Individual names or death causes must not be invented from aggregate counts.

Example using illustrative, not measured, values:

```text
VAULT 47 / GOVERNANCE PROTOCOL: EXPERT DELEGATION
Priority allocation: hydroponics and water recovery [farming]
Eligible residents: 40
Largest representative ballot share: 20%
Water reserve: 18 -> 24 units
External stock-loss incident: recorded
Living residents at cycle end: 39/40
```

The neutral report uses the same facts with neutral labels. The narrative
renderer must not say that delegation caused a death merely because the death
followed that vote. Cross-rule results and physical event traces answer
different explanatory questions.

## Improve Mechanics Through the Scenario Boundary

Bounded routine energy replenishment, universal action affordability, and
stock-budgeted treatment are implemented; see [physical accounting](physical_accounting.md).
Their effects are neutral resource transactions and explicit blocked-action
records, independent of the report profile. Reactor and infirmary labels are
presentation, not extra infrastructure mechanics.

Only afterward introduce specific infrastructure failures with declared effects,
such as reduced water recovery. Mechanical events belong in scenario dynamics;
their warnings and archive entries belong in the narrative profile. An event
with physical effects must occur equally with narrative output enabled or
disabled. Named residents can be added through the existing authored-agent
schema; faction membership should remain descriptive until it has an explicit,
tested behavioral rule.

## Smallest Useful Implementation

1. Completed: experiment protocol and policy/resource dictionary for Vault 47.
2. Completed: vocabulary profiles and a deterministic renderer.
3. Completed: show the same run as a Vault report and a neutral report; verify identical
   simulation data with either profile or with narration disabled.
4. Completed: neutral, ordered event records with actual state changes.
5. Completed: bounded energy generation, upfront action costs, and stock-budgeted treatment.
6. Proposed: specific infrastructure incidents, keeping profile changes independent
   from mechanical configuration changes.

This creates one inspectable experiment with two readings: a colony's history
and the computational evidence behind it. No TUI, work-shift system, or large
event catalogue is needed to establish that connection.
