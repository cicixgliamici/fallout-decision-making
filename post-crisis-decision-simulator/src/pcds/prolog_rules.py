from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pcds.models import Agent, Policy


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

    def eligible_to_vote(self, agent: Agent) -> bool:
        if self.available and self._prolog is not None:
            self._sync_agent(agent)
            query = f"eligible_to_vote({agent.name})"
            return bool(list(self._prolog.query(query)))
        return agent.alive and not agent.sanctioned

    def allocation_allowed(self, policy: Policy) -> bool:
        if self.available and self._prolog is not None:
            query = f"allowed_policy({policy.value})"
            return bool(list(self._prolog.query(query)))
        return policy in set(Policy)

    def filter_eligible(self, agents: Iterable[Agent]) -> list[Agent]:
        return [a for a in agents if self.eligible_to_vote(a)]

    def _sync_agent(self, agent: Agent) -> None:
        assert self._prolog is not None
        self._prolog.assertz(f"role({agent.name}, {agent.role.value})")
        if agent.alive:
            self._prolog.assertz(f"alive({agent.name})")
        if agent.sanctioned:
            self._prolog.assertz(f"sanctioned({agent.name})")
