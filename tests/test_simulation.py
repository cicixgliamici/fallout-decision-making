import networkx as nx
import pytest

from pcds.metrics import resource_resilience
from pcds.models import Agent, CommunityState, Policy, Role, WelfareWeights
from pcds.prolog_rules import PrologRuleEngine
from pcds.scenarios import AgentSpec, default_scenario_path, load_scenario
from pcds.simulation import compare_rules, run_simulation
from pcds.voting import VOTING_RULES


def test_run_simulation_returns_requested_number_of_steps():
    results = run_simulation(rule="majority", steps=5, n_agents=10, seed=1)
    assert len(results) == 5
    assert 0.0 <= results[-1].survival_rate <= 1.0


def test_compare_rules_returns_rows():
    df = compare_rules(rules=["majority", "approval"], runs=2, steps=3, n_agents=10, seed=1)
    assert df.height == 4
    assert set(df["rule"].to_list()) == {"majority", "approval"}
    assert "seed" in df.columns
    assert "final_resilience" in df.columns


def test_same_seed_is_reproducible():
    first = run_simulation(rule="approval", steps=6, n_agents=12, seed=123)
    second = run_simulation(rule="approval", steps=6, n_agents=12, seed=123)
    assert [r.model_dump() for r in first] == [r.model_dump() for r in second]


def test_unknown_rule_raises_value_error():
    with pytest.raises(ValueError, match="Unknown voting rule"):
        run_simulation(rule="unknown", steps=1, n_agents=5, seed=1)


def test_run_simulation_rejects_non_positive_steps():
    with pytest.raises(ValueError, match="steps must be greater than zero"):
        run_simulation(rule="majority", steps=0, n_agents=5, seed=1)


def test_compare_rules_rejects_non_positive_runs():
    with pytest.raises(ValueError, match="runs must be greater than zero"):
        compare_rules(runs=0, steps=1, n_agents=5, seed=1)


def test_scenario_loader_initializes_simulation():
    scenario = load_scenario(default_scenario_path())
    results = run_simulation(rule="majority", steps=2, seed=5, scenario=scenario)
    assert scenario.name == "Shelter Alpha"
    assert len(results) == 2


def test_resource_resilience_is_normalized_against_baseline():
    assert resource_resilience(CommunityState()) == 1.0


def test_prolog_fallback_blocks_unsafe_exploration():
    engine = PrologRuleEngine(rules_file="missing.pl")
    state = CommunityState(security=10, energy=50)
    assert not engine.allocation_allowed(Policy.EXPLORATION, state)
    assert engine.allocation_allowed(Policy.FARMING, state)


@pytest.mark.parametrize("rule", VOTING_RULES)
def test_long_trajectory_survives_population_changes(rule):
    # Fixed ballots retain the original mortality-heavy regression fixture.
    scenario = load_scenario(default_scenario_path())
    scenario.parameters.decision.mode = "fixed"
    results = run_simulation(rule=rule, steps=40, seed=42, scenario=scenario)
    assert len(results) == 40
    assert any(result.survival_rate < 1.0 for result in results)
    assert all(0.0 <= result.survival_rate <= 1.0 for result in results)
    assert all(value >= 0.0 for result in results for value in result.resources.values())
    assert all(
        later.survival_rate <= earlier.survival_rate for earlier, later in zip(results, results[1:])
    )


@pytest.mark.parametrize("rule", ["expert_delegation", "liquid_democracy"])
def test_complete_extinction_keeps_trajectory_executable(rule):
    scenario = load_scenario(default_scenario_path())
    scenario.parameters.shock.probability = 1.0
    scenario.parameters.shock.health_damage = 1.0
    results = run_simulation(rule=rule, steps=4, seed=42, scenario=scenario)
    assert [result.survival_rate for result in results] == [0.0] * 4
    assert all(result.selected_policy == Policy.FARMING for result in results[1:])
    assert all(result.survivor_health is None and result.welfare == 0.0 for result in results)
    assert results[0].eligible_voters > 0
    assert results[0].preference_satisfaction is not None
    assert all(
        result.eligible_voters == 0
        and result.preference_satisfaction is None
        and result.delegation_concentration is None
        for result in results[1:]
    )


def test_population_override_applies_without_mutating_scenario():
    scenario = load_scenario(default_scenario_path())
    expected = run_simulation("majority", steps=1, n_agents=5, seed=1)
    actual = run_simulation("majority", steps=1, n_agents=5, seed=1, scenario=scenario)
    assert actual == expected
    assert scenario.agents == 40


def test_scenario_population_is_preserved_without_override(tmp_path):
    scenario = load_scenario(default_scenario_path())
    scenario.agents = 7
    path = tmp_path / "scenario.json"
    path.write_text(scenario.model_dump_json(), encoding="utf-8")
    expected = run_simulation("majority", steps=1, n_agents=7, seed=1)
    assert run_simulation("majority", steps=1, seed=1, scenario=path) == expected


def test_population_override_rejects_authored_agents():
    scenario = load_scenario(default_scenario_path())
    scenario.agents = [AgentSpec(name="farmer", role=Role.FARMER)]
    with pytest.raises(ValueError, match="explicit agent list"):
        run_simulation("majority", steps=1, n_agents=5, scenario=scenario)


@pytest.mark.parametrize("rule", ["expert_delegation", "liquid_democracy"])
@pytest.mark.parametrize("sanctioned", [False, True])
def test_trajectory_drops_dead_or_sanctioned_representative(monkeypatch, rule, sanctioned):
    voters = [
        Agent(
            name=f"voter_{index}",
            role=Role.GUARD,
            health=1.0,
            preferences=[Policy.FARMING, Policy.MEDICINE, Policy.DEFENSE, Policy.EXPLORATION],
        )
        for index in range(2)
    ]
    expert = Agent(
        name="expert",
        role=Role.FARMER,
        health=0.1,
        sanctioned=sanctioned,
        preferences=[Policy.DEFENSE, Policy.FARMING, Policy.MEDICINE, Policy.EXPLORATION],
    )
    graph = nx.DiGraph()
    graph.add_nodes_from([agent.name for agent in [*voters, expert]])
    for voter in voters:
        graph.add_edge(voter.name, expert.name, trust=1.0)
    monkeypatch.setattr(
        "pcds.simulation.create_agents_for_scenario", lambda *args, **kwargs: [*voters, expert]
    )
    monkeypatch.setattr(
        "pcds.simulation.create_trust_graph_for_scenario", lambda *args, **kwargs: graph
    )
    scenario = load_scenario(default_scenario_path())
    # This fixture isolates delegation eligibility from preference adaptation.
    scenario.parameters.decision.mode = "fixed"
    scenario.parameters.shock.probability = 1.0
    scenario.parameters.shock.health_damage = 0.2
    scenario.parameters.random_health_damage_max = 0.0
    results = run_simulation(rule, steps=3, seed=42, scenario=scenario)
    # Only the fragile expert dies; the retained trust edges must not restore
    # their vote or prevent the surviving voters from choosing directly.
    assert [result.survival_rate for result in results] == [2 / 3] * 3
    first_policy = Policy.FARMING if sanctioned else Policy.DEFENSE
    assert [result.selected_policy for result in results] == [
        first_policy,
        Policy.FARMING,
        Policy.FARMING,
    ]


def test_metric_weights_do_not_change_decisions_or_physical_outcomes():
    scenario = load_scenario(default_scenario_path())
    original = run_simulation("liquid_democracy", steps=8, n_agents=8, seed=42, scenario=scenario)
    scenario.parameters.metrics.welfare_weights = WelfareWeights(
        survival=0.0, health=1.0, resources=0.0
    )
    changed = run_simulation("liquid_democracy", steps=8, n_agents=8, seed=42, scenario=scenario)
    assert any(first.welfare != second.welfare for first, second in zip(original, changed))
    for first, second in zip(original, changed):
        assert first.selected_policy == second.selected_policy
        assert first.resources == second.resources
        assert first.survival_rate == second.survival_rate
        assert first.environmental_health_damage == second.environmental_health_damage
        assert first.welfare_sensitivity == second.welfare_sensitivity


@pytest.mark.parametrize("rule", VOTING_RULES)
def test_vote_weight_conservation_and_welfare_components_across_trajectory(rule):
    results = run_simulation(rule, steps=40, n_agents=8, seed=42)
    for result in results:
        assert sum(result.vote_weights.values()) == result.eligible_voters
        assert len(result.vote_representatives) == result.eligible_voters
        assert set(result.vote_representatives.values()) == set(result.vote_weights)
        assert sum(result.welfare_components.values()) == pytest.approx(result.welfare)
        assert result.welfare <= result.survival_rate + 1e-12
        if result.survivors:
            assert result.population_health == pytest.approx(
                result.survival_rate * result.survivor_health
            )
        else:
            assert result.survivor_health is None


@pytest.mark.parametrize("names", [[], ["duplicate", "duplicate"]])
def test_empty_or_duplicate_initial_population_is_rejected(names):
    scenario = load_scenario(default_scenario_path())
    scenario.agents = [AgentSpec(name=name, role=Role.FARMER) for name in names]
    with pytest.raises(ValueError, match="at least one|unique"):
        run_simulation("majority", steps=1, scenario=scenario)
