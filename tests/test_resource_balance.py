"""Check that the baseline offers a feasible finite-horizon colony budget."""

from pcds.factory import create_agents_for_scenario
from pcds.models import Policy
from pcds.randomness import sample_environment
from pcds.scenarios import default_scenario_path, load_scenario
from pcds.simulation import _apply_environmental_pressure, _apply_policy, _replenish_energy


def test_baseline_has_a_feasible_schedule_without_population_loss():
    scenario = load_scenario(default_scenario_path())
    parameters = scenario.parameters
    agents = create_agents_for_scenario(scenario, seed=42)
    state = scenario.resources.model_copy(deep=True)
    # Isolate physical feasibility from shocks and voting, using the actual
    # baseline reserve, bounded power generation, and stock-budgeted treatment.
    parameters.shock.probability = 0.0
    schedule = [Policy.FARMING] * 6 + [Policy.MEDICINE] * 3 + [Policy.DEFENSE]
    for step in range(40):
        _replenish_energy(agents, state, parameters)
        assert _apply_policy(schedule[step % 10], agents, state, 42, step, parameters) is None
        environment = sample_environment(42, step, agents, parameters)
        _apply_environmental_pressure(agents, state, environment, parameters)
        assert all(agent.alive for agent in agents)
        assert state.food > 0.0 and state.water > 0.0 and state.medicine > 0.0
    assert state.energy > 0.0


def test_legacy_budget_retains_the_original_water_deficit():
    path = default_scenario_path().with_name("shelter_alpha_legacy.json")
    scenario = load_scenario(path)
    # This contrast prevents the archival crisis from silently inheriting the
    # balanced baseline and documents why mortality was structurally likely.
    demand = scenario.agents * scenario.parameters.water_consumption
    maximum_gain = 2 * scenario.parameters.policy_impacts[Policy.EXPLORATION].water_delta
    assert demand > maximum_gain
