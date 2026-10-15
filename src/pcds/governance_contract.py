"""Versioned data boundary for the current, deterministic governance procedure.

This contract describes a decision after private rankings have been updated and
before physical effects occur. It contains no random generator or narrative text.
Certificates are inspectable witnesses; Lean verification is separate future work.
"""

from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
import math
from typing import Annotated, Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator

from pcds.models import Agent, CommunityState, Policy, Role

CONTRACT_VERSION = "pcds-governance-v1"
POLICY_ORDER = tuple(Policy)
Name = Annotated[str, Field(strict=True, min_length=1)]
Count = Annotated[int, Field(strict=True, ge=0)]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Rule = Literal["majority", "approval", "expert_delegation", "liquid_democracy"]
ErrorCode = Literal[
    "unsupported_version", "invalid_request", "backend_unavailable",
    "backend_version_mismatch", "rule_loading_failed", "backend_query_failed", "invalid_response",
    "request_mismatch", "invalid_certificate",
]

# Freeze the simulation's current expertise map as part of this version's meaning.
# Prolog's illustrative expert_for/2 is not authoritative for current delegation.
ROLE_EXPERTISE = {
    Role.DOCTOR: Policy.MEDICINE, Role.FARMER: Policy.FARMING,
    Role.ENGINEER: Policy.DEFENSE, Role.GUARD: Policy.DEFENSE,
    Role.SCAVENGER: Policy.EXPLORATION, Role.ELDER: Policy.MEDICINE,
}


class ContractRecord(BaseModel):
    """Reject unknown fields so misspelled mechanical inputs cannot be ignored."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class ExactValue(ContractRecord):
    """Nonnegative reduced fraction; transport never rounds binary64 boundaries."""

    numerator: Count
    denominator: Annotated[int, Field(strict=True, gt=0)]

    @model_validator(mode="after")
    def require_reduced_fraction(self) -> ExactValue:
        if math.gcd(self.numerator, self.denominator) != 1:
            raise ValueError("fractions must be reduced; zero is represented as 0/1")
        return self

    @classmethod
    def from_number(cls, value: int | float) -> ExactValue:
        """Retain the exact value of a finite source number, rather than its display rounding."""
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError("resource and trust values must be finite numbers")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("resource and trust values must be finite numbers")
        fraction = Fraction(value)
        return cls(numerator=fraction.numerator, denominator=fraction.denominator)

    def fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


class ResidentSnapshot(ContractRecord):
    """Only decision-relevant member fields; health and private scores stay upstream."""

    name: Name
    role: Role
    alive: Annotated[bool, Field(strict=True)]
    sanctioned: Annotated[bool, Field(strict=True)]
    ranking: Annotated[tuple[Policy, ...], Field(min_length=4, max_length=4)]

    @model_validator(mode="after")
    def require_complete_ranking(self) -> ResidentSnapshot:
        if set(self.ranking) != set(POLICY_ORDER):
            raise ValueError("ranking must contain each of the four policies exactly once")
        return self


class TrustLink(ContractRecord):
    """Directed edge; list position preserves the legacy equal-trust tie-breaker."""

    source: Name
    target: Name
    weight: ExactValue

    @model_validator(mode="after")
    def require_unit_weight(self) -> TrustLink:
        if self.weight.numerator > self.weight.denominator:
            raise ValueError("trust weight must be between zero and one")
        return self


class ResourceSnapshot(ContractRecord):
    """Bind shared stocks without introducing policy costs or physical transitions."""

    food: ExactValue
    water: ExactValue
    medicine: ExactValue
    energy: ExactValue
    security: ExactValue


class GovernanceRequest(ContractRecord):
    """Complete inputs for the built-in governance semantics, including meaningful order."""

    schema_version: Literal["pcds-governance-v1"]
    decision_id: Name
    rule: Rule
    institutional_checks: Annotated[bool, Field(strict=True)] = False
    # Version 1 matches the simulator, not the custom-k/depth helper APIs.
    approval_k: Annotated[int, Field(strict=True, ge=2, le=2)] = 2
    delegation_max_depth: Annotated[int, Field(strict=True, ge=3, le=3)] = 3
    policy_order: tuple[Policy, ...] = POLICY_ORDER
    residents: tuple[ResidentSnapshot, ...]
    trust_links: tuple[TrustLink, ...] = ()
    resources: ResourceSnapshot

    @model_validator(mode="after")
    def require_unambiguous_state(self) -> GovernanceRequest:
        names = [resident.name for resident in self.residents]
        edges = [(edge.source, edge.target) for edge in self.trust_links]
        if len(set(names)) != len(names):
            raise ValueError("resident names must be unique")
        if len(set(edges)) != len(edges):
            raise ValueError("directed trust edges must be unique")
        if self.policy_order != POLICY_ORDER:
            raise ValueError("policy order is fixed by contract version 1")
        return self


class BallotWitness(ContractRecord):
    """One original ballot, its greedy delegation path, and its actual contributions."""

    voter: Name
    topic: Policy
    path: Annotated[tuple[Name, ...], Field(min_length=1, max_length=4)]
    stop_reason: Literal["direct_rule", "no_eligible_expert", "single_hop", "cycle", "depth_limit"]
    representative: Name
    votes_for: Annotated[tuple[Policy, ...], Field(min_length=1, max_length=2)]


class PolicyPermission(ContractRecord):
    policy: Policy
    allowed: Annotated[bool, Field(strict=True)]
    reason: Literal["checks_disabled", "unconditional", "requirements_met",
                    "security_below_15", "energy_below_2"]


class GovernanceDecision(ContractRecord):
    """Election result and post-election permission override, before affordability."""

    mandate: Literal["vote", "recording_default"]
    eligible_voters: tuple[Name, ...]
    representatives: dict[Name, Name]
    scores: dict[Policy, Count]
    voted_policy: Policy
    selected_policy: Policy
    permission_override: Annotated[bool, Field(strict=True)]


class GovernanceCertificate(ContractRecord):
    """A request-bound witness, not an attestation of backend identity or a Lean proof."""

    schema_version: Literal["governance-witness-v1"] = "governance-witness-v1"
    request_sha256: Digest
    ballots: tuple[BallotWitness, ...]
    permissions: tuple[PolicyPermission, ...]


class GovernanceSuccess(ContractRecord):
    schema_version: Literal["pcds-governance-v1"] = CONTRACT_VERSION
    status: Literal["ok"] = "ok"
    decision: GovernanceDecision
    certificate: GovernanceCertificate


class ContractProblem(ContractRecord):
    code: ErrorCode
    message: Name


class GovernanceFailure(ContractRecord):
    """An error never carries a successful policy or a substitute certificate."""

    schema_version: Literal["pcds-governance-v1"] = CONTRACT_VERSION
    status: Literal["error"] = "error"
    request_sha256: Digest | None = None
    error: ContractProblem


GovernanceResponse = Annotated[GovernanceSuccess | GovernanceFailure, Field(discriminator="status")]
RESPONSE_ADAPTER = TypeAdapter(GovernanceResponse)


class GovernanceContractError(ValueError):
    """Structured contract failures can be serialized without interpreting error prose."""

    def __init__(self, code: ErrorCode, message: str):
        super().__init__(message)
        self.problem = ContractProblem(code=code, message=message)


def parse_request(payload: str | dict) -> GovernanceRequest:
    """Separate an unsupported protocol from invalid data in a supported protocol."""
    try:
        data = read_contract_json(payload, "invalid_request") if isinstance(payload, str) else payload
        if isinstance(data, dict) and data.get("schema_version", CONTRACT_VERSION) != CONTRACT_VERSION:
            raise GovernanceContractError("unsupported_version", "Unsupported governance contract version")
        return GovernanceRequest.model_validate(data)
    except (ValidationError, TypeError) as error:
        raise GovernanceContractError("invalid_request", str(error)) from error


def read_contract_json(payload: str, error_code: ErrorCode) -> object:
    """Reject duplicate object members instead of letting parsers disagree on their values."""
    try:
        return json.loads(payload, object_pairs_hook=_unique_members)
    except (ValueError, TypeError) as error:
        raise GovernanceContractError(error_code, str(error)) from error


def _unique_members(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON member: {key}")
        result[key] = value
    return result


def request_digest(request: GovernanceRequest) -> str:
    """Hash normalized defaults and ordered arrays using a domain-separated encoding."""
    normalized = json.dumps(request.model_dump(mode="json"), sort_keys=True,
                            separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return sha256((CONTRACT_VERSION + "\n" + normalized).encode("utf-8")).hexdigest()


def snapshot_governance_request(
    rule: str, agents: list[Agent], trust_graph: nx.DiGraph, state: CommunityState,
    *, decision_id: str, institutional_checks: bool = False,
) -> GovernanceRequest:
    """Copy the decision-time world without advancing RNGs or changing graph order.

    Unknown historical graph endpoints remain visible but cannot receive a ballot.
    Missing edge weights retain the resolver's existing default of zero.
    """
    if not trust_graph.is_directed() or trust_graph.is_multigraph():
        raise GovernanceContractError("invalid_request", "A simple directed trust graph is required")
    try:
        return GovernanceRequest(
            schema_version=CONTRACT_VERSION, decision_id=decision_id, rule=rule,
            institutional_checks=institutional_checks,
            residents=tuple(ResidentSnapshot(name=agent.name, role=agent.role,
                alive=agent.alive, sanctioned=agent.sanctioned, ranking=tuple(agent.preferences))
                for agent in agents),
            trust_links=tuple(TrustLink(source=source, target=target,
                weight=ExactValue.from_number(data.get("trust", 0.0)))
                for source, target, data in trust_graph.edges(data=True)),
            resources=ResourceSnapshot(**{key: ExactValue.from_number(value)
                                         for key, value in state.as_dict().items()}),
        )
    except (ValidationError, ValueError) as error:
        raise GovernanceContractError("invalid_request", str(error)) from error
