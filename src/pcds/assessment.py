"""Turn imperfect information about needs and policy effects into current rankings.

These scores guide ballots; they are separate from the welfare measured after outcomes.

The path is current world -> reserve targets -> private noisy policy scores ->
rankings. This is a one-step heuristic, with stable personal priorities; members
do not search future trajectories or learn a posterior belief across rounds.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from pcds.models import Agent, CommunityState, Policy, PolicyImpact, SimulationParameters


@dataclass(frozen=True)
class AssessmentContext:
    """True current stocks and needs used as the source of private noisy observations.

    Members score estimates of this context, not a perfect-information governing strategy.
    """

    resources: dict[str, float]
    targets: dict[str, float]
    weights: dict[str, float]
    treatable_fraction: float
    health_deficit: float
    population: int


def assessment_context(
    agents: list[Agent], state: CommunityState, parameters: SimulationParameters
) -> AssessmentContext:
    """Build desired stock buffers and health summaries for the current living population.

    The horizon sets reserve targets; it does not execute a multi-round forecast.
    """
    living = [agent for agent in agents if agent.alive]
    population = len(living)
    horizon = parameters.decision.planning_horizon
    targets = {
        "food": population
        * (horizon * parameters.food_consumption + parameters.scarcity_food_threshold),
        "water": population
        * (horizon * parameters.water_consumption + parameters.scarcity_water_threshold),
        "medicine": population
        * (horizon * parameters.medicine_consumption + parameters.scarcity_medicine_threshold),
        "security": parameters.low_security_threshold,
        "energy": horizon
        * sum(impact.energy_cost for impact in parameters.policy_impacts.values())
        / len(parameters.policy_impacts),
    }
    weights = {
        "food": parameters.scarcity_food_damage,
        "water": parameters.scarcity_water_damage,
        "medicine": parameters.scarcity_medicine_damage,
        "security": parameters.low_security_damage,
        "energy": 0.0,
    }
    return AssessmentContext(
        resources=state.as_dict(),
        targets=targets,
        weights=weights,
        treatable_fraction=sum(agent.health < 0.75 for agent in living) / max(1, population),
        health_deficit=sum(1.0 - agent.health for agent in living) / max(1, population),
        population=population,
    )


def policy_accuracy(agent: Agent, policy: Policy, parameters: SimulationParameters) -> float:
    """Choose specialist or general information quality, honoring individual overrides."""
    if agent.expertise == policy:
        return (
            agent.expert_accuracy
            if agent.expert_accuracy is not None
            else parameters.decision.expert_accuracy
        )
    return (
        agent.general_accuracy
        if agent.general_accuracy is not None
        else parameters.decision.general_accuracy
    )


def assess_policy(
    agent: Agent,
    policy: Policy,
    context: AssessmentContext,
    parameters: SimulationParameters,
    prior: tuple[Policy, ...],
    rng: random.Random,
    *,
    perfect_information: bool = False,
) -> float:
    """Score estimated stock gains, healing, risk, and the original personal ranking.

    Higher scores lead to higher current ranks. Exact information is an audit reference only.
    """
    # Expertise narrows estimation errors. It does not multiply production or
    # supply the winning policy directly to a specialist.
    accuracy = 1.0 if perfect_information else policy_accuracy(agent, policy, parameters)
    uncertainty = 1.0 - accuracy
    impact = parameters.policy_impacts[policy]
    prior_score = (len(prior) - prior.index(policy)) / len(prior)
    if not _perceived_affordable(policy, context, parameters, uncertainty, rng):
        # A failed action has no production or healing benefit. Keep stable
        # priorities as a tie-breaker when all options appear unavailable.
        return -1.0 + parameters.decision.preference_weight * prior_score
    effects = {
        "food": impact.food_delta,
        "water": impact.water_delta,
        "medicine": impact.medicine_delta,
        "security": impact.security_delta,
        "energy": -impact.energy_cost,
    }
    effect_noise = parameters.decision.effect_noise * uncertainty
    healing = _expected_healing(impact, context, parameters, uncertainty, rng)
    # Healing is a mean per living member; convert it to a community medicine
    # bill so the same benefit is not also counted as unspent reserve stock.
    effects["medicine"] -= healing * context.population * parameters.treatment_medicine_per_health
    reserve_gain = _reserve_gain(context, effects, parameters, uncertainty, rng)
    expected_injury = impact.injury_probability * (impact.injury_min + impact.injury_max) / 2.0
    injury = _bounded_signal(expected_injury, expected_injury * effect_noise, rng)
    # Preferences remain a stable prior: the previous round's noisy ranking
    # must not become a new prior and accumulate accidental path dependence.
    communal_weight = 0.5 + 0.5 * agent.cooperation
    # This is a member's perceived policy score, not the welfare reported after
    # consequences occur. The two calculations answer different questions.
    return (
        communal_weight * (reserve_gain + healing)
        - (1.0 + agent.risk_aversion) * injury
        + parameters.decision.preference_weight * prior_score
    )


def _perceived_affordable(
    policy: Policy,
    context: AssessmentContext,
    parameters: SimulationParameters,
    uncertainty: float,
    rng: random.Random,
) -> bool:
    """Use private stock estimates for planning; the physical gate uses real stocks."""
    impact = parameters.policy_impacts[policy]
    for resource, cost in impact.required_inputs().items():
        if cost <= 0:
            continue
        stock = context.resources[resource]
        scale = max(1.0, stock, context.targets[resource])
        observed = _signal(
            stock, scale * parameters.decision.observation_noise * uncertainty, rng
        )
        if max(0.0, observed) < cost:
            return False
    return True


def _expected_healing(
    impact: PolicyImpact,
    context: AssessmentContext,
    parameters: SimulationParameters,
    uncertainty: float,
    rng: random.Random,
) -> float:
    """Bound aggregate expected healing by estimated post-production medical supply."""
    observation_noise = parameters.decision.observation_noise * uncertainty
    effect_noise = parameters.decision.effect_noise * uncertainty
    treatable = _bounded_signal(context.treatable_fraction, observation_noise, rng)
    deficit = _bounded_signal(context.health_deficit, observation_noise, rng)
    boost = max(0.0, _signal(impact.health_boost, abs(impact.health_boost) * effect_noise, rng))
    scale = max(1.0, context.targets["medicine"], context.resources["medicine"])
    observed_stock = _signal(context.resources["medicine"], scale * observation_noise, rng)
    production = _signal(impact.medicine_delta, abs(impact.medicine_delta) * effect_noise, rng)
    available = max(0.0, observed_stock + production)
    capacity = available / parameters.treatment_medicine_per_health / max(1, context.population)
    # This heuristic does not reveal future patient-level draws to voters.
    return min(deficit, boost * treatable, capacity)


def _reserve_gain(
    context: AssessmentContext,
    effects: dict[str, float],
    parameters: SimulationParameters,
    uncertainty: float,
    rng: random.Random,
) -> float:
    """Estimate how an action changes stocks up to desired buffer levels.

    Capping stocks at each target stops large surpluses from continually dominating this score.
    """
    gain = 0.0
    # Helpers draw their own signals, even for a previously observed resource.
    # These are independent heuristic estimates, not one coherent stock belief.
    for resource, effect in effects.items():
        target = max(1.0, context.targets[resource])
        # Absolute observation error remains possible at zero stock; effect
        # error is relative to the known scale of the policy's resource change.
        scale = max(target, context.resources[resource])
        observed = max(
            0.0,
            _signal(
                context.resources[resource],
                scale * parameters.decision.observation_noise * uncertainty,
                rng,
            ),
        )
        estimated_effect = _signal(
            effect, abs(effect) * parameters.decision.effect_noise * uncertainty, rng
        )
        projected = max(0.0, observed + estimated_effect)
        reserve_change = (min(target, projected) - min(target, observed)) / target
        gain += reserve_change * (context.weights[resource] + parameters.decision.reserve_weight)
    return gain


def _signal(value: float, standard_deviation: float, rng: random.Random) -> float:
    # Exact information neither adds noise nor consumes the random stream.
    """Add a bell-shaped estimation error only when its configured spread is positive."""
    return rng.gauss(value, standard_deviation) if standard_deviation > 0.0 else value


def _bounded_signal(value: float, standard_deviation: float, rng: random.Random) -> float:
    """Keep estimated fractions or probabilities within their meaningful unit interval."""
    return min(1.0, max(0.0, _signal(value, standard_deviation, rng)))


def update_preferences(
    agents: list[Agent],
    state: CommunityState,
    parameters: SimulationParameters,
    priors: dict[str, tuple[Policy, ...]],
    seed: int,
    step: int,
) -> tuple[int, float]:
    """Reassess before a decision and return ranking changes plus average score error.

    Fixed mode preserves the supplied rankings. In adaptive mode, the original ranking
    remains the prior so past random errors do not silently become new personal priorities.
    """
    if parameters.decision.mode == "fixed":
        return 0, 0.0
    context = assessment_context(agents, state, parameters)
    changes = 0
    errors: list[float] = []
    for agent in agents:
        if not agent.alive or agent.sanctioned:
            continue
        scores: dict[Policy, float] = {}
        for policy in Policy:
            # Keyed streams keep private signals comparable across rules and
            # independent of policy effects, deaths, and other agents' draws.
            rng = random.Random(f"assessment:{seed}:{step}:{agent.name}:{policy.value}")
            scores[policy] = assess_policy(
                agent, policy, context, parameters, priors[agent.name], rng
            )
            # The exact-information reference is diagnostic only; ballots use
            # private estimates and never consult this reference score.
            reference = assess_policy(
                agent,
                policy,
                context,
                parameters,
                priors[agent.name],
                rng,
                perfect_information=True,
            )
            errors.append(abs(scores[policy] - reference))
        # Python's stable sort preserves Policy declaration order on equal scores.
        # Count a changed full ranking, not merely a change of first choice.
        ranking = sorted(Policy, key=lambda policy: scores[policy], reverse=True)
        changes += ranking != agent.preferences
        agent.preferences = ranking
        agent.utility_weights = scores
    return changes, sum(errors) / max(1, len(errors))
