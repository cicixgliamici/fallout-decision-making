"""Run the pinned Lean kernel on concrete valid and forged contract witnesses."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

import networkx as nx
import pytest
from typer.testing import CliRunner

from pcds.cli import app
from pcds.governance_contract import parse_request, snapshot_governance_request
from pcds.governance_lean import parse_success, render_lean_certificate
from pcds.governance_reference import decide_governance
from pcds.models import Agent, CommunityState, Policy, Role
from pcds.voting import VOTING_RULES

pytestmark = pytest.mark.lean
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def lean():
    lake = shutil.which("lake")
    assert lake, "Install the pinned Lean toolchain; these checks cannot be skipped"
    formal = ROOT / "formal/lean"
    build = subprocess.run([lake, "build", "Wasteland"], cwd=formal, capture_output=True,
                           stdin=subprocess.DEVNULL, text=True, encoding="utf-8", timeout=180)
    assert build.returncode == 0, build.stdout + build.stderr
    return lake, formal


def _compile(lean, source, directory):
    lake, formal = lean
    path = directory / "Cases.lean"
    path.write_text(source, encoding="utf-8")
    return subprocess.run([lake, "env", "lean", "-R", str(directory), str(path)], cwd=formal,
                          stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, encoding="utf-8", timeout=180)


def _example():
    request = parse_request((ROOT / "data/governance/v1/example_request.json").read_text(encoding="utf-8"))
    # This is an actual retained native response, rather than a mock backend.
    response = parse_success((ROOT / "docs/evidence/2026-10-15/prolog_migration/prolog_response.json")
                             .read_text(encoding="utf-8"))
    return request, response


def test_real_cli_proves_retained_prolog_witness_and_keeps_artifacts(lean, tmp_path):
    output = tmp_path / "proof"
    result = CliRunner().invoke(app, ["certify-governance", "--request",
        str(ROOT / "data/governance/v1/example_request.json"), "--response",
        str(ROOT / "docs/evidence/2026-10-15/prolog_migration/prolog_response.json"),
        "--output-dir", str(output)])
    assert result.exit_code == 0, result.output
    receipt = json.loads((output / "certification.json").read_text(encoding="utf-8"))
    assert receipt["lean_version"] == "4.19.0"
    assert receipt["status"] == "certified"
    assert "sorryAx" not in receipt["axiom_report"]
    assert "certificate_conforms" in receipt["axiom_report"]
    assert (output / "GovernanceCertificate.olean").is_file()
    assert (output / "GovernanceCertificate.lean").is_file()
    assert sha256((output / "GovernanceCertificate.lean").read_bytes()).hexdigest() == receipt["source_sha256"]
    assert sha256((output / "GovernanceCertificate.olean").read_bytes()).hexdigest() == receipt["proof_sha256"]


def test_real_lean_rejects_wrong_winner_without_success_receipt(lean, tmp_path):
    _, response = _example()
    payload = response.model_dump(mode="json")
    payload["decision"]["voted_policy"] = "medicine"
    altered = tmp_path / "altered.json"
    altered.write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "rejected"
    result = CliRunner().invoke(app, ["certify-governance", "--request",
        str(ROOT / "data/governance/v1/example_request.json"), "--response", str(altered),
        "--output-dir", str(output)])
    assert result.exit_code == 1
    assert "Lean certification failed" in result.output
    assert (output / "GovernanceCertificate.lean").is_file()
    assert not (output / "certification.json").exists()


def test_kernel_checks_all_rules_empty_electorates_cycles_and_identity_escaping(lean, tmp_path):
    sources = []
    names = ['true', 'O"Brien\\\n', 'élève', 'false']
    for rule in VOTING_RULES:
        for empty in (False, True):
            residents = [Agent(name=name, role=Role.FARMER, alive=not empty,
                                preferences=list(Policy)) for name in names]
            graph = nx.DiGraph()
            graph.add_edge(names[0], names[1], trust=.5)
            graph.add_edge(names[0], names[2], trust=.5)
            graph.add_edge(names[1], names[2], trust=1.)
            graph.add_edge(names[2], names[1], trust=1.)
            request = snapshot_governance_request(rule, residents, graph,
                CommunityState(energy=0., security=0.), decision_id=f"{rule}:{empty}", institutional_checks=True)
            # The producer is untrusted: only the generated Lean proof is accepted.
            response = decide_governance(request)
            payload = response.model_dump(mode="json")
            payload["decision"]["representatives"] = dict(reversed(list(
                payload["decision"]["representatives"].items())))
            source = render_lean_certificate(request, parse_success(payload))
            namespace = f"Case{len(sources)}"
            sources.append(source.replace("import Wasteland.Governance\n", "")
                           .replace("namespace GovernanceCertificate", f"namespace {namespace}")
                           .replace("end GovernanceCertificate", f"end {namespace}"))
    result = _compile(lean, "import Wasteland.Governance\n" + "\n".join(sources), tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count("certificate_conforms") == 8
    assert "sorryAx" not in result.stdout


def test_kernel_proves_tampered_witnesses_do_not_conform(lean, tmp_path):
    request, response = _example()
    original = response.model_dump(mode="json")
    mutations = []
    for field, value in (("mandate", "recording_default"), ("voted_policy", "medicine"),
                         ("selected_policy", "exploration"), ("permission_override", False),
                         ("eligible_voters", ["ada", "bram", "cleo"])):
        payload = deepcopy(original)
        payload["decision"][field] = value
        mutations.append(payload)
    for field, value in (("path", ["ada", "bram"]), ("representative", "bram"),
                         ("stop_reason", "depth_limit"), ("topic", "medicine"),
                         ("votes_for", ["medicine"])):
        payload = deepcopy(original)
        payload["certificate"]["ballots"][0][field] = value
        mutations.append(payload)
    payload = deepcopy(original)
    payload["certificate"]["ballots"].pop()
    mutations.append(payload)
    payload = deepcopy(original)
    payload["decision"]["scores"]["exploration"] += 1
    mutations.append(payload)
    payload = deepcopy(original)
    payload["decision"]["representatives"]["ada"] = "bram"
    mutations.append(payload)
    payload = deepcopy(original)
    payload["certificate"]["permissions"][-1]["allowed"] = True
    mutations.append(payload)
    payload = deepcopy(original)
    payload["certificate"]["request_sha256"] = "0" * 64
    mutations.append(payload)
    sources = []
    for index, payload in enumerate(mutations):
        source = render_lean_certificate(request, parse_success(payload))
        # Keep the translated data, but prove rejection instead of acceptance.
        definitions = source.split("/-- Kernel-checked")[0].replace("import Wasteland.Governance\n", "")
        definitions = definitions.replace("namespace GovernanceCertificate", f"namespace Forged{index}")
        sources.append(definitions + "example : ¬ Conforms request claim := by decide\n"
                       + f"end Forged{index}\n")
    result = _compile(lean, "import Wasteland.Governance\n" + "\n".join(sources), tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
