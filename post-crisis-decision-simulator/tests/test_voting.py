from pcds.models import Agent, Policy, Role
from pcds.voting import approval_vote, majority_vote


def test_majority_vote_selects_most_first_place_votes():
    agents = [
        Agent(name="a", role=Role.FARMER, preferences=[Policy.FARMING, Policy.MEDICINE, Policy.DEFENSE, Policy.EXPLORATION]),
        Agent(name="b", role=Role.FARMER, preferences=[Policy.FARMING, Policy.DEFENSE, Policy.MEDICINE, Policy.EXPLORATION]),
        Agent(name="c", role=Role.DOCTOR, preferences=[Policy.MEDICINE, Policy.FARMING, Policy.DEFENSE, Policy.EXPLORATION]),
    ]
    assert majority_vote(agents) == Policy.FARMING


def test_approval_vote_uses_top_k_preferences():
    agents = [
        Agent(name="a", role=Role.FARMER, preferences=[Policy.FARMING, Policy.MEDICINE, Policy.DEFENSE, Policy.EXPLORATION]),
        Agent(name="b", role=Role.DOCTOR, preferences=[Policy.MEDICINE, Policy.FARMING, Policy.DEFENSE, Policy.EXPLORATION]),
        Agent(name="c", role=Role.GUARD, preferences=[Policy.DEFENSE, Policy.FARMING, Policy.MEDICINE, Policy.EXPLORATION]),
    ]
    assert approval_vote(agents, k=2) == Policy.FARMING
