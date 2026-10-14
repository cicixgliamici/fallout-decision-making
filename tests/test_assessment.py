import random

import pytest
from pydantic import ValidationError

from pcds.assessment import assess_policy, assessment_context, policy_accuracy, update_preferences
from pcds.factory import create_agents_from_specs
from pcds.models import (
    Agent,
    CommunityState,
    DecisionParameters,
    Policy,
    Role,
    SimulationParameters,
)
from pcds.scenarios import AgentSpec, default_scenario_path, load_scenario
from pcds.simulation import run_simulation


def make_voter(role=Role.DOCTOR):
    return Agent(
        name="voter",
        role=role,
        health=1.0,
        cooperation=1.0,
        risk_aversion=0.0,
        preferences=list(Policy),
    )


def exact_parameters():
    parameters = SimulationParameters()
    parameters.decision = DecisionParameters(
        general_accuracy=1.0, expert_accuracy=1.0, preference_weight=0.0
    )
    return parameters


def test_rankings_follow_changing_needs_without_role_bonus():
    agent = make_voter()
    parameters = exact_parameters()
    priors = {agent.name: tuple(agent.preferences)}
    update_preferences([agent], CommunityState(food=0.0), parameters, priors, 42, 0)
    assert agent.top_choice() == Policy.FARMING
    agent.health = 0.4
    update_preferences([agent], CommunityState(food=100.0, medicine=0.0), parameters, priors, 42, 1)
    assert agent.top_choice() == Policy.MEDICINE
    assert agent.utility_for(Policy.MEDICINE) > agent.utility_for(Policy.FARMING)


def test_water_shortage_can_favor_exploration():
    agent = make_voter(Role.FARMER)
    parameters = exact_parameters()
    update_preferences(
        [agent],
        CommunityState(water=0.0),
        parameters,
        {agent.name: tuple(agent.preferences)},
        42,
        0,
    )
    assert agent.top_choice() == Policy.EXPLORATION


@pytest.mark.parametrize("noise_kind", ["observation", "effect", "both"])
def test_expertise_reduces_average_assessment_error(noise_kind):
    agent = make_voter(Role.FARMER)
    parameters = SimulationParameters()
    parameters.decision.observation_noise = 0.6 if noise_kind != "effect" else 0.0
    parameters.decision.effect_noise = 0.6 if noise_kind != "observation" else 0.0
    # Keep farming affordable while its water debit remains below the reserve
    # target: this exercises information errors without saturating every effect.
    context = assessment_context([agent], CommunityState(food=1.0, water=4.0), parameters)
    prior = tuple(agent.preferences)
    reference = assess_policy(
        agent,
        Policy.FARMING,
        context,
        parameters,
        prior,
        random.Random(0),
        perfect_information=True,
    )
    errors = {}
    for accuracy in [0.55, 0.90]:
        agent.expert_accuracy = accuracy
        errors[accuracy] = (
            sum(
                abs(
                    assess_policy(
                        agent, Policy.FARMING, context, parameters, prior, random.Random(seed)
                    )
                    - reference
                )
                for seed in range(400)
            )
            / 400
        )
    assert errors[0.90] < errors[0.55] * 0.6


def test_expertise_applies_only_to_specialist_domain():
    agent = make_voter(Role.FARMER)
    parameters = SimulationParameters()
    assert policy_accuracy(agent, Policy.FARMING, parameters) == 0.90
    assert policy_accuracy(agent, Policy.MEDICINE, parameters) == 0.55


def test_equal_accuracy_removes_direct_role_advantage():
    doctor = make_voter(Role.DOCTOR)
    farmer = make_voter(Role.FARMER)
    parameters = SimulationParameters(decision=DecisionParameters(expert_accuracy=0.55))
    context = assessment_context([doctor], CommunityState(food=0.0), parameters)
    for policy in Policy:
        doctor_score = assess_policy(
            doctor, policy, context, parameters, tuple(doctor.preferences), random.Random(42)
        )
        farmer_score = assess_policy(
            farmer, policy, context, parameters, tuple(farmer.preferences), random.Random(42)
        )
        assert doctor_score == farmer_score


def test_zero_noise_matches_exact_information_despite_limited_accuracy():
    agent = make_voter()
    parameters = SimulationParameters(
        decision=DecisionParameters(observation_noise=0.0, effect_noise=0.0)
    )
    changes, error = update_preferences(
        [agent], CommunityState(food=0.0), parameters, {agent.name: tuple(agent.preferences)}, 42, 0
    )
    assert changes >= 0
    assert error == 0.0


def test_authored_accuracy_overrides_survive_factory():
    spec = AgentSpec(name="farmer", role=Role.FARMER, general_accuracy=0.3, expert_accuracy=0.8)
    agent = create_agents_from_specs([spec])[0]
    parameters = SimulationParameters()
    assert policy_accuracy(agent, Policy.FARMING, parameters) == 0.8
    assert policy_accuracy(agent, Policy.DEFENSE, parameters) == 0.3


def test_perfect_information_has_zero_error_and_no_seed_dependence():
    first = make_voter()
    second = first.model_copy(deep=True)
    parameters = exact_parameters()
    state = CommunityState(food=0.0)
    priors = {first.name: tuple(first.preferences)}
    assert update_preferences([first], state, parameters, priors, 1, 0)[1] == 0.0
    assert update_preferences([second], state, parameters, priors, 999, 0)[1] == 0.0
    assert first.utility_weights == second.utility_weights


def test_noisy_assessments_are_reproducible_and_seed_sensitive():
    agent = make_voter()
    parameters = SimulationParameters()
    context = assessment_context([agent], CommunityState(food=0.0), parameters)
    prior = tuple(agent.preferences)

    def score(seed):
        return assess_policy(agent, Policy.FARMING, context, parameters, prior, random.Random(seed))

    assert score(1) == score(1)
    assert score(1) != score(2)


def test_other_agents_do_not_shift_private_signal_stream():
    voter = make_voter()
    other = make_voter(Role.GUARD).model_copy(update={"name": "other", "sanctioned": True})
    first_population = [voter, other]
    second_population = [agent.model_copy(deep=True) for agent in reversed(first_population)]
    parameters = SimulationParameters()
    priors = {agent.name: tuple(agent.preferences) for agent in first_population}
    update_preferences(first_population, CommunityState(food=0.0), parameters, priors, 42, 0)
    update_preferences(second_population, CommunityState(food=0.0), parameters, priors, 42, 0)
    assert first_population[0].utility_weights == second_population[1].utility_weights
    assert not other.utility_weights


def test_original_prior_does_not_drift_with_noisy_rankings():
    agent = make_voter()
    parameters = SimulationParameters()
    priors = {agent.name: tuple(agent.preferences)}
    state = CommunityState(food=0.0)
    update_preferences([agent], state, parameters, priors, 42, 0)
    scores = agent.utility_weights.copy()
    agent.preferences.reverse()
    update_preferences([agent], state, parameters, priors, 42, 0)
    assert agent.utility_weights == scores


def test_fixed_mode_preserves_supplied_ballots_and_utilities():
    agent = make_voter()
    parameters = SimulationParameters(decision=DecisionParameters(mode="fixed"))
    before = agent.model_dump()
    assert update_preferences(
        [agent], CommunityState(food=0.0), parameters, {agent.name: tuple(agent.preferences)}, 42, 0
    ) == (0, 0.0)
    assert agent.model_dump() == before


def test_empty_or_dead_population_has_no_assessments():
    agent = make_voter().model_copy(update={"alive": False})
    parameters = SimulationParameters()
    assert update_preferences([], CommunityState(), parameters, {}, 42, 0) == (0, 0.0)
    assert update_preferences(
        [agent], CommunityState(), parameters, {agent.name: tuple(agent.preferences)}, 42, 0
    ) == (0, 0.0)


@pytest.mark.parametrize(
    "field,value",
    [
        ("general_accuracy", -0.1),
        ("expert_accuracy", 1.1),
        ("observation_noise", -1),
        ("planning_horizon", 0),
        ("mode", "unknown"),
    ],
)
def test_invalid_information_parameters_are_rejected(field, value):
    with pytest.raises(ValidationError):
        DecisionParameters(**{field: value})


@pytest.mark.parametrize("rule", ["majority", "approval", "expert_delegation", "liquid_democracy"])
def test_adaptive_trajectories_expose_information_diagnostics(rule):
    results = run_simulation(rule, steps=40, seed=42)
    assert len(results) == 40
    assert any(result.preference_changes > 0 for result in results)
    assert any(result.mean_assessment_error > 0.0 for result in results)
    assert all(0.0 <= result.survival_rate <= 1.0 for result in results)


def test_fixed_trajectory_reports_no_adaptive_changes():
    scenario = load_scenario(default_scenario_path())
    scenario.parameters.decision.mode = "fixed"
    results = run_simulation("majority", steps=40, seed=42, scenario=scenario)
    assert all(
        result.preference_changes == 0 and result.mean_assessment_error == 0.0 for result in results
    )


def test_assessment_draws_do_not_shift_physical_randomness():
    scenario = load_scenario(default_scenario_path())
    scenario.agents = [AgentSpec(name="farmer", role=Role.FARMER, health=1.0)]
    scenario.resources.food = 0.0
    scenario.parameters.decision = DecisionParameters(preference_weight=10.0)
    # Strong stable priorities keep farming selected while private noise is
    # actually sampled. Assessment draws must not shift physical randomness.
    adaptive = run_simulation("majority", steps=3, seed=42, scenario=scenario)
    assert any(result.mean_assessment_error > 0.0 for result in adaptive)
    scenario.parameters.decision.mode = "fixed"
    fixed = run_simulation("majority", steps=3, seed=42, scenario=scenario)
    assert [result.selected_policy for result in adaptive] == [
        result.selected_policy for result in fixed
    ]
    for adaptive_round, fixed_round in zip(adaptive, fixed):
        assert adaptive_round.resources == fixed_round.resources
        assert adaptive_round.shock_occurred == fixed_round.shock_occurred
        assert adaptive_round.welfare == fixed_round.welfare
