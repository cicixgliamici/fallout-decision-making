"""Apply institutional checks using a recorded backend with optional strict loading.

Python still resolves voting and delegation. Required mode rejects unavailable or
unpinned runtimes; optional mode records its fallback rather than disguising it
as real Prolog execution. Query failures never trigger a mid-run backend switch.
"""

from __future__ import annotations

from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
import tomllib
from typing import Iterable

import networkx as nx

from pcds.models import Agent, CommunityState, GovernanceBackend, Policy

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def governance_versions() -> dict[str, str]:
    """Read one version contract shared by runtime checks, tests, and documentation."""
    with (PROJECT_ROOT / "toolchains.toml").open("rb") as handle:
        return tomllib.load(handle)["governance"]


class PrologBackendError(RuntimeError):
    """The requested institutional backend could not be initialized or queried."""


class PrologRuleEngine:
    """Mirror one sequential simulation world into SWI-Prolog via PySwip.

    PySwip shares a process-wide interpreter. Each round replaces dynamic facts;
    concurrent worlds must use separate processes, as the experiment suite does.
    """

    def __init__(self, rules_file: str | Path | None = None, *, required: bool = False) -> None:
        self.available = False
        self._prolog = None
        mode = "required" if required else "optional"
        rules = Path(rules_file) if rules_file is not None else PROJECT_ROOT / "rules/governance.pl"
        self.info = GovernanceBackend(mode=mode, backend="python_fallback")
        try:
            self._load(rules.resolve(), required)
        except Exception as error:
            reason = f"{type(error).__name__}: {error}"
            self._prolog = None
            self.info = self.info.model_copy(update={"fallback_reason": reason})
            if required:
                raise PrologBackendError(f"Required SWI-Prolog backend unavailable: {reason}") from error

    def _load(self, rules: Path, required: bool) -> None:
        """Validate the rule file and runtime before enabling institutional checks."""
        contents = rules.read_bytes()
        self.info = self.info.model_copy(update={
            "rules_sha256": sha256(contents.replace(b"\r\n", b"\n")).hexdigest(),
            "pyswip_version": version("pyswip"),
        })
        from pyswip import Prolog

        self._prolog = Prolog()
        rows = self._query("current_prolog_flag(version_data, swi(Major, Minor, Patch, _))")
        runtime = ".".join(str(rows[0][part]) for part in ("Major", "Minor", "Patch"))
        self.info = self.info.model_copy(update={"swipl_version": runtime})
        if required:
            self._require_versions()
        # consult/1 can report syntax errors yet succeed. Parse all terms first
        # with exceptions enabled so a partially loaded file cannot pass startup.
        self._query("use_module(library(readutil))")
        self._query(f"read_file_to_terms({_atom(rules.as_posix())}, _, [syntax_errors(error)])")
        self._query(f"consult({_atom(rules.as_posix())})")
        for predicate in ("eligible_to_vote/1", "allowed_policy/1"):
            if not self._query(f"current_predicate({predicate})"):
                raise PrologBackendError(f"Missing governance predicate: {predicate}")
            head = predicate.replace("/1", "(_)")
            if not self._query(f"source_file({head}, {_atom(rules.as_posix())})"):
                # PySwip shares an interpreter: a predicate left by an earlier
                # engine must not make a different, incomplete file look valid.
                raise PrologBackendError(f"Governance predicate not defined by rule file: {predicate}")
        self.available = True
        self.info = self.info.model_copy(update={"backend": "swipl"})

    def _require_versions(self) -> None:
        expected = governance_versions()
        for name, actual in (("swipl", self.info.swipl_version),
                             ("pyswip", self.info.pyswip_version)):
            if actual != expected[name]:
                raise PrologBackendError(f"{name} version {actual}; required {expected[name]}")

    def _query(self, goal: str) -> list[dict]:
        """Exhaust generators before the next query; PySwip forbids nested queries."""
        assert self._prolog is not None
        try:
            return list(self._prolog.query(goal))
        except Exception as error:
            raise PrologBackendError(f"SWI-Prolog query failed: {error}") from error

    def sync_world(
        self, agents: Iterable[Agent], trust_graph: nx.DiGraph, state: CommunityState
    ) -> None:
        """Replace previous facts using declared arities, including empty worlds."""
        if not self.available:
            return
        for fact in ("alive(_)", "sanctioned(_)", "role(_, _)",
                     "trusts(_, _)", "resource(_, _)"):
            self._query(f"retractall({fact})")
        for agent in agents:
            self._sync_agent(agent)
        for source, target in trust_graph.edges:
            self._query(f"assertz(trusts({_atom(source)}, {_atom(target)}))")
        self._sync_resources(state)

    def _sync_resources(self, state: CommunityState) -> None:
        # repr preserves boundary values; eight-decimal rounding could change
        # whether a stock immediately below an institutional threshold is allowed.
        for resource, value in state.as_dict().items():
            self._query(f"retractall(resource({_atom(resource)}, _))")
            self._query(f"assertz(resource({_atom(resource)}, {value!r}))")

    def eligible_to_vote(self, agent: Agent) -> bool:
        """Query the loaded backend, or apply the recorded Python fallback."""
        if self.available:
            self._sync_agent(agent)
            return bool(self._query(f"eligible_to_vote({_atom(agent.name)})"))
        return agent.alive and not agent.sanctioned

    def allocation_allowed(self, policy: Policy, state: CommunityState | None = None) -> bool:
        """Check institutional permission; physical affordability is a separate gate."""
        if self.available:
            if state is not None:
                self._sync_resources(state)
            return bool(self._query(f"allowed_policy({_atom(policy.value)})"))
        return _fallback_policy_allowed(policy, state)

    def filter_eligible(self, agents: Iterable[Agent]) -> list[Agent]:
        """Retain supplied order while applying participation checks."""
        return [agent for agent in agents if self.eligible_to_vote(agent)]

    def _sync_agent(self, agent: Agent) -> None:
        """Refresh one identity without merging names or retaining obsolete status."""
        name = _atom(agent.name)
        for fact in (f"role({name}, _)", f"alive({name})", f"sanctioned({name})"):
            self._query(f"retractall({fact})")
        self._query(f"assertz(role({name}, {_atom(agent.role.value)}))")
        if agent.alive:
            self._query(f"assertz(alive({name}))")
        if agent.sanctioned:
            self._query(f"assertz(sanctioned({name}))")


def _fallback_policy_allowed(policy: Policy, state: CommunityState | None) -> bool:
    """Mirror only declared institutional thresholds, not delegation or physics."""
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
    """Quote data as atoms, preserving distinct names and preventing goal injection."""
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"
