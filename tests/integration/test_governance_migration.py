"""Compare real Prolog decisions and full trajectories with the migration oracle."""

import math
from pathlib import Path
import random

import networkx as nx
import pytest

from pcds.governance_contract import parse_request, snapshot_governance_request
from pcds.governance_prolog import decide_prolog
from pcds.governance_reference import decide_governance
from pcds.models import Agent, CommunityState, Policy, Role
from pcds.prolog_rules import PrologRuleEngine
from pcds.simulation import run_simulation
from pcds.scenarios import default_scenario_path, load_scenario
from pcds.voting import VOTING_RULES

pytestmark = pytest.mark.prolog


@pytest.fixture(scope="module")
def engine():
    return PrologRuleEngine(required=True)


def _request(rule, seed):
    """Generate ordered snapshots independently of the production world factory."""
    rng = random.Random(seed)
    names = ["true", "false", "O'Brien", "back\\slash", "città", "a", "b", "c"]
    agents = [Agent(name=name, role=rng.choice(list(Role)),
                    preferences=rng.sample(list(Policy), len(Policy)),
                    alive=rng.random() > .2, sanctioned=rng.random() < .2) for name in names]
    graph = nx.DiGraph()
    for source in names:
        for target in rng.sample(names + ["unknown"], 6):
            graph.add_edge(source, target, trust=rng.choice([0., .5, 1.]))
    state = CommunityState(energy=rng.choice([0., 2., math.nextafter(2., 0.)]),
                           security=rng.choice([0., 15., math.nextafter(15., 0.)]))
    return snapshot_governance_request(rule, agents, graph, state,
        decision_id=f"random:{seed}", institutional_checks=seed % 2 == 0)


@pytest.mark.parametrize("rule", VOTING_RULES)
@pytest.mark.parametrize("seed", range(12))
def test_complete_decisions_match_for_ordered_seeded_snapshots(engine, rule, seed):
    request = _request(rule, seed)
    assert decide_prolog(request, engine) == decide_governance(request)


@pytest.mark.parametrize("rule", VOTING_RULES)
@pytest.mark.parametrize("edges", [[], [("a", "a")], [("a", "b"), ("b", "a")],
    [("a", "b"), ("b", "c"), ("c", "b")],
    [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")],
    [("a", "c"), ("a", "b")]])
def test_cycles_depth_and_equal_trust_preserve_the_complete_witness(engine, rule, edges):
    agents = [Agent(name=name, role=Role.FARMER, preferences=list(Policy)) for name in "abcd"]
    graph = nx.DiGraph()
    graph.add_edges_from(edges, trust=.5)
    request = snapshot_governance_request(rule, agents, graph, CommunityState(), decision_id="edges")
    assert decide_prolog(request, engine) == decide_governance(request)


@pytest.mark.parametrize("rule", VOTING_RULES)
def test_empty_electorate(engine, rule):
    request = snapshot_governance_request(rule, [], nx.DiGraph(), CommunityState(), decision_id="empty")
    assert decide_prolog(request, engine) == decide_governance(request)


def test_published_intermediate_cycle_and_permission_override(engine):
    request = parse_request((Path(__file__).resolve().parents[2] /
        "data/governance/v1/example_request.json").read_text(encoding="utf-8"))
    assert decide_prolog(request, engine) == decide_governance(request)


@pytest.mark.parametrize("rule", VOTING_RULES)
@pytest.mark.parametrize("seed", [1, 42, 123])
def test_matched_full_adaptive_trajectories(rule, seed):
    options = dict(rule=rule, steps=40, n_agents=8, seed=seed,
                   require_prolog=True, record_events=True)
    reference = run_simulation(**options, governance_resolver="python_reference")
    actual = run_simulation(**options)
    assert all(item.governance.resolver == "prolog" for item in actual)
    assert all(item.governance.resolver == "python" for item in reference)
    assert [item.model_dump(exclude={"governance"}) for item in actual] == [
        item.model_dump(exclude={"governance"}) for item in reference]


def test_native_simulation_does_not_call_the_python_voting_producer(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Python voting must not produce a native decision")

    monkeypatch.setattr("pcds.simulation.voting_outcome", forbidden)
    monkeypatch.setattr("pcds.governance_reference.voting_outcome", forbidden)
    result = run_simulation("liquid_democracy", steps=2, n_agents=8, seed=42, require_prolog=True)
    assert result[-1].governance.resolver == "prolog"


def test_exact_trust_comparison_and_elder_expertise(engine):
    agents = [Agent(name=name, role=Role.ELDER,
                    preferences=[Policy.MEDICINE, Policy.DEFENSE, Policy.FARMING, Policy.EXPLORATION])
              for name in "abc"]
    graph = nx.DiGraph()
    graph.add_edge("a", "b", trust=.5)
    graph.add_edge("a", "c", trust=.5)
    payload = snapshot_governance_request("expert_delegation", agents, graph, CommunityState(),
                                          decision_id="exact").model_dump(mode="json")
    # The second edge is strictly stronger although both round to 0.5 as floats.
    payload["trust_links"][1]["weight"] = {"numerator": 2**80 + 1, "denominator": 2**81}
    request = parse_request(payload)
    actual = decide_prolog(request, engine)
    assert actual == decide_governance(request)
    assert actual.decision.representatives["a"] == "c"


@pytest.mark.parametrize("rule", VOTING_RULES)
def test_post_extinction_and_unaffordable_rounds_match(rule):
    scenario = load_scenario(default_scenario_path())
    scenario.agents = 3
    scenario.resources.food = scenario.resources.water = scenario.resources.energy = 0.
    scenario.parameters.energy_replenishment = 0.
    scenario.parameters.shock.probability = 1.
    scenario.parameters.shock.health_damage = 1.
    options = dict(rule=rule, scenario=scenario, steps=3, seed=42,
                   require_prolog=True, record_events=True)
    reference = run_simulation(**options, governance_resolver="python_reference")
    native = run_simulation(**options)
    assert native[-1].policy_block_reason == "no_living_residents"
    assert native[0].policy_block_reason.startswith("insufficient_")
    assert [item.model_dump(exclude={"governance"}) for item in native] == [
        item.model_dump(exclude={"governance"}) for item in reference]
