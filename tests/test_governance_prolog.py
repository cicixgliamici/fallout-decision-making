"""Check transport and failure boundaries without a native installation."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from pcds.cli import app
from pcds.governance_contract import GovernanceContractError, parse_request
from pcds.governance_prolog import _term, decide_prolog
from pcds.governance_reference import decide_governance
from pcds.models import GovernanceBackend
from pcds.prolog_rules import PrologRuleEngine
from pcds.paired_analysis import governance_pairing_errors
from pcds.simulation import compare_rules
import polars as pl


@pytest.fixture
def request_snapshot():
    return parse_request((Path(__file__).resolve().parents[1] /
        "data/governance/v1/example_request.json").read_text(encoding="utf-8"))


def test_transport_uses_ground_terms_and_exact_integers():
    assert _term({"name": "O'Brien\\", "alive": True, "weight": [2**80, 3]}) == (
        "snapshot{'name':'O\\'Brien\\\\','alive':true,'weight':[1208925819614629174706176,3]}"
    )
    with pytest.raises(TypeError):
        _term(.5)


@pytest.mark.parametrize("rows", [[], [{}, {}], [{"Response": {}}]])
def test_bad_native_output_is_an_error_and_never_a_substitute_vote(request_snapshot, rows):
    engine = SimpleNamespace(available=True, _query=lambda goal: rows)
    with pytest.raises(GovernanceContractError):
        decide_prolog(request_snapshot, engine)


def test_native_resolver_cannot_use_an_unavailable_engine(request_snapshot):
    with pytest.raises(GovernanceContractError, match="requires a real backend"):
        decide_prolog(request_snapshot, SimpleNamespace(available=False))


def test_valid_shape_but_forged_tally_is_rejected(request_snapshot):
    payload = decide_governance(request_snapshot).model_dump(mode="json")
    payload["decision"]["scores"]["farming"] += 1
    payload["decision"]["permission_override"] = str(payload["decision"]["permission_override"]).lower()
    for item in payload["certificate"]["permissions"]:
        item["allowed"] = str(item["allowed"]).lower()
    engine = SimpleNamespace(available=True, _query=lambda goal: [{"Response": payload}])
    with pytest.raises(GovernanceContractError):
        decide_prolog(request_snapshot, engine)


def test_cli_native_failure_writes_an_explicit_error(monkeypatch, tmp_path, request_snapshot):
    def missing(*args):
        raise ImportError("controlled missing runtime")

    monkeypatch.setattr(PrologRuleEngine, "_load", missing)
    source, output = tmp_path / "request.json", tmp_path / "response.json"
    source.write_text(request_snapshot.model_dump_json(), encoding="utf-8")
    result = CliRunner().invoke(app, ["govern", "--backend", "prolog", "--request", str(source),
                                    "--output", str(output)])
    assert result.exit_code == 1
    assert json.loads(output.read_text())["error"]["code"] == "backend_unavailable"


def test_new_metadata_defaults_do_not_claim_native_voting():
    assert GovernanceBackend(backend="swipl").resolver == "python"


def test_historical_metadata_is_readable_but_partial_resolver_identity_is_rejected():
    raw = compare_rules(runs=1, steps=1, n_agents=3).with_columns(pl.lit("test").alias("experiment"))
    historical = raw.drop("governance_resolver", "governance_resolver_sha256", "governance_contract_version")
    assert not governance_pairing_errors(historical)
    assert governance_pairing_errors(raw.drop("governance_resolver_sha256")) == ["governance identity is incomplete"]
    forged = raw.with_columns(pl.lit("prolog").alias("governance_resolver"))
    assert any("Prolog resolver requires" in error for error in governance_pairing_errors(forged))
