import pytest

from pcds.models import Agent, CommunityState, Policy, Role, SimulationParameters
from pcds.randomness import sample_environment
from pcds.scenarios import default_scenario_path, load_scenario
from pcds.simulation import _apply_policy, compare_rules, run_simulation
from pcds.voting import VOTING_RULES, VotingOutcome


def make_agent(name, alive=True):
    return Agent(name=name, role=Role.FARMER, health=0.4, alive=alive, preferences=list(Policy))


def test_external_draws_match_despite_different_policies_and_deaths(monkeypatch):
    selected = dict(zip(VOTING_RULES, Policy))
    monkeypatch.setattr(
        "pcds.simulation._select_policy",
        lambda rule, agents, graph: VotingOutcome(
            selected[rule], {agent.name: agent.name for agent in agents}
        ),
    )
    scenario = load_scenario(default_scenario_path())
    scenario.agents = 8
    scenario.parameters.decision.mode = "fixed"
    scenario.parameters.shock.probability = 0.35
    scenario.parameters.random_health_damage_max = 0.06
    trajectories = [
        run_simulation(rule, steps=40, seed=42, scenario=scenario) for rule in VOTING_RULES
    ]
    reference = trajectories[0]
    assert any(result.shock_occurred for result in reference)
    assert not all(result.shock_occurred for result in reference)
    assert (
        len({tuple(result.survival_rate for result in trajectory) for trajectory in trajectories})
        > 1
    )
    for trajectory in trajectories[1:]:
        assert trajectory[0].selected_policy != reference[0].selected_policy
        for expected, actual in zip(reference, trajectory):
            assert actual.environmental_shock_draw == expected.environmental_shock_draw
            assert actual.shock_occurred == expected.shock_occurred
            assert actual.environmental_health_damage == expected.environmental_health_damage
            assert len(actual.environmental_health_damage) == 8


def test_environment_is_independent_of_order_and_survival():
    first = make_agent("first")
    second = make_agent("second")
    parameters = SimulationParameters()
    original = sample_environment(42, 5, [first, second], parameters)
    first.alive = False
    assert sample_environment(42, 5, [second, first], parameters) == original
    reduced = sample_environment(42, 5, [second], parameters)
    assert reduced.shock_draw == original.shock_draw
    assert reduced.health_damage["second"] == original.health_damage["second"]
    assert sample_environment(43, 5, [second], parameters) != reduced


@pytest.mark.parametrize("policy", [Policy.MEDICINE, Policy.EXPLORATION])
def test_policy_draws_for_survivor_ignore_other_agents(policy):
    target = make_agent("target")
    other = make_agent("other")
    isolated = target.model_copy(deep=True)
    parameters = SimulationParameters()
    parameters.policy_impacts[Policy.EXPLORATION].injury_probability = 1.0
    shared_state = CommunityState()
    isolated_state = CommunityState()
    _apply_policy(policy, [other, target], shared_state, 42, 3, parameters)
    _apply_policy(policy, [isolated], isolated_state, 42, 3, parameters)
    assert target.health == isolated.health
    # Individual potential healing draws stay fixed; treating an additional
    # resident now correctly spends additional shared medical stock.
    assert shared_state.model_dump(exclude={"medicine"}) == isolated_state.model_dump(
        exclude={"medicine"}
    )
    if policy == Policy.MEDICINE:
        assert isolated_state.medicine - shared_state.medicine == pytest.approx(other.health - 0.4)
    else:
        assert shared_state.medicine == isolated_state.medicine


def test_compare_records_matching_environment_digests():
    raw = compare_rules(runs=2, steps=40, n_agents=8, seed=42)
    for seed in [42, 43]:
        rows = [row for row in raw.iter_rows(named=True) if row["seed"] == seed]
        assert len({row["environment_trace_digest"] for row in rows}) == 1
        assert len({row["shock_count"] for row in rows}) == 1
    assert raw["environment_trace_digest"].n_unique() == 2


def test_unseeded_run_can_be_replayed_from_recorded_seed():
    original = run_simulation("majority", steps=3, n_agents=8)
    replay = run_simulation("majority", steps=3, n_agents=8, seed=original[0].simulation_seed)
    assert original == replay
