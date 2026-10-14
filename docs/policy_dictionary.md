# Vault 47 — Priority Allocation Dictionary

This dictionary connects the four existing policy identifiers to the Vault's
context. Labels describe the current baseline; they do not add actions or
replace identifiers in JSON, CLI output, voting, or experiment data.

Values come from
[`shelter_alpha.json`](../data/scenarios/shelter_alpha.json) and describe policy
effects **before** consumption, scarcity damage, and external shocks. Another
scenario can configure different effects for the same identifiers.

## Policy Labels and Effects

| Engine identifier | Vault priority | Energy cost | Shared reserve/readiness changes |
| --- | --- | ---: | --- |
| `farming` | Hydroponic production and water recovery | 2 | +14 food, +12 water |
| `medicine` | Infirmary support and medical supply preparation | 2 | +8 medicine |
| `defense` | Shelter security and access readiness | 4 | +9 security |
| `exploration` | Surface supply expedition | 2 | Food 0–14, water 0–10, medicine 0–5; respective expected gains 7, 5, and 2.5 |

Reserve changes and energy costs are community-wide abstract units per selected
action. Positive exploration gains are independently drawn from uniform ranges;
the three realized amounts need not move together. Every policy requires its
energy cost and any negative resource deltas in full before execution. Insufficient
inputs block all policy effects. Routine consumption and shock losses retain zero floors.
Routine power adds up to 2 energy per inhabited cycle, capped at 50; see
[physical accounting](physical_accounting.md).
Security is a readiness counter, not a count of armed residents.

## `farming`: Hydroponic Production and Water Recovery

**Briefing:** Prioritize the systems that keep the colony supplied. Recover
water and increase food reserves before scarcity becomes a medical emergency.

The policy adds 14 food and 12 water and deducts 2 energy. Combining the two
gains is an explicit scenario abstraction of production and recovery, not a
simulation of crop growth, pipes, or water chemistry. It has no direct healing
effect or policy-specific injury risk in the baseline.

At a population of 40, routine use subsequently removes 8 food and 6 water.
Without a shock, the selected action therefore adds a net 6 food and 6 water
over that cycle. Medicine use and health pressure still occur.

**Choice it exposes:** Protecting reserves can postpone medical support or
security improvements. Selecting this action does not directly cure residents.
Farmers are the model's specialists for this policy.

## `medicine`: Infirmary Support and Medical Supply Preparation

**Briefing:** Give the infirmary priority. Improve medical reserves and treat
residents whose health has fallen below the treatment threshold.

The policy adds 8 medicine and deducts 2 energy. Each living resident whose
health is strictly below 0.75 requests a sampled boost between 0.04 and 0.12,
with final health capped at 1. The baseline boost parameter is 0.08. Requests
are proportionally reduced if the post-production medical stock is insufficient;
one medicine unit pays for one summed health point in the baseline.
Treatment happens before the cycle's environmental damage; improved health
does not guarantee survival through that damage.

The supply increase represents an abstract medical-support allocation. It is
not recovery from an outside delivery or a modeled pharmaceutical factory.
Actual health recovery debits medical stock, including supply produced in this
cycle. Zero post-production stock means no healing. Routine per-resident
medicine use is accounted for separately after treatment.

**Choice it exposes:** Health support competes with food/water recovery.
Repeated treatment can keep residents alive while essential reserves decline.
Doctors and elders are the model's specialists for this policy; the elder
mapping is a declared model assumption, not a claim of clinical qualification.

## `defense`: Shelter Security and Access Readiness

**Briefing:** Prioritize shelter protection and access readiness before low
security becomes another source of harm.

The policy adds 9 security and deducts 4 energy. In the baseline, security below
30 adds 0.02 health damage to each living resident during environmental pressure.
Improving readiness can avoid that penalty when it raises security sufficiently.

This does not reduce shock probability or automatically prevent shock losses.
Combat, hostile factions, airlock repairs, and individual guard assignments are
not simulated. The physical affordability gate requires all 4 energy units
regardless of whether optional institutional checks are enabled.

**Choice it exposes:** Readiness uses the largest policy energy cost and adds
neither food/water nor treatment. Guards and engineers are the model's
specialists for this policy. Engineers do not receive a separate water-recovery
expertise domain in the current mapping.

## `exploration`: Surface Supply Expedition

**Briefing:** Seek supplies beyond the shelter. Returns are uncertain, and
exposure can injure the community.

The policy deducts 2 energy and samples the gains in the overview table. For
each living resident, it independently samples a 0.02 probability of injury;
an injury removes between 0.08 and 0.20 health. Scavengers are the specialists.

The engine currently applies potential injury to all living residents. It does
not select an expedition crew, route, travel duration, or loot inventory.
The expedition label interprets an aggregate policy risk; reports must not
invent a named injured explorer from these aggregate results.

With optional governance checks enabled, exploration may be disallowed when
security is below 15 or energy below 2. Those restrictions do not apply to
ordinary runs without the optional checks, except that the physical energy
cost must always be affordable. See [governance rules](rules.md).

**Choice it exposes:** Exploration can replenish several reserves at once,
but its water and food returns are less predictable than hydroponic production
and it introduces direct injury risk. It does not supply energy or healing.

## Resource Vocabulary

| Engine field | Vault meaning | Accounting boundary |
| --- | --- | --- |
| `food` | Shared edible reserve | Net consumption; no individual ration allocation. |
| `water` | Shared usable-water reserve | Recovery is bundled into farming; no purity or radiation variable. |
| `medicine` | Shared medical reserve | Routine consumption plus stock-budgeted treatment proportional to actual healing. |
| `energy` | Available operating reserve | Bounded routine generation and upfront policy expenditure; no fuel/maintenance model. |
| `security` | Aggregate protective readiness | Policy gains and shock losses; no routine per-resident consumption. |

## Reuse Contract

Keep the engine identifiers stable. A neutral report can display `farming` as
"food production and water recovery"; a lunar-colony profile can display
"greenhouse and water reclamation" with the same mechanical configuration.
Changing a label changes presentation. Changing production, costs, expertise,
or risk changes the experiment and belongs in a validated scenario/model change.

This document is the human-readable dictionary, not a runtime narrative-profile
loader. The [implemented renderer](event_reports.md) reads recorded effects
instead of copying these baseline numbers into output templates. The
[experiment protocol](vault_protocol.md) supplies the colony briefing.
