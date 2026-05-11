from __future__ import annotations

import random
from typing import Iterable

import networkx as nx
import numpy as np

from pcds.models import Agent, Policy, Role


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


def create_agents(n: int, seed: int | None = None) -> list[Agent]:
    """Create a synthetic community with heterogeneous preferences."""
    rng = random.Random(seed)
    agents: list[Agent] = []

    for i in range(n):
        role = rng.choice(ROLES)
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


def create_trust_graph(agents: Iterable[Agent], seed: int | None = None, p: float = 0.18) -> nx.DiGraph:
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
            same_or_relevant = a.expertise == b.expertise or b.role in {Role.DOCTOR, Role.ENGINEER, Role.ELDER}
            probability = p + (0.12 if same_or_relevant else 0.0)
            if rng.random() < probability:
                graph.add_edge(a.name, b.name, trust=round(rng.uniform(0.5, 1.0), 3))

    return graph
