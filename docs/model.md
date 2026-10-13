# Model

The model is a repeated collective choice problem under scarcity.

For a first reading, use the [plain-language walkthrough](walkthrough.md).
This page gives the detailed assumptions behind it; unfamiliar terms are defined
in the [glossary](glossary.md). Parameters describe a hypothetical community,
not calibrated estimates of real behavior.

At each step, living and unsanctioned agents choose one policy through a voting
or delegation mechanism. The selected policy changes resources and health, then
environmental pressure consumes resources and may damage agents.

## Agents

Each agent has:

- role and associated expertise;
- ordinal preferences over policies;
- derived cardinal utility for policies;
- health and survival state;
- risk aversion and cooperation;
- sanction status.

In the default `adaptive` mode, agents reassess all four policies before each
ballot. Their original rankings remain stable personal priorities, while current
rankings and cardinal utility reflect their private estimates of current needs
and policy effects. In `fixed` mode, original rankings remain unchanged.

## Information and Expertise

An agent's role identifies one specialist policy domain. Default accuracy is
0.55 outside that domain and 0.90 within it. These are model parameters, not
empirical estimates or probabilities of choosing the best policy. Named agents
may override either accuracy in their JSON specification.

For each policy assessment, stock observations use Gaussian error with standard
deviation `observation_noise * (1 - accuracy) * max(stock, reserve_target)`.
Effect estimates use `effect_noise * (1 - accuracy) * abs(expected_effect)`.
Observed stocks are clipped at zero; estimated resource effects may have either
sign. Health signals and expected injury loss are clipped to [0, 1]. Health
observation error uses the same observation-noise coefficient on a unit scale.
Zero noise or accuracy 1 yields exact information. Policies with a known zero
effect retain a zero effect estimate. Errors are drawn independently for each
agent, policy, and round: this is a stylized private assessment, not a shared
public stock report or a Bayesian belief-update process.

Reserve targets for food, water, and medicine equal living population times
`planning_horizon * consumption + scarcity_threshold`. Security uses the
low-security threshold; energy uses the horizon times mean policy energy cost.
Each normalization target is floored at 1 to handle zero thresholds safely.
The horizon defines a desired buffer, not a multi-step rollout.

For each resource, the score uses the change in stock capped at its reserve
target, divided by that target, weighted by its scarcity-damage parameter plus
`reserve_weight` (energy has only the reserve weight). Expected healing is the
minimum of estimated mean health deficit and estimated health boost times the
estimated fraction of living agents below the treatment threshold of 0.75.
Expected injury is injury probability times midpoint injury severity.

The final score is:

```text
(0.5 + 0.5 * cooperation) * (reserve_gain + expected_healing)
- (1 + risk_aversion) * expected_injury
+ preference_weight * original_rank_score
```

The original rank score is 1 for the first choice and 0.25 for the fourth.
Policies are ranked by this score; equal scores use policy declaration order.
There is no direct expertise bonus in the adaptive score. A doctor can choose
farming when food is scarce. Synthetic populations retain the existing
role-correlated initial priorities, controlled identically in the equal-accuracy
comparison. Delegation still uses the voter's current first choice as its topic
and the trusted specialist's current ranking as the representative ballot.

Only information quality improves with expertise; actual policy impacts remain
unchanged. Experts can still misjudge policies, and neither delegation nor
greater accuracy is guaranteed to improve survival.

Round diagnostics record full-ranking changes and mean absolute score error
against the same agent's exact-information assessment. The reference is used
only for diagnostics, never to select a ballot. Error measures fidelity to this
heuristic score, not distance from a globally optimal governing strategy.

## Policies

The current policy set is finite:

- `farming`
- `medicine`
- `defense`
- `exploration`

Policy impacts are scenario parameters. Exploration has stochastic upside and
risk; defense and medicine reduce different failure modes. In the rebalanced
Shelter Alpha baseline, farming bundles hydroponic food production with water
recovery. The legacy scenario retains farming's original water cost.

Consumption is measured per living member, while policy stock changes are
community-wide amounts. These units matter: increasing population without
increasing policy production can make shortages unavoidable under a fixed
budget. Energy costs currently reduce a nonnegative stock counter without a
universal action-affordability gate. Medicine treatment is not stock-budgeted.
See [limitations](limitations.md) before treating these effects as realistic.

The baseline's consumption rates represent net reserve draw after routine
recovery. See [resource balance](resource_balance.md) for the declared budget,
a feasible finite-horizon schedule, and the archived original assumptions.

## Resources and Shocks

The community tracks food, water, medicine, energy, and security. Scenario files
define initial resources, consumption rates, scarcity thresholds, and optional
environmental shocks.

## Metrics

The report separates survival, mean survivor health, population health,
health dispersion, current/original preference satisfaction, actual delegated
ballot concentration, and resource reserves. Welfare is an explicitly weighted,
bounded material-outcome index with exported contributions and three weight
sensitivity profiles. It is not an overall political-quality score.

Definitions, denominators, undefined outcomes, normative weights, and examples
are developed in [Metrics and Their Interpretation](metrics.md). These measures
compare mechanisms inside the model, not real-world welfare.
