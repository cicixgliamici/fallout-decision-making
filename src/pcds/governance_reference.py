"""Produce current Python decisions and check their request-bound witnesses.

The producer uses the existing voting resolver. The checker independently checks
greedy path choices, stopping conditions, complete ballots, tally, and permission
override from contract data. This is executable conformance checking, not a Lean
proof or evidence that Prolog has taken over delegation.
"""

from __future__ import annotations

from collections import Counter

import networkx as nx
from pydantic import ValidationError

from pcds.governance_contract import (
    POLICY_ORDER, ROLE_EXPERTISE, RESPONSE_ADAPTER, BallotWitness,
    GovernanceCertificate, GovernanceContractError, GovernanceDecision,
    GovernanceFailure, GovernanceRequest, GovernanceSuccess, PolicyPermission,
    ResidentSnapshot, parse_request, read_contract_json, request_digest,
)
from pcds.models import Agent, Policy
from pcds.voting import _trusted_experts, voting_outcome


def _legacy_world(request: GovernanceRequest) -> tuple[list[Agent], nx.DiGraph]:
    """Reconstruct only voting inputs; exact fractions preserve all trust comparisons."""
    agents = [Agent(name=resident.name, role=resident.role, alive=resident.alive,
                    sanctioned=resident.sanctioned, preferences=list(resident.ranking))
              for resident in request.residents]
    graph = nx.DiGraph()
    for edge in request.trust_links:
        graph.add_edge(edge.source, edge.target, trust=edge.weight.fraction())
    return agents, graph


def _trace_ballot(
    request: GovernanceRequest, voter: Agent, eligible: dict[str, Agent], graph: nx.DiGraph,
) -> BallotWitness:
    """Explain the legacy candidate selection without altering its outcome or graph."""
    path, reason, holder = (voter.name,), "direct_rule", voter
    if request.rule in {"expert_delegation", "liquid_democracy"}:
        path, reason, holder = _trace_delegation(request, voter, eligible, graph)
    count = request.approval_k if request.rule == "approval" else 1
    return BallotWitness(voter=voter.name, topic=voter.top_choice(), path=path,
                         stop_reason=reason, representative=holder.name,
                         votes_for=tuple(holder.preferences[:count]))


def _trace_delegation(
    request: GovernanceRequest, voter: Agent, eligible: dict[str, Agent], graph: nx.DiGraph,
) -> tuple[tuple[str, ...], str, Agent]:
    current, path, seen = voter, [voter.name], {voter.name}
    liquid = request.rule == "liquid_democracy"
    budget = request.delegation_max_depth if liquid else 1
    for _ in range(budget):
        candidates = _trusted_experts(current, voter.top_choice(), eligible, graph)
        if not candidates:
            return tuple(path), "no_eligible_expert", current
        target = candidates[0]
        path.append(target.name)
        # Keep the closing edge in the witness even though a cycle's holder
        # is the origin, which need not be the repeated node at the end.
        if liquid and target.name in seen:
            return tuple(path), "cycle", voter
        current = target
        seen.add(current.name)
        if not liquid:
            return tuple(path), "single_hop", current
    return tuple(path), "depth_limit", current


def _permission(request: GovernanceRequest, policy: Policy) -> PolicyPermission:
    """Encode the current core thresholds using exact comparisons, not affordability."""
    reason, allowed = "requirements_met", True
    if not request.institutional_checks:
        reason = "checks_disabled"
    elif policy in {Policy.FARMING, Policy.MEDICINE}:
        reason = "unconditional"
    elif policy == Policy.EXPLORATION and request.resources.security.fraction() < 15:
        # Preserve the fallback's security-before-energy short-circuit explanation.
        reason, allowed = "security_below_15", False
    elif request.resources.energy.fraction() < 2:
        reason, allowed = "energy_below_2", False
    return PolicyPermission(policy=policy, allowed=allowed, reason=reason)


def decide_governance(request: GovernanceRequest) -> GovernanceSuccess:
    """Wrap the current resolver in the new contract; the live simulator is unchanged."""
    request = parse_request(request.model_dump(mode="python", warnings=False))
    agents, graph = _legacy_world(request)
    eligible = {agent.name: agent for agent in agents if agent.alive and not agent.sanctioned}
    outcome = voting_outcome(request.rule, agents, graph)
    ballots = tuple(_trace_ballot(request, agent, eligible, graph) for agent in eligible.values())
    totals = Counter(policy for ballot in ballots for policy in ballot.votes_for)
    permissions = tuple(_permission(request, policy) for policy in POLICY_ORDER)
    allowed = [item.policy for item in permissions if item.allowed]
    # Permission is applied after the election. Never discard forbidden options
    # before tallying or move their ballots to the replacement policy.
    selected = outcome.policy if outcome.policy in allowed else allowed[0]
    response = GovernanceSuccess(
        decision=GovernanceDecision(
            mandate="vote" if eligible else "recording_default", eligible_voters=tuple(eligible),
            representatives=outcome.representatives,
            scores={policy: totals[policy] for policy in POLICY_ORDER},
            voted_policy=outcome.policy, selected_policy=selected,
            permission_override=selected != outcome.policy,
        ),
        certificate=GovernanceCertificate(request_sha256=request_digest(request),
                                          ballots=ballots, permissions=permissions),
    )
    verify_governance_response(request, response)
    return response


def handle_governance_request(payload: str | dict) -> GovernanceSuccess | GovernanceFailure:
    """Return an explicit error envelope for known contract failures, never a policy default."""
    request = None
    try:
        request = parse_request(payload)
        return decide_governance(request)
    except GovernanceContractError as error:
        return GovernanceFailure(request_sha256=request_digest(request) if request else None,
                                 error=error.problem)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GovernanceContractError("invalid_certificate", message)


def _best_target(
    request: GovernanceRequest, source: str, topic: Policy, eligible: dict[str, ResidentSnapshot],
) -> str | None:
    """Check the ordered input edges directly, independently of NetworkX and the resolver."""
    candidates = [edge for edge in request.trust_links if edge.source == source
                  and edge.target in eligible and ROLE_EXPERTISE[eligible[edge.target].role] == topic]
    # max retains the first equal element, matching outgoing-edge insertion order.
    return max(candidates, key=lambda edge: edge.weight.fraction()).target if candidates else None


def _check_liquid_path(
    request: GovernanceRequest, ballot: BallotWitness, eligible: dict[str, ResidentSnapshot],
) -> str:
    """Check supplied edges locally; do not accept an arbitrary eligible terminal holder."""
    seen = {ballot.voter}
    for hop, (source, target) in enumerate(zip(ballot.path, ballot.path[1:]), start=1):
        _require(hop <= request.delegation_max_depth, "Delegation exceeds the depth budget")
        _require(target == _best_target(request, source, ballot.topic, eligible),
                 "Delegation does not follow the highest-priority eligible expert")
        if target in seen:
            _require(hop == len(ballot.path) - 1 and ballot.stop_reason == "cycle",
                     "A repeated node must close the path with cycle fallback")
            return ballot.voter
        seen.add(target)
    if len(ballot.path) - 1 == request.delegation_max_depth:
        _require(ballot.stop_reason == "depth_limit", "A full noncyclic budget ends at depth_limit")
    else:
        _require(ballot.stop_reason == "no_eligible_expert"
                 and _best_target(request, ballot.path[-1], ballot.topic, eligible) is None,
                 "Delegation stopped before its next eligible expert")
    return ballot.path[-1]


def _check_ballot(
    request: GovernanceRequest, ballot: BallotWitness, eligible: dict[str, ResidentSnapshot],
) -> None:
    voter = eligible[ballot.voter]
    _require(ballot.topic == voter.ranking[0] and ballot.path[0] == voter.name,
             "A ballot must start at its voter and keep that voter's original topic")
    holder = voter.name
    if request.rule in {"majority", "approval"}:
        _require(ballot.path == (voter.name,) and ballot.stop_reason == "direct_rule",
                 "A direct ballot cannot delegate")
    elif request.rule == "expert_delegation":
        target = _best_target(request, voter.name, ballot.topic, eligible)
        path = (voter.name,) if target is None else (voter.name, target)
        reason = "no_eligible_expert" if target is None else "single_hop"
        _require(ballot.path == path and ballot.stop_reason == reason,
                 "Single-hop delegation has an incorrect recipient or stopping reason")
        holder = voter.name if target is None else target
    else:
        holder = _check_liquid_path(request, ballot, eligible)
    count = request.approval_k if request.rule == "approval" else 1
    _require(ballot.representative == holder, "Incorrect final ballot holder")
    _require(ballot.votes_for == eligible[holder].ranking[:count],
             "Contributions must use the final holder's current ranking")


def verify_governance_response(
    request: GovernanceRequest, response: GovernanceSuccess | GovernanceFailure | dict | str,
) -> None:
    """Reject malformed, incomplete, altered, or differently bound witnesses.

    This checker reads no backend and trusts neither a reported winner nor a
    certificate's self-reported electorate. Successful checking is not a Lean proof.
    """
    request = parse_request(request.model_dump(mode="python", warnings=False))
    try:
        # Models can be created with validation bypasses. Revalidate their Python
        # data; malformed fields get one structured error, not serializer warnings.
        data = response.model_dump(mode="python", warnings=False) if isinstance(
            response, GovernanceSuccess | GovernanceFailure) else response
        if isinstance(data, str):
            data = read_contract_json(data, "invalid_response")
        parsed = RESPONSE_ADAPTER.validate_python(data)
    except ValidationError as error:
        raise GovernanceContractError("invalid_response", str(error)) from error
    if not isinstance(parsed, GovernanceSuccess):
        raise GovernanceContractError("invalid_response", "An error response has no decision certificate")
    if parsed.certificate.request_sha256 != request_digest(request):
        raise GovernanceContractError("request_mismatch", "Certificate belongs to a different request")
    _check_complete_decision(request, parsed)


def _check_complete_decision(request: GovernanceRequest, response: GovernanceSuccess) -> None:
    eligible = {resident.name: resident for resident in request.residents
                if resident.alive and not resident.sanctioned}
    decision, certificate = response.decision, response.certificate
    _require(decision.eligible_voters == tuple(eligible), "Incomplete or reordered electorate")
    _require(tuple(ballot.voter for ballot in certificate.ballots) == tuple(eligible),
             "Certificate must include every eligible ballot exactly once and in input order")
    for ballot in certificate.ballots:
        _check_ballot(request, ballot, eligible)
    representatives = {ballot.voter: ballot.representative for ballot in certificate.ballots}
    totals = Counter(policy for ballot in certificate.ballots for policy in ballot.votes_for)
    scores = {policy: totals[policy] for policy in POLICY_ORDER}
    _require(decision.representatives == representatives, "Incomplete or incorrect ballot ownership")
    _require(decision.scores == scores, "Tally must include all four policies and all contributions")
    winner = max(POLICY_ORDER, key=lambda policy: scores[policy])
    _require(decision.voted_policy == winner, "Winner violates tally or policy-order tie-breaking")
    _require(decision.mandate == ("vote" if eligible else "recording_default"),
             "An empty electorate has no elected mandate")
    permissions = tuple(_permission(request, policy) for policy in POLICY_ORDER)
    _require(certificate.permissions == permissions, "Incomplete or incorrect policy permissions")
    allowed = [item.policy for item in permissions if item.allowed]
    selected = winner if winner in allowed else allowed[0]
    _require(decision.selected_policy == selected and decision.permission_override == (selected != winner),
             "Incorrect post-election permission override")
