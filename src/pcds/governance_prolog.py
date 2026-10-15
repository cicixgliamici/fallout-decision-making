"""Transport exact contract snapshots to Prolog and check every returned witness."""

from __future__ import annotations

from pydantic import ValidationError

from pcds.governance_contract import (
    CONTRACT_VERSION, GovernanceContractError, GovernanceFailure, GovernanceRequest,
    GovernanceSuccess, parse_request, request_digest,
)
from pcds.governance_reference import verify_governance_response
from pcds.prolog_rules import PrologBackendError, PrologRuleEngine, _atom


def _term(value: object) -> str:
    """Encode ground data only; fractions stay integers and names stay quoted atoms."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return _atom(value)
    if isinstance(value, list):
        return "[" + ",".join(_term(item) for item in value) + "]"
    if isinstance(value, dict):
        return "snapshot{" + ",".join(f"{_atom(key)}:{_term(item)}" for key, item in value.items()) + "}"
    raise TypeError(f"Unsupported contract transport value: {type(value).__name__}")


def _decode_response(payload: dict) -> GovernanceSuccess:
    # PySwip exposes boolean atoms as strings. Convert only boolean fields:
    # a resident named 'true' must keep that exact identity in paths and owners.
    payload["decision"]["permission_override"] = _boolean(payload["decision"]["permission_override"])
    for permission in payload["certificate"]["permissions"]:
        permission["allowed"] = _boolean(permission["allowed"])
    return GovernanceSuccess.model_validate(payload)


def _boolean(value: object) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError("Expected a Prolog boolean atom")


def decide_prolog(request: GovernanceRequest, engine: PrologRuleEngine | None = None) -> GovernanceSuccess:
    """Use Prolog for the whole decision; never repair its output with a Python vote."""
    request = parse_request(request.model_dump(mode="json"))
    engine = engine if engine is not None else PrologRuleEngine(required=True)
    if not engine.available:
        raise GovernanceContractError("backend_unavailable", "The Prolog resolver requires a real backend")
    goal = f"pcds_governance_v1:decide({_term(request.model_dump(mode='json'))},{_atom(request_digest(request))},Response)"
    rows = engine._query(goal)
    if len(rows) != 1:
        raise GovernanceContractError("backend_query_failed", "Expected exactly one Prolog decision")
    try:
        response = _decode_response(rows[0]["Response"])
    except (ValidationError, ValueError, TypeError, KeyError) as error:
        raise GovernanceContractError("invalid_certificate", str(error)) from error
    verify_governance_response(request, response)
    engine.info = engine.info.model_copy(update={
        "resolver": "prolog", "resolver_sha256": engine.resolver_sha256,
        "contract_version": CONTRACT_VERSION,
    })
    return response


def handle_prolog_request(payload: str | dict) -> GovernanceSuccess | GovernanceFailure:
    """Expose native startup/query failures through the same explicit error envelope."""
    request = None
    try:
        request = parse_request(payload)
        return decide_prolog(request)
    except PrologBackendError as error:
        problem = GovernanceContractError(error.code, str(error)).problem
    except GovernanceContractError as error:
        problem = error.problem
    return GovernanceFailure(request_sha256=request_digest(request) if request else None, error=problem)
