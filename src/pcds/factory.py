from __future__ import annotations

import random
from typing import Iterable

import networkx as nx
import numpy as np

from pcds.models import Agent, Policy, Role
from pcds.scenarios import AgentSpec, Scenario


ROLES: list[Role] = [
    Role.DOCTOR,
    Role.FARMER,
    Role.ENGINEER,
    Role.GUARD,
    Role.SCAVENGER,
    Role.ELDER,
]

POLICIES: list[Policy] = [
    Policy.FARMING,
    Policy.MEDICINE,
    Policy.DEFENSE,
    Policy.EXPLORATION,
]


def create_agents(
    n: int,
    seed: int | None = None,
    role_distribution: dict[Role, float] | None = None,
) -> list[Agent]:
    """Create a synthetic community with heterogeneous preferences."""
    rng = random.Random(seed)
    agents: list[Agent] = []

    for i in range(n):
        role = _sample_role(rng, role_distribution)
        prefs = POLICIES.copy()
        rng.shuffle(prefs)

        # Bias agents toward their own domain of expertise.
        expert_policy = {
            Role.FARMER: Policy.FARMING,
            Role.DOCTOR: Policy.MEDICINE,
            Role.GUARD: Policy.DEFENSE,
            Role.SCAVENGER: Policy.EXPLORATION,
            Role.ENGINEER: Policy.DEFENSE,
            Role.ELDER: Policy.MEDICINE,
        }[role]
        if rng.random() < 0.55:
            prefs.remove(expert_policy)
            prefs.insert(0, expert_policy)

        agents.append(
            Agent(
                name=f"agent_{i}",
                role=role,
                risk_aversion=rng.random(),
                cooperation=rng.random(),
                health=float(np.clip(rng.normalvariate(0.8, 0.15), 0.2, 1.0)),
                preferences=prefs,
            )
        )
    return agents


def create_agents_from_specs(specs: Iterable[AgentSpec]) -> list[Agent]:
    """Create agents from explicit scenario data instead of synthetic sampling."""
    agents: list[Agent] = []
    for spec in specs:
        prefs = spec.preferences or _default_preferences_for_role(spec.role)
        agents.append(
            Agent(
                name=spec.name,
                role=spec.role,
                health=spec.health,
                risk_aversion=spec.risk_aversion,
                cooperation=spec.cooperation,
                preferences=prefs,
            )
        )
    return agents


def create_agents_for_scenario(scenario: Scenario, seed: int | None = None) -> list[Agent]:
    """Dispatch between synthetic populations and fully specified populations."""
    if isinstance(scenario.agents, int):
        return create_agents(scenario.agents, seed=seed, role_distribution=scenario.role_distribution)
    return create_agents_from_specs(scenario.agents)


def create_trust_graph(
    agents: Iterable[Agent],
    seed: int | None = None,
    p: float = 0.18,
    topology: str = "expertise_clustered",
) -> nx.DiGraph:
    """Create a directed trust graph among agents.

    Edge A -> B means A trusts B enough to possibly delegate to B.
    """
    rng = random.Random(seed)
    graph = nx.DiGraph()
    agent_list = list(agents)

    for agent in agent_list:
        graph.add_node(agent.name, role=agent.role.value, expertise=agent.expertise.value)

    for a in agent_list:
        for b in agent_list:
            if a.name == b.name:
                continue
            # Expertise-clustered graphs favor agents who share expertise or
            # hold broadly useful coordination roles.
            same_or_relevant = a.expertise == b.expertise or b.role in {Role.DOCTOR, Role.ENGINEER, Role.ELDER}
            if topology == "sparse":
                probability = p * 0.45
            elif topology == "dense":
                probability = min(1.0, p * 2.2)
            elif topology == "fragile":
                probability = p if same_or_relevant else p * 0.25
            else:
                probability = p + (0.12 if same_or_relevant else 0.0)
            if rng.random() < probability:
                graph.add_edge(a.name, b.name, trust=round(rng.uniform(0.5, 1.0), 3))

    return graph


def create_trust_graph_for_scenario(
    scenario: Scenario,
    agents: Iterable[Agent],
    seed: int | None = None,
) -> nx.DiGraph:
    """Build a trust graph and then apply any hand-authored scenario edges."""
    graph = create_trust_graph(
        agents,
        seed=seed,
        p=scenario.trust_probability,
        topology=scenario.trust_topology,
    )
    if scenario.trust_edges is None:
        return graph
    for edge in scenario.trust_edges:
        graph.add_edge(edge.source, edge.target, trust=edge.trust)
    return graph


def _sample_role(rng: random.Random, role_distribution: dict[Role, float] | None) -> Role:
    if not role_distribution:
        return rng.choice(ROLES)
    roles = list(role_distribution)
    weights = [max(0.0, role_distribution[role]) for role in roles]
    if sum(weights) <= 0:
        return rng.choice(ROLES)
    return rng.choices(roles, weights=weights, k=1)[0]


def _default_preferences_for_role(role: Role) -> list[Policy]:
    expert_policy = {
        Role.FARMER: Policy.FARMING,
        Role.DOCTOR: Policy.MEDICINE,
        Role.GUARD: Policy.DEFENSE,
        Role.SCAVENGER: Policy.EXPLORATION,
        Role.ENGINEER: Policy.DEFENSE,
        Role.ELDER: Policy.MEDICINE,
    }[role]
    return [expert_policy, *[policy for policy in POLICIES if policy != expert_policy]]
