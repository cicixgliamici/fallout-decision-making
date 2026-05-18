from pcds.models import Agent, Policy, Role
from pcds.voting import approval_vote, liquid_democracy_vote, majority_vote
import networkx as nx


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


def test_majority_vote_ignores_sanctioned_agents():
    agents = [
        Agent(name="a", role=Role.FARMER, preferences=[Policy.FARMING, Policy.MEDICINE, Policy.DEFENSE, Policy.EXPLORATION]),
        Agent(name="b", role=Role.DOCTOR, sanctioned=True, preferences=[Policy.MEDICINE, Policy.FARMING, Policy.DEFENSE, Policy.EXPLORATION]),
        Agent(name="c", role=Role.DOCTOR, sanctioned=True, preferences=[Policy.MEDICINE, Policy.FARMING, Policy.DEFENSE, Policy.EXPLORATION]),
    ]
    assert majority_vote(agents) == Policy.FARMING


def test_liquid_democracy_cycle_falls_back_to_direct_vote():
    agents = [
        Agent(name="a", role=Role.FARMER, preferences=[Policy.FARMING, Policy.MEDICINE, Policy.DEFENSE, Policy.EXPLORATION]),
        Agent(name="b", role=Role.FARMER, preferences=[Policy.MEDICINE, Policy.FARMING, Policy.DEFENSE, Policy.EXPLORATION]),
    ]
    graph = nx.DiGraph()
    graph.add_edge("a", "b", trust=1.0)
    graph.add_edge("b", "a", trust=1.0)
    assert liquid_democracy_vote(agents, graph) == Policy.FARMING
