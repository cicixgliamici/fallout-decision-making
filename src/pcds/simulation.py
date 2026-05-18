from __future__ import annotations

import random
from pathlib import Path
from typing import Callable

import networkx as nx
import polars as pl

from pcds.factory import create_agents_for_scenario, create_trust_graph_for_scenario
from pcds.metrics import health_inequality, resource_resilience, social_welfare, survival_rate
from pcds.models import Agent, CommunityState, Policy, RoundResult, SimulationParameters
from pcds.prolog_rules import PrologRuleEngine
from pcds.scenarios import Scenario, default_scenario_path, load_scenario
from pcds.voting import (
    VOTING_RULES,
    approval_vote,
    expert_delegation_vote,
    liquid_democracy_vote,
    majority_vote,
)

VotingFn = Callable[[list[Agent], nx.DiGraph], Policy]


def run_simulation(
    rule: str,
    steps: int = 25,
    n_agents: int = 40,
    seed: int | None = None,
    use_prolog: bool = False,
    scenario: Scenario | str | Path | None = None,
) -> list[RoundResult]:
    """Run one seeded trajectory for a single voting rule."""
    if steps <= 0:
        raise ValueError("steps must be greater than zero")
    if n_agents <= 0:
        raise ValueError("n_agents must be greater than zero")

    rng = random.Random(seed)
    scenario_obj = _resolve_scenario(scenario, n_agents=n_agents)
    agents = create_agents_for_scenario(scenario_obj, seed=seed)
    trust_graph = create_trust_graph_for_scenario(scenario_obj, agents, seed=seed)
    state = scenario_obj.resources.model_copy(deep=True)
    parameters = scenario_obj.parameters
    prolog = PrologRuleEngine() if use_prolog else None

    results: list[RoundResult] = []

    for step in range(steps):
        # Prolog is optional: when enabled, it receives the current Python world
        # before eligibility and policy-admissibility checks are evaluated.
        if prolog:
            prolog.sync_world(agents, trust_graph, state)
        eligible_agents = prolog.filter_eligible(agents) if prolog else _eligible_agents(agents)
        selected = _select_policy(rule, eligible_agents, trust_graph)
        if prolog and not prolog.allocation_allowed(selected, state):
            selected = _first_allowed_policy(prolog, state)
        _apply_policy(selected, agents, state, rng, parameters)
        shock_occurred = _apply_environmental_pressure(agents, state, rng, parameters)

        results.append(
            RoundResult(
                step=step,
                rule=rule,
                selected_policy=selected,
                survival_rate=survival_rate(agents),
                welfare=social_welfare(agents, state),
                inequality=health_inequality(agents),
                resources=state.as_dict(),
                shock_occurred=shock_occurred,
            )
        )

    return results


def compare_rules(
    rules: list[str] | None = None,
    runs: int = 20,
    steps: int = 30,
    n_agents: int = 40,
    seed: int = 42,
    scenario: Scenario | str | Path | None = None,
) -> pl.DataFrame:
    """Run every requested rule over comparable seeds and return final metrics."""
    if runs <= 0:
        raise ValueError("runs must be greater than zero")

    rules = rules or list(VOTING_RULES)
    rows: list[dict] = []

    for rule in rules:
        for run_id in range(runs):
            run_seed = seed + run_id
            results = run_simulation(
                rule=rule,
                steps=steps,
                n_agents=n_agents,
                seed=run_seed,
                scenario=scenario,
            )
            last = results[-1]
            rows.append(
                {
                    "rule": rule,
                    "run_id": run_id,
                    "seed": run_seed,
                    "final_survival_rate": last.survival_rate,
                    "final_welfare": last.welfare,
                    "final_inequality": last.inequality,
                    "final_resilience": resource_resilience(CommunityState(**last.resources)),
                    "final_food": last.resources["food"],
                    "final_water": last.resources["water"],
                    "final_medicine": last.resources["medicine"],
                    "final_energy": last.resources["energy"],
                    "final_security": last.resources["security"],
                }
            )

    return pl.DataFrame(rows)


def _select_policy(rule: str, agents: list[Agent], trust_graph: nx.DiGraph) -> Policy:
    if rule == "majority":
        return majority_vote(agents)
    if rule == "approval":
        return approval_vote(agents)
    if rule == "expert_delegation":
        return expert_delegation_vote(agents, trust_graph)
    if rule == "liquid_democracy":
        return liquid_democracy_vote(agents, trust_graph)
    raise ValueError(f"Unknown voting rule: {rule}")


def _apply_policy(
    policy: Policy,
    agents: list[Agent],
    state: CommunityState,
    rng: random.Random,
    parameters: SimulationParameters,
) -> None:
    impact = parameters.policy_impacts[policy]

    # Policy impacts update shared resources first; individual health effects
    # are applied afterward so the same decision can affect both the shelter and
    # its members.
    state.energy = max(0.0, state.energy - impact.energy_cost)
    state.food = max(0.0, state.food + _stochastic_gain(impact.food_delta, rng, policy))
    state.water = max(0.0, state.water + _stochastic_gain(impact.water_delta, rng, policy))
    state.medicine = max(0.0, state.medicine + _stochastic_gain(impact.medicine_delta, rng, policy))
    state.security = max(0.0, state.security + impact.security_delta)

    if impact.health_boost > 0:
        for agent in agents:
            if agent.alive and agent.health < 0.75:
                boost = rng.uniform(impact.health_boost * 0.5, impact.health_boost * 1.5)
                agent.health = min(1.0, agent.health + boost)

    for agent in agents:
        if agent.alive and rng.random() < impact.injury_probability:
            agent.health = max(0.0, agent.health - rng.uniform(impact.injury_min, impact.injury_max))


def _apply_environmental_pressure(
    agents: list[Agent],
    state: CommunityState,
    rng: random.Random,
    parameters: SimulationParameters,
) -> bool:
    alive_agents = [a for a in agents if a.alive]
    population = len(alive_agents)

    # Scarcity pressure is intentionally simple: resources are consumed by the
    # surviving population, then shortages translate into health damage.
    state.food = max(0.0, state.food - parameters.food_consumption * population)
    state.water = max(0.0, state.water - parameters.water_consumption * population)
    state.medicine = max(0.0, state.medicine - parameters.medicine_consumption * population)

    scarcity = 0.0
    if state.food <= population * parameters.scarcity_food_threshold:
        scarcity += parameters.scarcity_food_damage
    if state.water <= population * parameters.scarcity_water_threshold:
        scarcity += parameters.scarcity_water_damage
    if state.medicine <= population * parameters.scarcity_medicine_threshold:
        scarcity += parameters.scarcity_medicine_damage
    if state.security < parameters.low_security_threshold:
        scarcity += parameters.low_security_damage

    shock_occurred = rng.random() < parameters.shock.probability
    if shock_occurred:
        state.food = max(0.0, state.food - parameters.shock.food_loss)
        state.water = max(0.0, state.water - parameters.shock.water_loss)
        state.medicine = max(0.0, state.medicine - parameters.shock.medicine_loss)
        state.security = max(0.0, state.security - parameters.shock.security_loss)
        scarcity += parameters.shock.health_damage

    for agent in alive_agents:
        damage = scarcity + rng.uniform(0.0, parameters.random_health_damage_max)
        agent.health = max(0.0, agent.health - damage)
        if agent.health <= parameters.death_threshold:
            agent.alive = False
    return shock_occurred


def _eligible_agents(agents: list[Agent]) -> list[Agent]:
    return [a for a in agents if a.alive and not a.sanctioned]


def _first_allowed_policy(prolog: PrologRuleEngine, state: CommunityState) -> Policy:
    for policy in Policy:
        if prolog.allocation_allowed(policy, state):
            return policy
    return Policy.FARMING


def _resolve_scenario(scenario: Scenario | str | Path | None, n_agents: int) -> Scenario:
    if scenario is None:
        scenario_obj = load_scenario(default_scenario_path())
        if isinstance(scenario_obj.agents, int):
            # CLI callers can override the default population size without
            # mutating the JSON scenario file.
            scenario_obj.agents = n_agents
        return scenario_obj
    if isinstance(scenario, Scenario):
        return scenario.model_copy(deep=True)
    return load_scenario(scenario)


def _stochastic_gain(delta: float, rng: random.Random, policy: Policy) -> float:
    if policy == Policy.EXPLORATION and delta > 0:
        return rng.uniform(0.0, delta * 2.0)
    return delta
