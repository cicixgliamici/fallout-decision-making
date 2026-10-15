"""Translate contract data into a concrete proposition checked by Lean's kernel.

This adapter does not call the Python witness checker or repair a decision.
Schema validation, JSON decoding, SHA-256 and faithful literal translation are
part of the trusted boundary; the generated proof checks governance semantics.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import tomllib

from pydantic import ValidationError

from pcds.governance_contract import (
    POLICY_ORDER, RESPONSE_ADAPTER, GovernanceContractError, GovernanceRequest,
    GovernanceSuccess, parse_request, read_contract_json, request_digest,
)
from pcds.prolog_rules import PROJECT_ROOT
from pcds.provenance import source_fingerprints


class LeanCertificationError(RuntimeError):
    """No successful certification is available after a toolchain or proof failure."""


def _string(value: str) -> str:
    """Quote Lean string literals without allowing names to become source code."""
    escapes = {'"': '\\"', "\\": "\\\\", "\n": "\\n", "\r": "\\r", "\t": "\\t"}
    return '"' + "".join(escapes.get(char, f"\\u{{{ord(char):x}}}" if ord(char) < 32 else char)
                         for char in value) + '"'


def _list(items) -> str:
    values = list(items)
    if any("\n" in item for item in values):
        return "[\n" + ",\n".join(_indent(item) for item in values) + "\n]"
    return "[" + ", ".join(values) + "]"


def _record(**fields: str) -> str:
    entries = (_indent(f"{name} := {value}") for name, value in fields.items())
    return "{\n" + ",\n".join(entries) + "\n}"


def _indent(value: str) -> str:
    """Keep the retained proof source readable, including nested residents and paths."""
    return "\n".join("  " + line for line in value.split("\n"))


def _fraction(value) -> str:
    return _record(numerator=str(value.numerator), denominator=str(value.denominator))


def _request_literal(request: GovernanceRequest) -> str:
    residents = [_record(name=_string(item.name), role=f".{item.role.value}",
                         alive=str(item.alive).lower(), sanctioned=str(item.sanctioned).lower(),
                         ranking=_list(f".{policy.value}" for policy in item.ranking))
                 for item in request.residents]
    links = [_record(source=_string(item.source), target=_string(item.target), weight=_fraction(item.weight))
             for item in request.trust_links]
    return _record(decisionId=_string(request.decision_id), requestHash=_string(request_digest(request)),
                   rule=f".{request.rule}", institutionalChecks=str(request.institutional_checks).lower(),
                   residents=_list(residents), links=_list(links),
                   **{name: _fraction(getattr(request.resources, name))
                      for name in type(request.resources).model_fields})


def _claim_literal(response: GovernanceSuccess) -> str:
    decision = response.decision
    owners = _list(f"({_string(voter)}, {_string(holder)})"
                   for voter, holder in decision.representatives.items())
    scores = _list(f"(.{policy.value}, {decision.scores[policy]})" for policy in POLICY_ORDER)
    ballot_literals = []
    for item in response.certificate.ballots:
        trace = _record(holder=_string(item.representative), path=_list(map(_string, item.path)),
                        reason=_string(item.stop_reason))
        ballot_literals.append(_record(voter=_string(item.voter), topic=f".{item.topic.value}",
            trace=trace, votes=_list(f".{policy.value}" for policy in item.votes_for)))
    permissions = [_record(policy=f".{item.policy.value}", allowed=str(item.allowed).lower(),
                           reason=_string(item.reason)) for item in response.certificate.permissions]
    result = _record(mandate=_string(decision.mandate),
        eligibleVoters=_list(map(_string, decision.eligible_voters)), representatives=owners,
        scores=scores, votedPolicy=f".{decision.voted_policy.value}",
        selectedPolicy=f".{decision.selected_policy.value}",
        permissionOverride=str(decision.permission_override).lower())
    return _record(requestHash=_string(response.certificate.request_sha256), decision=result,
                   ballots=_list(ballot_literals), permissions=_list(permissions))


def parse_success(payload: str | dict) -> GovernanceSuccess:
    """Validate structure only; Lean, not a Python election, decides conformance."""
    try:
        data = read_contract_json(payload, "invalid_response") if isinstance(payload, str) else payload
        response = RESPONSE_ADAPTER.validate_python(data)
    except ValidationError as error:
        raise GovernanceContractError("invalid_response", str(error)) from error
    if not isinstance(response, GovernanceSuccess):
        raise GovernanceContractError("invalid_response", "An error response has no certifiable decision")
    if set(response.decision.scores) != set(POLICY_ORDER):
        raise GovernanceContractError("invalid_response", "All four policy scores must be supplied")
    return response


def render_lean_certificate(request: GovernanceRequest, response: GovernanceSuccess) -> str:
    """Emit the whole concrete witness, not a Python-computed acceptance boolean."""
    request = parse_request(request.model_dump(mode="json"))
    response = parse_success(response.model_dump(mode="json"))
    return (
        "import Wasteland.Governance\n\n"
        "namespace GovernanceCertificate\n"
        "open Wasteland Wasteland.Governance\n"
        "set_option maxRecDepth 10000\n"
        "set_option maxHeartbeats 2000000\n\n"
        f"def request : Request := {_request_literal(request)}\n\n"
        f"def claim : Claim := {_claim_literal(response)}\n\n"
        "/-- Kernel-checked conformance of this concrete, translated witness. -/\n"
        "theorem certificate_conforms : Conforms request claim := by decide\n\n"
        "theorem original_ballots_conserved : claim.ballots.length = (electorate request).length :=\n"
        "  accepted_ballot_count request claim certificate_conforms\n\n"
        "theorem original_voters_preserved : claim.ballots.map (·.voter) =\n"
        "    (electorate request).map (·.name) :=\n"
        "  accepted_ballot_voters request claim certificate_conforms\n\n"
        "#print axioms certificate_conforms\n"
        "end GovernanceCertificate\n"
    )


def _run(command: list[str], formal: Path) -> str:
    try:
        result = subprocess.run(command, cwd=formal, capture_output=True, text=True,
                                encoding="utf-8", stdin=subprocess.DEVNULL, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LeanCertificationError(str(error)) from error
    output = result.stdout + result.stderr
    if result.returncode or "declaration uses 'sorry'" in output or "sorryAx" in output:
        raise LeanCertificationError(output or "Lean failed without diagnostics")
    return output


def certify_governance(request: GovernanceRequest, response: GovernanceSuccess,
                       output_dir: str | Path) -> dict[str, Path]:
    """Retain source, compiled proof and receipt only after actual pinned checks.

    Failed attempts retain their source for review, but cannot leave a successful
    receipt from an earlier run: each invocation requires a new output directory.
    """
    source = render_lean_certificate(request, response)
    lake = shutil.which("lake")
    if lake is None:
        raise LeanCertificationError("Lean certification requires lake on PATH")
    formal = PROJECT_ROOT / "formal/lean"
    pins = tomllib.loads((PROJECT_ROOT / "toolchains.toml").read_text(encoding="utf-8"))
    expected = pins["formal"]["lean"]
    version = _run([lake, "env", "lean", "--version"], formal)
    if f"version {expected}," not in version:
        raise LeanCertificationError(f"Lean {expected} required; found {version.strip()}")
    _run([lake, "build", "Wasteland"], formal)
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False)
    paths = {"source": output / "GovernanceCertificate.lean", "proof": output / "GovernanceCertificate.olean",
             "receipt": output / "certification.json"}
    # Write exact UTF-8 bytes: Windows newline translation would otherwise make
    # the receipt's source hash disagree with the retained source artifact.
    paths["source"].write_bytes(source.encode("utf-8"))
    diagnostics = _run([lake, "env", "lean", "-R", str(output), "-o", str(paths["proof"]),
                        str(paths["source"])], formal)
    if not paths["proof"].is_file():
        raise LeanCertificationError("Lean returned without a compiled proof artifact")
    receipt = {
        "status": "certified", "scope": "concrete-translated-governance-v1-conformance",
        "request_sha256": request_digest(request), "lean_version": expected,
        "response_sha256": sha256(json.dumps(response.model_dump(mode="json"), sort_keys=True,
            separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest(),
        "proof_method": "decide (kernel checked); no native_decide",
        "axiom_report": diagnostics.strip(), "source_fingerprints": source_fingerprints(),
        "source_sha256": sha256(source.encode("utf-8")).hexdigest(),
        "proof_sha256": sha256(paths["proof"].read_bytes()).hexdigest(),
        "trusted_boundary": ["JSON/schema adapter", "SHA-256 calculation", "literal translation", "Lean toolchain"],
        "not_certified": ["backend identity", "physical dynamics", "all runtime executions",
                          "JSON adapter correctness", "empirical validity"],
    }
    paths["receipt"].write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return paths
