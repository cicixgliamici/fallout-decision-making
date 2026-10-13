import pytest
from pydantic import ValidationError

from pcds.metrics import (
    WELFARE_PROFILES,
    delegation_power,
    health_inequality,
    population_health,
    preference_satisfaction,
    resource_resilience,
    social_welfare,
    survival_rate,
    survivor_health,
    welfare_components,
)
from pcds.models import Agent, CommunityState, Policy, ResourceReference, Role, WelfareWeights


def make_agent(name, health=1.0, alive=True):
    return Agent(name=name, role=Role.FARMER, health=health, alive=alive, preferences=list(Policy))


def test_equal_health_dispersion_distinguishes_good_health_from_shared_deprivation():
    healthy = [make_agent(str(index), 0.9) for index in range(4)]
    deprived = [make_agent(str(index), 0.1) for index in range(4)]
    assert health_inequality(healthy) == health_inequality(deprived) == 0.0
    assert survivor_health(healthy) == pytest.approx(0.9)
    assert survivor_health(deprived) == pytest.approx(0.1)
    assert social_welfare(healthy, CommunityState()) > social_welfare(deprived, CommunityState())


def test_death_cannot_inflate_population_health_or_welfare():
    agents = [make_agent("survivor", 0.8), make_agent("dead", 0.04, alive=False)]
    assert survival_rate(agents) == 0.5
    assert survivor_health(agents) == 0.8
    assert population_health(agents) == 0.4
    assert health_inequality(agents) == pytest.approx(0.4)
    assert social_welfare(agents, CommunityState()) == pytest.approx(0.475)


def test_extinction_remains_zero_welfare_despite_resource_surpluses():
    agents = [make_agent("dead", 0.04, alive=False)]
    state = CommunityState(food=10000.0, water=10000.0)
    assert resource_resilience(state) > 1.0
    assert survivor_health(agents) is None
    assert population_health(agents) == health_inequality(agents) == 0.0
    assert social_welfare(agents, state) == 0.0


def test_welfare_components_and_custom_weights_are_explicit():
    agents = [make_agent("voter", 0.4)]
    weights = WelfareWeights(survival=0.5, health=0.5, resources=0.0)
    components = welfare_components(agents, CommunityState(), weights)
    assert components == {"survival": 0.5, "health": 0.2, "resources": 0.0}
    assert social_welfare(agents, CommunityState(), weights) == sum(components.values())


def test_welfare_profiles_can_reverse_a_normative_ranking():
    full_survival = [make_agent(str(index), 0.1) for index in range(4)]
    partial_survival = [make_agent(str(index), 1.0, alive=index < 3) for index in range(4)]
    state = CommunityState()
    survival_weights = WELFARE_PROFILES["survival_priority"]
    health_weights = WELFARE_PROFILES["health_priority"]
    assert social_welfare(full_survival, state, survival_weights) > social_welfare(
        partial_survival, state, survival_weights
    )
    assert social_welfare(full_survival, state, health_weights) < social_welfare(
        partial_survival, state, health_weights
    )


def test_resource_normalization_is_configurable_and_welfare_is_capped():
    reference = ResourceReference(food=50, water=50, medicine=25, energy=25, security=25)
    assert resource_resilience(CommunityState(), reference) == 2.0
    assert social_welfare([make_agent("voter")], CommunityState(), reference=reference) == 1.0


@pytest.mark.parametrize(
    "values",
    [
        {"survival": 0.5, "health": 0.5, "resources": 0.1},
        {"survival": -0.1, "health": 1.0, "resources": 0.1},
        {"survival": float("nan")},
    ],
)
def test_invalid_welfare_weights_are_rejected(values):
    with pytest.raises(ValidationError):
        WelfareWeights(**values)


@pytest.mark.parametrize("value", [0.0, -1.0, float("inf")])
def test_invalid_resource_reference_is_rejected(value):
    with pytest.raises(ValidationError):
        ResourceReference(food=value)


def test_preference_satisfaction_has_explicit_ordinal_endpoints():
    voters = [make_agent("voter")]
    assert preference_satisfaction(voters, Policy.FARMING) == 1.0
    assert preference_satisfaction(voters, Policy.MEDICINE) == pytest.approx(2 / 3)
    assert preference_satisfaction(voters, Policy.EXPLORATION) == 0.0
    assert preference_satisfaction([], Policy.FARMING) is None


def test_current_and_original_preferences_can_disagree():
    voter = make_agent("voter")
    priors = {voter.name: tuple(voter.preferences)}
    voter.preferences.reverse()
    assert preference_satisfaction([voter], Policy.EXPLORATION) == 1.0
    assert preference_satisfaction([voter], Policy.EXPLORATION, priors) == 0.0


def test_ineligible_agents_do_not_change_preference_satisfaction():
    eligible = make_agent("eligible")
    dead = make_agent("dead", alive=False)
    sanctioned = make_agent("sanctioned")
    sanctioned.sanctioned = True
    dead.preferences.reverse()
    sanctioned.preferences.reverse()
    assert preference_satisfaction([eligible, dead, sanctioned], Policy.FARMING) == 1.0
    assert preference_satisfaction([dead, sanctioned], Policy.FARMING) is None


def test_direct_ballot_control_is_equal_and_total_delegation_is_concentrated():
    direct = {str(index): str(index) for index in range(4)}
    delegated = {str(index): "0" for index in range(4)}
    assert delegation_power(direct) == {
        "delegation_concentration": 0.0,
        "max_vote_share": 0.25,
        "delegated_vote_share": 0.0,
    }
    assert delegation_power(delegated) == {
        "delegation_concentration": 1.0,
        "max_vote_share": 1.0,
        "delegated_vote_share": 0.75,
    }


def test_partial_delegation_uses_original_electorate_denominator():
    metrics = delegation_power({"a": "a", "b": "a", "c": "c", "d": "d"})
    assert metrics["delegation_concentration"] == pytest.approx(1 / 6)
    assert metrics["max_vote_share"] == 0.5
    assert metrics["delegated_vote_share"] == 0.25


def test_absent_and_single_voter_electorates_are_distinct():
    assert all(value is None for value in delegation_power({}).values())
    assert delegation_power({"sole": "sole"}) == {
        "delegation_concentration": 0.0,
        "max_vote_share": 1.0,
        "delegated_vote_share": 0.0,
    }
