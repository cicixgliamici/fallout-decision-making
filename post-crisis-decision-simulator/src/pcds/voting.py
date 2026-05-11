from __future__ import annotations

from collections import Counter, defaultdict

import networkx as nx

from pcds.models import Agent, Policy


def majority_vote(agents: list[Agent]) -> Policy:
    """Select the policy with the highest number of first-place votes."""
    votes = Counter(a.top_choice() for a in agents if a.alive and not a.sanctioned)
    return _stable_argmax(votes)


def approval_vote(agents: list[Agent], k: int = 2) -> Policy:
    """Select the policy with the highest approval score.

    In MVP 0, each agent approves their top-k ranked options.
    """
    scores: Counter[Policy] = Counter()
    for agent in agents:
        if not agent.alive or agent.sanctioned:
            continue
        for policy in Policy:
            if agent.approves(policy, k=k):
                scores[policy] += 1
    return _stable_argmax(scores)


def expert_delegation_vote(agents: list[Agent], trust_graph: nx.DiGraph) -> Policy:
    """Delegate to trusted experts when possible, otherwise vote directly.

    This is intentionally simple: for an agent's top policy, the agent tries to delegate
    to a trusted living expert on that policy. The expert's top choice receives the vote.
    """
    by_name = {a.name: a for a in agents}
    scores: Counter[Policy] = Counter()

    for agent in agents:
        if not agent.alive or agent.sanctioned:
            continue
        topic = agent.top_choice()
        representative = _find_trusted_expert(agent, topic, agents, trust_graph)
        if representative is None:
            scores[agent.top_choice()] += 1
        else:
            scores[representative.top_choice()] += 1

    return _stable_argmax(scores)


def liquid_democracy_vote(agents: list[Agent], trust_graph: nx.DiGraph, max_depth: int = 3) -> Policy:
    """Simplified liquid democracy.

    Each agent can delegate along trust edges to an agent with relevant expertise. Delegation
    chains are resolved up to max_depth. Cycles fall back to direct voting.
    """
    agent_map = {a.name: a for a in agents}
    weighted_scores: defaultdict[Policy, float] = defaultdict(float)

    for agent in agents:
        if not agent.alive or agent.sanctioned:
            continue
        representative = _resolve_delegate(agent, agent.top_choice(), agent_map, trust_graph, max_depth)
        weighted_scores[representative.top_choice()] += 1.0

    return _stable_argmax(Counter(weighted_scores))


def _find_trusted_expert(
    agent: Agent,
    topic: Policy,
    agents: list[Agent],
    trust_graph: nx.DiGraph,
) -> Agent | None:
    by_name = {a.name: a for a in agents}
    candidates: list[Agent] = []

    for _, target in trust_graph.out_edges(agent.name):
        candidate = by_name[target]
        if candidate.alive and not candidate.sanctioned and candidate.expertise == topic:
            candidates.append(candidate)

    if not candidates:
        return None

    candidates.sort(key=lambda c: trust_graph[agent.name][c.name].get("trust", 0.0), reverse=True)
    return candidates[0]


def _resolve_delegate(
    agent: Agent,
    topic: Policy,
    agent_map: dict[str, Agent],
    trust_graph: nx.DiGraph,
    max_depth: int,
) -> Agent:
    current = agent
    seen = {agent.name}

    for _ in range(max_depth):
        candidates: list[Agent] = []
        for _, target_name in trust_graph.out_edges(current.name):
            if target_name in seen:
                continue
            candidate = agent_map[target_name]
            if candidate.alive and not candidate.sanctioned and candidate.expertise == topic:
                candidates.append(candidate)

        if not candidates:
            return current

        candidates.sort(key=lambda c: trust_graph[current.name][c.name].get("trust", 0.0), reverse=True)
        current = candidates[0]
        seen.add(current.name)

    return current


def _stable_argmax(scores: Counter[Policy]) -> Policy:
    """Deterministic argmax with enum order as tie-breaker."""
    if not scores:
        return Policy.FARMING
    return max(Policy, key=lambda p: (scores.get(p, 0), -list(Policy).index(p)))
