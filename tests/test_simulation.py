import pytest

from pcds.metrics import resource_resilience
from pcds.models import CommunityState, Policy
from pcds.prolog_rules import PrologRuleEngine
from pcds.scenarios import default_scenario_path, load_scenario
from pcds.simulation import compare_rules, run_simulation


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
