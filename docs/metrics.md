# Metrics and Their Interpretation

The research question involves survival, wellbeing, representation, and power.
These are distinct outcomes. No single indicator establishes that a mechanism
governs better, and the report does not designate an overall winner.

The [walkthrough](walkthrough.md) introduces the interpretation problem without
equations; the [glossary](glossary.md) explains conditional means, coverage, and
concentration. Dashboard values are rounded to three decimal places; use CSV
values when examining small differences quantitatively.

## Outcome Definitions

| Output | Definition and interpretation |
| --- | --- |
| `final_survival_rate` | Living members after the final round divided by the original population. Defined even after extinction. |
| `final_survivor_health` | Mean health among final survivors. Undefined when none survive; a higher conditional mean can result from the death of unhealthy members. |
| `final_population_health` | Sum of survivors' health divided by the original population, assigning zero to deaths. This remains comparable across all seed pairs and exposes the selection hidden by conditional survivor health. |
| `final_inequality` | Population standard deviation of health, with deaths assigned zero. Lower means less dispersion, not better wellbeing: shared deprivation and shared good health can both have zero dispersion. |
| `final_preference_satisfaction` | Mean normalized rank of the implemented policy in eligible voters' current rankings, measured before policy effects. |
| `final_prior_preference_satisfaction` | The same rank measure using those voters' original priorities, so adaptation cannot conceal disagreement with their initial preferences. |
| `final_delegation_concentration` | Normalized concentration of control over original ballots at their actual terminal representatives. Lower means more dispersed ballot control. |
| `final_max_vote_share` | Largest terminal representative's share of original ballots. Report electorate size alongside it: one remaining voter necessarily holds a share of one. |
| `final_delegated_vote_share` | Fraction of voters whose terminal representative differs from themselves. Descriptive: more delegation is not inherently better. |
| `final_resilience` | Mean of the five resource stocks divided by configurable reference stocks. Values above one indicate surpluses. This stock proxy does not measure recovery after shocks or guarantee that every essential resource is sufficient. |
| `final_welfare` | A bounded normative material-outcome index, decomposed and checked under alternative weights below. |

Survival and health are measured after policy effects and environmental pressure.
Satisfaction and ballot control describe the electorate at decision time, before
those effects. A voter who dies during the round still belongs to that round's
electorate. Sanctioned members remain in material outcomes but are excluded from
the electorate; satisfaction is not a measure of inclusion of the whole original
community. Raw results record `initial_population`, `final_survivors`, and
`final_eligible_voters` to make these denominators visible.

## Preference Satisfaction

For a ranking of K policies and a selected policy at zero-based position r:

```text
rank satisfaction = (K - 1 - r) / (K - 1)
```

With four policies the scores are 1, 2/3, 1/3, and 0. This explicitly assumes
equal reporting distances between ranks. It is an ordinal congruence indicator,
not a measurement of comparable psychological utilities or realized happiness.
Current rankings reflect private information; original rankings preserve stable
personal priorities. The implemented policy is evaluated, including any policy
replacement imposed by governance constraints. With no eligible voters both
satisfaction measures are undefined, not zero or perfect agreement.

## Delegation Power

The voting implementation produces one trace mapping each eligible original
voter to the representative whose ballot actually receives that voter's weight.
Choice and metrics use the same resolution, including cycle, depth-limit, and
missing-recipient fallbacks. Network centrality alone would not reveal this
actual control. Each original vote is counted once; approval voting grants
multiple approvals but keeps ownership of each original ballot with its voter.

Let N be eligible voters, w_j the original ballots controlled by representative
j, and s_j = w_j / N. For N greater than one:

```text
concentration = (sum(s_j ** 2) - 1/N) / (1 - 1/N)
```

The index is zero when every voter controls their own ballot and one when a
single representative controls all ballots. With a single voter it is defined
as zero excess concentration, while their maximum share is one. With no voters
all power metrics are undefined. Round snapshots retain the representative map
and ballot weights so conservation can be checked independently.

This measures current ballot control, not all political influence. It does not
capture informal coercion, agenda-setting, or lifetime dominance. Lower
concentration can conflict with effective coordination; read it alongside
survival, health, and preference congruence.

## Welfare as an Explicit Normative Choice

Let S be survival, P population health, and R reference-normalized reserves:

```text
W = survival_weight * S
  + health_weight * P
  + resources_weight * S * min(1, R)
```

P equals S times mean survivor health whenever survivors exist, and is zero
after extinction. This retains deaths in the health denominator. The reserve
component is capped so resource accumulation cannot dominate the index and is
gated by survival so extinction cannot receive a positive reserve reward.
With nonnegative weights summing to one, 0 <= W <= S <= 1, within floating-point
roundoff. The three weighted contributions are exported separately.

Default weights are 0.65 for survival, 0.25 for population health, and 0.10 for
reserves. Their rationale is a declared crisis-governance priority: preserving
members receives the largest weight, health distinguishes living conditions,
and reserves receive a smaller weight because they are only a proxy for future
capacity. These values are neither empirically estimated nor uniquely correct;
they do not enforce lexicographic priority for survival. They deliberately keep
political satisfaction and power outside the aggregate rather than hiding those
tradeoffs inside additional unsupported weights.

Weights and positive resource references are configurable under
`parameters.metrics` in scenario JSON. Defaults use Shelter Alpha's original
stock scales (100 food/water, 50 medicine/energy/security), not hidden constants
inside the metric functions. Other scenario budgets can choose other references.
The equal averaging of resource ratios is also a reporting convention; inspect
the separate resource stocks when bottlenecks matter.

## Weight Sensitivity

Every trajectory is scored under these prespecified profiles as well as its
configured weights, using identical physical outcomes and resource references:

| Profile | Survival | Population health | Reserves |
| --- | ---: | ---: | ---: |
| `survival_priority` | 0.80 | 0.15 | 0.05 |
| `health_priority` | 0.45 | 0.45 | 0.10 |
| `balanced` | 0.50 | 0.30 | 0.20 |

They produce `final_welfare_survival_priority`,
`final_welfare_health_priority`, and `final_welfare_balanced`, each with paired
differences and confidence intervals. They are not fitted to make a rule win,
and changing reporting weights does not change agents' decisions or random draws.

For example, with reference-level reserves, four survivors at health 0.1 score
0.865 under survival priority and 0.595 under health priority. Three healthy
survivors out of four score 0.75 under both. The preferred outcome reverses with
the priorities: this is an ethical tradeoff, not an implementation error. These
profiles illustrate sensitivity; they do not exhaust the possible weight space.

## Undefined Outcomes and Paired Coverage

Extinction leaves conditional survivor health undefined. An absent electorate
leaves satisfaction and power undefined. CSV files leave these cells blank;
they are never imputed as zero. Seed pairs still must be complete and unique:
an undefined outcome is different from a missing simulation row.

For conditional outcomes, a paired difference is defined only when both rules
have a defined value. Effects record `n_seed_pairs` (all matched seeds),
`n_pairs` (defined pairs), and `n_undefined_pairs`, with
`estimand = defined_pairs_only`. Means and bootstrap intervals use the same
defined pairs on both sides. With no such pairs there is no effect estimate;
with fewer than two there is no confidence interval. Rule summaries also show
the number of defined runs for every metric.

This conditional subset depends on the mechanisms themselves and can create
selection bias. It must not be presented as an all-seed causal benefit of a
rule. Survival and population health retain all seed pairs and must accompany
conditional health and political indicators. Low paired coverage also weakens
bootstrap interpretation even if the total run count is large.

The metric schema is `separate-outcomes-v1`. Welfare and health-dispersion
definitions changed; previous reported metric values must be regenerated rather
than pooled with these outputs. Physical dynamics and event-keyed external
conditions are unaffected by the reporting definitions.
