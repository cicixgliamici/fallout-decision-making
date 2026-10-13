import networkx as nx
import pytest

from pcds.models import Agent, Policy, Role
from pcds.voting import (
    _resolve_delegate,
    approval_vote,
    expert_delegation_vote,
    liquid_democracy_vote,
    majority_vote,
    voting_outcome,
)


def test_majority_vote_selects_most_first_place_votes():
    agents = [
        Agent(
            name="a",
            role=Role.FARMER,
            preferences=[Policy.FARMING, Policy.MEDICINE, Policy.DEFENSE, Policy.EXPLORATION],
        ),
        Agent(
            name="b",
            role=Role.FARMER,
            preferences=[Policy.FARMING, Policy.DEFENSE, Policy.MEDICINE, Policy.EXPLORATION],
        ),
        Agent(
            name="c",
            role=Role.DOCTOR,
            preferences=[Policy.MEDICINE, Policy.FARMING, Policy.DEFENSE, Policy.EXPLORATION],
        ),
    ]
    assert majority_vote(agents) == Policy.FARMING


def test_approval_vote_uses_top_k_preferences():
    agents = [
        Agent(
            name="a",
            role=Role.FARMER,
            preferences=[Policy.FARMING, Policy.MEDICINE, Policy.DEFENSE, Policy.EXPLORATION],
        ),
        Agent(
            name="b",
            role=Role.DOCTOR,
            preferences=[Policy.MEDICINE, Policy.FARMING, Policy.DEFENSE, Policy.EXPLORATION],
        ),
        Agent(
            name="c",
            role=Role.GUARD,
            preferences=[Policy.DEFENSE, Policy.FARMING, Policy.MEDICINE, Policy.EXPLORATION],
        ),
    ]
    assert approval_vote(agents, k=2) == Policy.FARMING


def test_majority_vote_ignores_sanctioned_agents():
    agents = [
        Agent(
            name="a",
            role=Role.FARMER,
            preferences=[Policy.FARMING, Policy.MEDICINE, Policy.DEFENSE, Policy.EXPLORATION],
        ),
        Agent(
            name="b",
            role=Role.DOCTOR,
            sanctioned=True,
            preferences=[Policy.MEDICINE, Policy.FARMING, Policy.DEFENSE, Policy.EXPLORATION],
        ),
        Agent(
            name="c",
            role=Role.DOCTOR,
            sanctioned=True,
            preferences=[Policy.MEDICINE, Policy.FARMING, Policy.DEFENSE, Policy.EXPLORATION],
        ),
    ]
    assert majority_vote(agents) == Policy.FARMING


def test_liquid_democracy_cycle_falls_back_to_direct_vote():
    agents = [
        Agent(
            name="a",
            role=Role.FARMER,
            preferences=[Policy.FARMING, Policy.MEDICINE, Policy.DEFENSE, Policy.EXPLORATION],
        ),
        Agent(
            name="b",
            role=Role.FARMER,
            preferences=[Policy.MEDICINE, Policy.FARMING, Policy.DEFENSE, Policy.EXPLORATION],
        ),
    ]
    graph = nx.DiGraph()
    graph.add_edge("a", "b", trust=1.0)
    graph.add_edge("b", "a", trust=1.0)
    assert liquid_democracy_vote(agents, graph) == Policy.FARMING


def make_agent(name, choice, **state):
    return Agent(
        name=name,
        role=Role.FARMER,
        preferences=[choice, *[policy for policy in Policy if policy != choice]],
        **state,
    )


@pytest.mark.parametrize("vote", [expert_delegation_vote, liquid_democracy_vote])
@pytest.mark.parametrize("exclusion", [{"alive": False}, {"sanctioned": True}])
@pytest.mark.parametrize("filtered", [False, True])
def test_delegation_ignores_ineligible_targets(vote, exclusion, filtered):
    voter = make_agent("voter", Policy.FARMING)
    excluded = make_agent("excluded", Policy.DEFENSE, **exclusion)
    expert = make_agent("expert", Policy.MEDICINE)
    graph = nx.DiGraph()
    graph.add_edge("voter", "excluded", trust=1.0)
    graph.add_edge("voter", "unknown", trust=1.0)
    graph.add_edge("voter", "expert", trust=0.8)
    agents = [voter, expert] if filtered else [voter, excluded, expert]
    assert vote(agents, graph) == Policy.MEDICINE


@pytest.mark.parametrize("vote", [expert_delegation_vote, liquid_democracy_vote])
def test_delegation_without_graph_node_votes_directly(vote):
    assert vote([make_agent("voter", Policy.DEFENSE)], nx.DiGraph()) == Policy.DEFENSE


@pytest.mark.parametrize("vote", [expert_delegation_vote, liquid_democracy_vote])
def test_delegation_without_eligible_expert_votes_directly(vote):
    graph = nx.DiGraph()
    graph.add_edge("voter", "excluded", trust=1.0)
    assert vote([make_agent("voter", Policy.DEFENSE)], graph) == Policy.DEFENSE


@pytest.mark.parametrize("vote", [expert_delegation_vote, liquid_democracy_vote])
def test_delegation_with_empty_electorate_uses_default(vote):
    assert vote([], nx.DiGraph()) == Policy.FARMING


@pytest.mark.parametrize("cycle_length", [1, 2, 3])
def test_selected_cycle_restores_original_ballot(cycle_length):
    agents = [make_agent(str(index), Policy.FARMING) for index in range(cycle_length)]
    alternative = make_agent("alternative", Policy.MEDICINE)
    agent_map = {agent.name: agent for agent in [*agents, alternative]}
    graph = nx.DiGraph()
    for index, agent in enumerate(agents):
        graph.add_edge(agent.name, agents[(index + 1) % cycle_length].name, trust=1.0)
    # A lower-trust exit must not silently replace the selected cyclic path.
    graph.add_edge(agents[-1].name, alternative.name, trust=0.5)
    assert _resolve_delegate(agents[0], Policy.FARMING, agent_map, graph, 3) is agents[0]


def test_delegation_chain_stops_at_depth_limit():
    agents = [make_agent(str(index), Policy.FARMING) for index in range(5)]
    graph = nx.DiGraph()
    for source, target in zip(agents, agents[1:]):
        graph.add_edge(source.name, target.name, trust=1.0)
    agent_map = {agent.name: agent for agent in agents}
    assert _resolve_delegate(agents[0], Policy.FARMING, agent_map, graph, 3) is agents[3]


@pytest.mark.parametrize("rule", ["majority", "approval"])
def test_direct_vote_trace_preserves_equal_original_ballot_ownership(rule):
    agents = [
        make_agent("a", Policy.FARMING),
        make_agent("b", Policy.MEDICINE),
        make_agent("excluded", Policy.MEDICINE, sanctioned=True),
    ]
    outcome = voting_outcome(rule, agents, nx.DiGraph())
    assert outcome.representatives == {"a": "a", "b": "b"}


@pytest.mark.parametrize("rule", ["expert_delegation", "liquid_democracy"])
def test_vote_trace_measures_the_expert_who_actually_controls_ballots(rule):
    agents = [
        make_agent("a", Policy.FARMING),
        make_agent("b", Policy.FARMING),
        make_agent("expert", Policy.MEDICINE),
    ]
    graph = nx.DiGraph()
    graph.add_edge("a", "expert", trust=1.0)
    graph.add_edge("b", "expert", trust=1.0)
    outcome = voting_outcome(rule, agents, graph)
    assert outcome.policy == Policy.MEDICINE
    assert outcome.representatives == {"a": "expert", "b": "expert", "expert": "expert"}


def test_liquid_cycle_restores_ballot_ownership_as_well_as_choice():
    agents = [make_agent("a", Policy.FARMING), make_agent("b", Policy.FARMING)]
    graph = nx.DiGraph()
    graph.add_edge("a", "b", trust=1.0)
    graph.add_edge("b", "a", trust=1.0)
    assert voting_outcome("liquid_democracy", agents, graph).representatives == {"a": "a", "b": "b"}
