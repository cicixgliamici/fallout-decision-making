"""Choose a policy and record who controls each original ballot.

Selection and power measurement share one resolved trace so their counts agree.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import networkx as nx

from pcds.models import Agent, Policy

VotingRuleName = str
VOTING_RULES: tuple[VotingRuleName, ...] = (
    "majority",
    "approval",
    "expert_delegation",
    "liquid_democracy",
)


@dataclass(frozen=True)
class VotingOutcome:
    """The selected policy and the terminal holder of every eligible original ballot."""

    policy: Policy
    representatives: dict[str, str]


def majority_vote(agents: list[Agent]) -> Policy:
    """Select the largest first-choice total: this is plurality, despite the legacy name.

    A winner does not need more than half the eligible votes.
    """
    votes = Counter(a.top_choice() for a in agents if a.alive and not a.sanctioned)
    return _stable_argmax(votes)


def approval_vote(agents: list[Agent], k: int = 2) -> Policy:
    """Count one approval for each policy in a member's top-k set.

    Each member still owns one original ballot when measuring concentration.
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
    """Transfer a vote to the most trusted eligible topic specialist, or vote directly.

    The representative's current first choice receives the weight, not necessarily the topic.
    """
    return _delegation_outcome(agents, trust_graph, liquid=False).policy


def liquid_democracy_vote(
    agents: list[Agent], trust_graph: nx.DiGraph, max_depth: int = 3
) -> Policy:
    """Resolve topic-specific delegation chains up to a fixed depth.

    A selected cycle returns the original ballot; the depth limit uses the current holder.
    """
    return _delegation_outcome(agents, trust_graph, liquid=True, max_depth=max_depth).policy


def voting_outcome(rule: str, agents: list[Agent], trust_graph: nx.DiGraph) -> VotingOutcome:
    """Choose a policy and retain the exact ballot-ownership trace used to choose it.

    Direct rules keep each ballot with its voter; delegated rules resolve it once.
    """
    if rule in {"majority", "approval"}:
        policy = majority_vote(agents) if rule == "majority" else approval_vote(agents)
        # Approval grants multiple approvals, but each voter still controls
        # one original ballot; ballot ownership is comparable across rules.
        representatives = {
            agent.name: agent.name for agent in agents if agent.alive and not agent.sanctioned
        }
        return VotingOutcome(policy, representatives)
    if rule in {"expert_delegation", "liquid_democracy"}:
        return _delegation_outcome(agents, trust_graph, liquid=rule == "liquid_democracy")
    raise ValueError(f"Unknown voting rule: {rule}")


def _delegation_outcome(
    agents: list[Agent],
    trust_graph: nx.DiGraph,
    *,
    liquid: bool,
    max_depth: int = 3,
) -> VotingOutcome:
    """Count each eligible original voter once at their resolved representative.

    The resulting mapping also supplies the power metrics, avoiding a second interpretation.
    """
    agent_map = {agent.name: agent for agent in agents if agent.alive and not agent.sanctioned}
    representatives: dict[str, str] = {}
    scores: Counter[Policy] = Counter()
    for agent in agent_map.values():
        if liquid:
            representative = _resolve_delegate(
                agent, agent.top_choice(), agent_map, trust_graph, max_depth
            )
        else:
            candidates = _trusted_experts(agent, agent.top_choice(), agent_map, trust_graph)
            representative = candidates[0] if candidates else agent
        # Each original voter contributes exactly once at their terminal
        # representative, including direct/cycle/depth-limit fallbacks.
        representatives[agent.name] = representative.name
        scores[representative.top_choice()] += 1
    return VotingOutcome(_stable_argmax(scores), representatives)


def _trusted_experts(
    agent: Agent,
    topic: Policy,
    agent_map: dict[str, Agent],
    trust_graph: nx.DiGraph,
) -> list[Agent]:
    # The graph retains historical links after deaths or exclusions. Only
    # currently eligible agents may receive a delegated vote.
    """Find current eligible specialists among historical outgoing trust links.

    Dead, excluded, or unknown recipients cannot acquire a delegated vote.
    """
    if agent.name not in trust_graph:
        return []
    candidates: list[Agent] = []

    for _, target in trust_graph.out_edges(agent.name):
        candidate = agent_map.get(target)
        if (
            candidate is not None
            and candidate.alive
            and not candidate.sanctioned
            and candidate.expertise == topic
        ):
            candidates.append(candidate)

    if not candidates:
        return []

    candidates.sort(key=lambda c: trust_graph[agent.name][c.name].get("trust", 0.0), reverse=True)
    return candidates


def _resolve_delegate(
    agent: Agent,
    topic: Policy,
    agent_map: dict[str, Agent],
    trust_graph: nx.DiGraph,
    max_depth: int,
) -> Agent:
    """Follow the most trusted eligible choice without repeatedly visiting a member.

    The original voter is restored on a cycle; no alternative lower-trust exit is invented.
    """
    current = agent
    seen = {agent.name}

    for _ in range(max_depth):
        candidates = _trusted_experts(current, topic, agent_map, trust_graph)
        if not candidates:
            return current
        representative = candidates[0]
        # Follow the most trusted eligible choice consistently. A cycle on
        # that path restores the original ballot rather than rerouting it.
        if representative.name in seen:
            return agent
        current = representative
        seen.add(current.name)

    return current


def _stable_argmax(scores: Counter[Policy]) -> Policy:
    """Choose the highest policy score, breaking ties by policy declaration order.

    Empty electorates use farming as a recording default, not an elected mandate.
    """
    if not scores:
        return Policy.FARMING
    return max(Policy, key=lambda p: (scores.get(p, 0), -list(Policy).index(p)))
