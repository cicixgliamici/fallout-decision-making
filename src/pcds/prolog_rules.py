"""Connect optional institutional checks to Prolog or a Python fallback.

Voting eligibility and policy admissibility are distinct from physical feasibility.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import networkx as nx

from pcds.models import Agent, CommunityState, Policy


class PrologRuleEngine:
    """Apply optional institutional checks through Prolog or a Python fallback.

    Unavailable libraries or rule-loading failures set available to False. The bridge
    checks eligibility and policy permission; Python still resolves delegations.
    """

    def __init__(self, rules_file: str | Path = "rules/governance.pl") -> None:
        """Attempt to load the optional rule engine, falling back if it cannot be used."""
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
        """Replace the previous round's logical facts with the current Python world."""
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
        """Check current participation eligibility, using matching fallback conditions."""
        if self.available and self._prolog is not None:
            self._sync_agent(agent)
            query = f"eligible_to_vote({_atom(agent.name)})"
            return bool(list(self._prolog.query(query)))
        return agent.alive and not agent.sanctioned

    def allocation_allowed(self, policy: Policy, state: CommunityState | None = None) -> bool:
        """Check institutional policy permission, not complete resource affordability."""
        if self.available and self._prolog is not None:
            if state is not None:
                for resource, value in state.as_dict().items():
                    list(self._prolog.query(f"retractall(resource({_atom(resource)}, _))"))
                    self._prolog.assertz(f"resource({_atom(resource)}, {float(value):.8f})")
            query = f"allowed_policy({_atom(policy.value)})"
            return bool(list(self._prolog.query(query)))
        return _fallback_policy_allowed(policy, state)

    def filter_eligible(self, agents: Iterable[Agent]) -> list[Agent]:
        """Apply the configured eligibility check to all supplied community members."""
        return [a for a in agents if self.eligible_to_vote(a)]

    def _sync_agent(self, agent: Agent) -> None:
        """Refresh one member's role, survival, and sanction facts before a query."""
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
    """Mirror the core policy-permission thresholds when Prolog cannot be loaded."""
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
    """Replace dashes in simple identifiers used as unquoted Prolog atoms.

    This is not general quoting or sanitization; use simple lowercase identifiers.
    """
    return value.replace("-", "_")
