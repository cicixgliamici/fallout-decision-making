from __future__ import annotations

from pathlib import Path
from typing import Iterable

import networkx as nx

from pcds.models import Agent, CommunityState, Policy


class PrologRuleEngine:
    """Thin optional bridge to SWI-Prolog through PySwip.

    If SWI-Prolog or PySwip is not available, the engine falls back to a conservative
    Python implementation. This keeps the MVP executable on ordinary machines while
    preserving a real Prolog layer for users who install SWI-Prolog.
    """

    def __init__(self, rules_file: str | Path = "rules/governance.pl") -> None:
        self.available = False
        self._prolog = None
        try:
            from pyswip import Prolog  # type: ignore

            self._prolog = Prolog()
            self._prolog.consult(str(rules_file))
            self.available = True
        except Exception:
            self.available = False

    def sync_world(
        self,
        agents: Iterable[Agent],
        trust_graph: nx.DiGraph,
        state: CommunityState,
    ) -> None:
        """Mirror the current Python simulation state into Prolog facts."""
        if not self.available or self._prolog is None:
            return
        for predicate in ("alive", "sanctioned", "role", "trusts", "resource"):
            list(self._prolog.query(f"retractall({predicate}(_, _))"))
            list(self._prolog.query(f"retractall({predicate}(_))"))
        for agent in agents:
            self._sync_agent(agent)
        for source, target in trust_graph.edges:
            self._prolog.assertz(f"trusts({_atom(source)}, {_atom(target)})")
        for resource, value in state.as_dict().items():
            self._prolog.assertz(f"resource({_atom(resource)}, {float(value):.8f})")

    def eligible_to_vote(self, agent: Agent) -> bool:
        if self.available and self._prolog is not None:
            self._sync_agent(agent)
            query = f"eligible_to_vote({_atom(agent.name)})"
            return bool(list(self._prolog.query(query)))
        return agent.alive and not agent.sanctioned

    def allocation_allowed(self, policy: Policy, state: CommunityState | None = None) -> bool:
        if self.available and self._prolog is not None:
            if state is not None:
                for resource, value in state.as_dict().items():
                    list(self._prolog.query(f"retractall(resource({_atom(resource)}, _))"))
                    self._prolog.assertz(f"resource({_atom(resource)}, {float(value):.8f})")
            query = f"allowed_policy({_atom(policy.value)})"
            return bool(list(self._prolog.query(query)))
        return _fallback_policy_allowed(policy, state)

    def filter_eligible(self, agents: Iterable[Agent]) -> list[Agent]:
        return [a for a in agents if self.eligible_to_vote(a)]

    def _sync_agent(self, agent: Agent) -> None:
        assert self._prolog is not None
        list(self._prolog.query(f"retractall(role({_atom(agent.name)}, _))"))
        list(self._prolog.query(f"retractall(alive({_atom(agent.name)}))"))
        list(self._prolog.query(f"retractall(sanctioned({_atom(agent.name)}))"))
        self._prolog.assertz(f"role({_atom(agent.name)}, {_atom(agent.role.value)})")
        if agent.alive:
            self._prolog.assertz(f"alive({_atom(agent.name)})")
        if agent.sanctioned:
            self._prolog.assertz(f"sanctioned({_atom(agent.name)})")


def _fallback_policy_allowed(policy: Policy, state: CommunityState | None) -> bool:
    """Conservative Python copy of the core Prolog governance constraints."""
    if policy not in set(Policy):
        return False
    if state is None:
        return True
    if policy == Policy.EXPLORATION and state.security < 15.0:
        return False
    if policy in {Policy.DEFENSE, Policy.EXPLORATION} and state.energy < 2.0:
        return False
    return True


def _atom(value: str) -> str:
    """Map simple scenario identifiers into Prolog-safe atom names."""
    return value.replace("-", "_")
