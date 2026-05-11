from __future__ import annotations

import random
from typing import Callable

import networkx as nx
import polars as pl

from pcds.factory import create_agents, create_trust_graph
from pcds.metrics import health_inequality, social_welfare, survival_rate
from pcds.models import Agent, CommunityState, Policy, RoundResult
from pcds.prolog_rules import PrologRuleEngine
from pcds.voting import approval_vote, expert_delegation_vote, liquid_democracy_vote, majority_vote

VotingFn = Callable[[list[Agent], nx.DiGraph], Policy]


def run_simulation(
    rule: str,
    steps: int = 25,
    n_agents: int = 40,
    seed: int | None = None,
    use_prolog: bool = False,
) -> list[RoundResult]:
    rng = random.Random(seed)
    agents = create_agents(n_agents, seed=seed)
    trust_graph = create_trust_graph(agents, seed=seed)
    state = CommunityState()
    prolog = PrologRuleEngine() if use_prolog else None

    results: list[RoundResult] = []

    for step in range(steps):
        eligible_agents = prolog.filter_eligible(agents) if prolog else [a for a in agents if a.alive and not a.sanctioned]
        selected = _select_policy(rule, eligible_agents, trust_graph)
        _apply_policy(selected, agents, state, rng)
        _apply_environmental_pressure(agents, state, rng)

        results.append(
            RoundResult(
                step=step,
                rule=rule,
                selected_policy=selected,
                survival_rate=survival_rate(agents),
                welfare=social_welfare(agents, state),
                inequality=health_inequality(agents),
                resources=state.as_dict(),
            )
        )

    return results


def compare_rules(
    rules: list[str] | None = None,
    runs: int = 20,
    steps: int = 30,
    n_agents: int = 40,
    seed: int = 42,
) -> pl.DataFrame:
    rules = rules or ["majority", "approval", "expert_delegation", "liquid_democracy"]
    rows: list[dict] = []

    for rule in rules:
        for run_id in range(runs):
            run_seed = seed + run_id
            results = run_simulation(rule=rule, steps=steps, n_agents=n_agents, seed=run_seed)
            last = results[-1]
            rows.append(
                {
                    "rule": rule,
                    "run_id": run_id,
                    "final_survival_rate": last.survival_rate,
                    "final_welfare": last.welfare,
                    "final_inequality": last.inequality,
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


def _apply_policy(policy: Policy, agents: list[Agent], state: CommunityState, rng: random.Random) -> None:
    # Every policy consumes energy, but reinforces a different survival dimension.
    state.energy = max(0.0, state.energy - 2.0)

    if policy == Policy.FARMING:
        state.food += 14.0
        state.water = max(0.0, state.water - 3.0)
    elif policy == Policy.MEDICINE:
        state.medicine += 8.0
        for agent in agents:
            if agent.alive and agent.health < 0.75:
                agent.health = min(1.0, agent.health + rng.uniform(0.04, 0.12))
    elif policy == Policy.DEFENSE:
        state.security += 9.0
        state.energy = max(0.0, state.energy - 2.0)
    elif policy == Policy.EXPLORATION:
        state.food += rng.uniform(0.0, 14.0)
        state.water += rng.uniform(0.0, 10.0)
        state.medicine += rng.uniform(0.0, 5.0)
        # Exploration is useful but risky.
        unlucky = [a for a in agents if a.alive and rng.random() < 0.02]
        for agent in unlucky:
            agent.health = max(0.0, agent.health - rng.uniform(0.08, 0.20))


def _apply_environmental_pressure(
    agents: list[Agent], state: CommunityState, rng: random.Random
) -> None:
    alive_agents = [a for a in agents if a.alive]
    population = len(alive_agents)

    state.food = max(0.0, state.food - 0.8 * population)
    state.water = max(0.0, state.water - 0.7 * population)
    state.medicine = max(0.0, state.medicine - 0.08 * population)

    scarcity = 0.0
    if state.food <= population * 0.5:
        scarcity += 0.05
    if state.water <= population * 0.5:
        scarcity += 0.06
    if state.medicine <= population * 0.05:
        scarcity += 0.02
    if state.security < 30:
        scarcity += 0.02

    for agent in alive_agents:
        damage = scarcity + rng.uniform(0.0, 0.015)
        agent.health = max(0.0, agent.health - damage)
        if agent.health <= 0.05:
            agent.alive = False
