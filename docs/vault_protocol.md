# Vault 47 — Colony Governance Protocol

> OVERSEER RESEARCH TERMINAL  
> PROTOCOL 47-G / ISOLATED COLONY SELF-GOVERNMENT  
> Continued habitation is an outcome to be recorded, not an assumption.

This document supplies the fictional briefing and its explicit mapping to the
current simulator. It introduces no additional executable mechanics.

## Experimental Briefing

Vault 47 was designed to preserve a community beneath a devastated surface.
Its second purpose is to investigate whether that community can govern itself
when survival depends on limited reserves, uncertain information, and decisions
that cannot satisfy every need at once.

Forty residents share the shelter. Food production and water recovery compete
with medical attention, security, and expeditions for the colony's next priority
allocation. Specialists understand parts of the problem; none has a complete
or infallible view. Trust can place many residents' votes in a few hands.

The research protocol compares institutions capable of directing this isolated
colony. The motivating problem also applies to imagined lunar bases and
long-duration space settlements: how should people organize collective choices
when routine outside assistance is unavailable?

The Overseer reviews alternative simulated histories. Each history starts from
the same colony and encounters matched external conditions. Residents belong
to their own history; they do not know the results of another government.

> Administrative objective: preserve the colony.  
> Research obligation: retain the record when preservation fails.

## Colony Conditions

The executable baseline is
[`shelter_alpha.json`](../data/scenarios/shelter_alpha.json). Its technical name
remains **Shelter Alpha**; **Vault 47** is its narrative identity.

| Condition | Current baseline interpretation |
| --- | --- |
| Population | 40 generated residents with varied roles, health, priorities, and attitudes. Named characters are not part of this baseline. |
| Isolation | No rescue or routine supply-import action exists in the current policy set. Exploration provides uncertain supplies. |
| Initial reserves | 100 food, 100 water, 50 medicine, 50 energy, and 50 security units. |
| Routine reserve use | Per living resident and decision cycle: 0.20 food, 0.15 water, and 0.04 medicine. Food/water use represents net reserve draw after abstracted routine recovery. |
| Priority allocation | One of four policies is selected per cycle. Its resource effects are community-wide; it is an abstract colony priority, not an individual work assignment. |
| External pressure | Generic shocks and background health damage. The baseline shock probability is 0.22 per cycle; it is not a rate per day. |

Resource quantities are abstract model units, not liters, calories, or reactor
kilowatt-hours. Security is an aggregate readiness counter. The Vault's
hydroponics, recovery systems, infirmary, reactor, and airlock provide context;
they are not individually simulated infrastructure objects.

Routine activity is folded into the budget. Selecting medicine does not mean
residents stop eating or that every other activity physically shuts down.
The simulator adds the chosen policy's declared effects and then applies
consumption and pressure. Cycles have no assigned calendar duration or resident
shift schedule.

## Information and Participation

Living, unsanctioned residents participate. Roles identify policy expertise,
not additional voting rights. Default information accuracy is 0.90 in the
resident's specialist domain and 0.55 elsewhere; these values control estimation
error rather than the probability of making the right decision.

Residents privately estimate reserves and policy effects, then rank priorities.
Their preferences can change as conditions change. The scenario's parameters
and population define the experiment; noisy stock and health observations
represent incomplete information within it. Expertise improves estimates,
not actual production or healing. Trust links are directed and remain fixed
in the current model; there is no implemented process of earning trust.

| Protocol identifier | Institutional procedure |
| --- | --- |
| `majority` | First-choice plurality: the largest number of first-place votes wins, even without an absolute majority. |
| `approval` | Each resident approves their top two policies; the largest approval total wins. |
| `expert_delegation` | Transfer a ballot to the most trusted eligible specialist for the resident's first-choice policy, if available. The representative's current choice receives its weight. |
| `liquid_democracy` | Follow a bounded specialist-delegation chain. A cycle restores the original resident's ballot. |

No institution receives privileged resource effects. Sanctions are input state,
not punishments dynamically imposed by the Overseer. Optional Prolog policy
checks apply only when explicitly enabled; they are not a universal physical
affordability check.

## Evaluation Record

Material success means preserving residents, their health, and usable reserves.
The protocol also measures preference satisfaction and concentration of ballot
control. These outcomes must be read together: one survivor is not a successful
colony, and a healthy colony can still concentrate political power.

The review configuration uses 40 decision cycles and matched seeds across the
four institutions. Report mortality, population health, policy choices, and
representation alongside any welfare score. Do not declare an institution
universally best from one scenario or from its aggregate score alone.

The current baseline's difficulty was selected using an aggregate extinction
target. This is a declared design choice, not empirical evidence about human
colonies. See [resource balance](resource_balance.md) for calibration results,
independent seed checks, and assumptions.

## Interpretation Boundaries

Generic shocks remove reserves and damage health; they do not identify a
particular broken purifier, raider attack, or radiation event. Specific causes
require additional modeled events before they can be reported as facts.
Energy currently has no replenishment or universal affordability gate; healing
is not constrained by a patient-level medicine budget. The protocol does not
claim that these systems already provide complete physical accounting.

The fictional premise is original and Fallout-inspired. Lunar colonies are a
parallel motivation, not an implemented spaceflight model or a claim about
canonical Fallout lore. For each priority's exact meaning and effects, read the
[policy dictionary](policy_dictionary.md). For the reusable design, read
[context architecture](context_architecture.md).
