"""Real SWI-Prolog checks: explicit selection must fail rather than skip or fall back."""

import json
import math

import networkx as nx
import polars as pl
import pytest
from typer.testing import CliRunner

from pcds.cli import app
from pcds.experiments import _condition_frames
from pcds.models import Agent, CommunityState, Policy, Role
from pcds.prolog_rules import PrologBackendError, PrologRuleEngine, _fallback_policy_allowed
from pcds.scenarios import default_scenario_path, load_scenario
from pcds.simulation import run_simulation

pytestmark = pytest.mark.prolog


@pytest.fixture
def engine():
    # No importorskip or fake interpreter: this fixture is the backend assertion.
    loaded = PrologRuleEngine(required=True)
    assert loaded.available and loaded.info.backend == "swipl"
    loaded.sync_world([], nx.DiGraph(), CommunityState())
    return loaded


def member(name, **status):
    return Agent(name=name, role=Role.FARMER, preferences=list(Policy), **status)


@pytest.mark.parametrize("alive,sanctioned", [(True, False), (False, False),
                                              (True, True), (False, True)])
def test_real_eligibility_matches_declared_participation(engine, alive, sanctioned):
    assert engine.eligible_to_vote(member("resident", alive=alive, sanctioned=sanctioned)) == (
        alive and not sanctioned
    )


@pytest.mark.parametrize("energy,security", [(0.0, 0.0), (2.0, 15.0), (50.0, 50.0),
    (math.nextafter(2.0, 0.0), 15.0), (2.0, math.nextafter(15.0, 0.0))])
def test_real_policy_thresholds_match_python_at_boundaries(engine, energy, security):
    state = CommunityState(energy=energy, security=security)
    for policy in Policy:
        assert engine.allocation_allowed(policy, state) == _fallback_policy_allowed(policy, state)


def test_real_world_sync_removes_obsolete_facts_and_preserves_names(engine):
    names = ["a-b", "a_b", "O'Brien", "Upper Case", "path\\name", "élève", "x'), alive(fake), ('y"]
    residents = [member(name) for name in names]
    graph = nx.DiGraph([(names[0], names[1])])
    engine.sync_world(residents, graph, CommunityState())
    assert {row["A"] for row in engine._query("alive(A)")} == set(names)
    residents[0].alive = False
    residents[1].sanctioned = True
    engine.sync_world(residents[:2], nx.DiGraph(), CommunityState())
    assert not engine.filter_eligible(residents[:2])
    assert not engine._query("trusts(_, _)")
    engine.sync_world([], nx.DiGraph(), CommunityState())
    assert not engine._query("alive(_)")
    assert not engine._query("sanctioned(_)")
    assert not engine._query("role(_, _)")


def test_invalid_rules_cannot_be_reported_as_loaded(tmp_path, engine):
    malformed = tmp_path / "broken.pl"
    malformed.write_text("eligible_to_vote( :- broken.\n", encoding="utf-8")
    with pytest.raises(PrologBackendError, match="Required SWI-Prolog"):
        PrologRuleEngine(malformed, required=True)
    with pytest.raises(PrologBackendError, match="FileNotFoundError"):
        PrologRuleEngine(tmp_path / "missing.pl", required=True)
    empty = tmp_path / "empty.pl"
    empty.write_text("% No governance predicates.\n", encoding="utf-8")
    with pytest.raises(PrologBackendError, match="predicate"):
        PrologRuleEngine(empty, required=True)


def test_default_rule_path_is_independent_of_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert PrologRuleEngine(required=True).available


def test_real_cli_event_log_records_versions_and_is_repeatable(tmp_path):
    output = tmp_path / "real.json"
    args = ["run", "--require-prolog", "--steps", "3", "--agents", "5",
            "--seed", "42", "--event-log", str(output)]
    assert CliRunner().invoke(app, args).exit_code == 0
    original = output.read_bytes()
    payload = json.loads(original)
    assert payload["governance"]["backend"] == "swipl"
    assert payload["governance"]["mode"] == "required"
    assert payload["governance"]["swipl_version"] == "9.2.9"
    assert payload["governance"]["pyswip_version"] == "0.3.3"
    assert len(payload["governance"]["rules_sha256"]) == 64
    assert CliRunner().invoke(app, args).exit_code == 0
    assert output.read_bytes() == original


def test_real_prolog_does_not_shift_external_random_events():
    plain = run_simulation("liquid_democracy", steps=4, n_agents=5, seed=42)
    checked = run_simulation("liquid_democracy", steps=4, n_agents=5, seed=42,
                             require_prolog=True)
    for left, right in zip(plain, checked):
        assert left.environmental_shock_draw == right.environmental_shock_draw
        assert left.environmental_health_damage == right.environmental_health_damage


def test_required_backend_is_propagated_to_parallel_conditions():
    scenario = load_scenario(default_scenario_path())
    scenario.agents = 3
    tasks = [("first", scenario, 1, 2, 42, False, True),
             ("second", scenario, 1, 2, 42, False, True)]
    sequential = list(_condition_frames(tasks, 1))
    parallel = list(_condition_frames(tasks, 2))
    assert all(left.equals(right) for left, right in zip(sequential, parallel))
    assert set(pl.concat(parallel)["governance_backend"]) == {"swipl"}


def test_real_research_suite_exports_backend_metadata(tmp_path):
    scenario = load_scenario(default_scenario_path())
    scenario.agents = 3
    source = tmp_path / "scenario.json"
    source.write_text(scenario.model_dump_json(), encoding="utf-8")
    output = tmp_path / "study"
    result = CliRunner().invoke(app, ["suite", "--require-prolog", "--runs", "1",
                                    "--steps", "2", "--scenario", str(source),
                                    "--output-dir", str(output)])
    assert result.exit_code == 0, result.output
    raw = pl.read_csv(output / "suite_raw.csv")
    assert set(raw["governance_backend"]) == {"swipl"}
    assert set(raw["governance_mode"]) == {"required"}
    metadata = json.loads((output / "suite_metadata.json").read_text(encoding="utf-8"))
    observed = metadata["governance"]["observed_backends"]
    assert len(observed) == 1 and observed[0]["governance_swipl_version"] == "9.2.9"
