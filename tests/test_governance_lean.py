"""Test the certificate adapter's boundaries without claiming native Lean coverage."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from pcds.governance_contract import GovernanceContractError, parse_request
from pcds.governance_lean import (
    LeanCertificationError, _run, _string, certify_governance, parse_success,
    render_lean_certificate,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def example():
    directory = ROOT / "data/governance/v1"
    request = parse_request((directory / "example_request.json").read_text(encoding="utf-8"))
    response = parse_success((directory / "example_response.json").read_text(encoding="utf-8"))
    return request, response


def test_literal_escaping_prevents_source_injection():
    assert _string('"\\\n\r\t\x00\x08è') == '"\\"\\\\\\n\\r\\t\\u{0}\\u{8}è"'


def test_renderer_emits_data_and_a_kernel_proof_without_python_checker(example, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No Python semantic acceptance is trusted")

    monkeypatch.setattr("pcds.governance_reference.verify_governance_response", forbidden)
    source = render_lean_certificate(*example)
    assert "theorem certificate_conforms : Conforms request claim := by decide" in source
    assert "native_decide" not in source and "sorry" not in source
    assert "3602879701896397" in source and "4503599627370496" in source
    assert 'role := .farmer' in source
    assert 'reason := "cycle"' in source


def test_renderer_does_not_hide_a_wrong_winner(example):
    request, response = example
    payload = response.model_dump(mode="json")
    payload["decision"]["voted_policy"] = "medicine"
    source = render_lean_certificate(request, parse_success(payload))
    assert "votedPolicy := .medicine" in source


def test_incomplete_scores_are_an_explicit_adapter_error(example):
    payload = example[1].model_dump(mode="json")
    payload["decision"]["scores"].pop("farming")
    with pytest.raises(GovernanceContractError, match="All four policy scores"):
        parse_success(payload)


@pytest.mark.parametrize("payload", ['{"status":"ok","status":"ok"}', '{}',
    '{"schema_version":"pcds-governance-v1","status":"error","error":{"code":"invalid_request","message":"bad"}}'])
def test_invalid_or_error_responses_cannot_be_certified(payload):
    with pytest.raises(GovernanceContractError):
        parse_success(payload)


def test_missing_lean_never_creates_a_successful_receipt(example, monkeypatch, tmp_path):
    monkeypatch.setattr("pcds.governance_lean.shutil.which", lambda _: None)
    with pytest.raises(LeanCertificationError, match="lake on PATH"):
        certify_governance(*example, tmp_path / "proof")
    assert not (tmp_path / "proof").exists()


def test_wrong_lean_version_never_creates_a_receipt(example, monkeypatch, tmp_path):
    monkeypatch.setattr("pcds.governance_lean.shutil.which", lambda _: "lake")
    monkeypatch.setattr("pcds.governance_lean._run", lambda *args: "Lean version 0.0.0,")
    with pytest.raises(LeanCertificationError, match="4.19.0 required"):
        certify_governance(*example, tmp_path / "proof")
    assert not (tmp_path / "proof").exists()


@pytest.mark.parametrize("output", ["error: rejected", "declaration uses 'sorry'", "uses sorryAx"])
def test_failed_or_admitted_proofs_are_not_success(monkeypatch, output):
    result = SimpleNamespace(returncode=int(output.startswith("error")), stdout=output, stderr="")
    monkeypatch.setattr("pcds.governance_lean.subprocess.run", lambda *args, **kwargs: result)
    with pytest.raises(LeanCertificationError):
        _run(["lake"], ROOT / "formal/lean")


def test_rejected_proof_retains_source_but_no_receipt(example, monkeypatch, tmp_path):
    def run(command, formal):
        if "--version" in command:
            return "Lean version 4.19.0,"
        if "-o" in command:
            raise LeanCertificationError("concrete proposition is false")
        return ""

    monkeypatch.setattr("pcds.governance_lean.shutil.which", lambda _: "lake")
    monkeypatch.setattr("pcds.governance_lean._run", run)
    output = tmp_path / "proof"
    with pytest.raises(LeanCertificationError, match="false"):
        certify_governance(*example, output)
    assert (output / "GovernanceCertificate.lean").is_file()
    assert not (output / "certification.json").exists()
