"""Pin the wire contract to current voting behavior and reject forged witnesses."""

from copy import deepcopy
from fractions import Fraction
import json
import math
from pathlib import Path

import networkx as nx
import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from pcds.assessment import update_preferences
from pcds.cli import app
from pcds.factory import create_agents_for_scenario, create_trust_graph_for_scenario
from pcds.governance_contract import (
    CONTRACT_VERSION, POLICY_ORDER, ROLE_EXPERTISE, RESPONSE_ADAPTER, ExactValue,
    GovernanceContractError, GovernanceRequest, GovernanceSuccess, parse_request,
    request_digest, snapshot_governance_request,
)
from pcds.governance_reference import (
    decide_governance, handle_governance_request, verify_governance_response,
)
from pcds.models import EXPERTISE, Agent, CommunityState, Policy, Role
from pcds.scenarios import default_scenario_path, load_scenario
from pcds.simulation import _replenish_energy, run_simulation
from pcds.voting import VOTING_RULES, voting_outcome

ROOT = Path(__file__).resolve().parents[1]


def resident(name, choice=Policy.FARMING, role=Role.FARMER, **status):
    return Agent(name=name, role=role,
                 preferences=[choice, *[policy for policy in Policy if policy != choice]], **status)


def make_request(agents=None, edges=(), rule="liquid_democracy", checks=False, state=None):
    graph = nx.DiGraph()
    for source, target, weight in edges:
        graph.add_edge(source, target, trust=weight)
    return snapshot_governance_request(
        rule, [resident("a"), resident("b")] if agents is None else agents,
        graph, state or CommunityState(), decision_id="test:round:0", institutional_checks=checks,
    )


def first_ballot(response):
    return response.certificate.ballots[0]


def test_contract_expertise_matches_the_actual_python_map_including_elders():
    assert ROLE_EXPERTISE == EXPERTISE


@pytest.mark.parametrize("rule", VOTING_RULES)
@pytest.mark.parametrize("seed", [1, 42, 123])
def test_contract_matches_a_real_adaptive_simulation_round(rule, seed):
    scenario = load_scenario(default_scenario_path())
    scenario.agents = 8
    agents = create_agents_for_scenario(scenario, seed)
    graph = create_trust_graph_for_scenario(scenario, agents, seed)
    state = scenario.resources.model_copy(deep=True)
    priors = {agent.name: tuple(agent.preferences) for agent in agents}
    _replenish_energy(agents, state, scenario.parameters)
    update_preferences(agents, state, scenario.parameters, priors, seed, 0)
    before = ([agent.model_dump() for agent in agents], state.model_dump(), list(graph.edges(data=True)))
    request = snapshot_governance_request(rule, agents, graph, state, decision_id=f"{seed}:0")
    response = decide_governance(request)
    legacy = voting_outcome(rule, agents, graph)
    trajectory = run_simulation(rule, steps=1, seed=seed, scenario=scenario)
    assert response.decision.voted_policy == legacy.policy == trajectory[0].selected_policy
    assert response.decision.representatives == legacy.representatives == trajectory[0].vote_representatives
    assert response.decision.eligible_voters == tuple(legacy.representatives)
    assert ([agent.model_dump() for agent in agents], state.model_dump(), list(graph.edges(data=True))) == before
    verify_governance_response(request, response.model_dump_json())


@pytest.mark.parametrize("rule", VOTING_RULES)
def test_no_electorate_is_a_recording_default_with_complete_zero_tally(rule):
    request = make_request([resident("dead", alive=False), resident("excluded", sanctioned=True)], rule=rule)
    response = decide_governance(request)
    assert response.decision.mandate == "recording_default"
    assert response.decision.selected_policy == Policy.FARMING
    assert response.decision.eligible_voters == ()
    assert response.decision.representatives == {}
    assert response.decision.scores == dict.fromkeys(Policy, 0)
    assert response.certificate.ballots == ()


def test_approval_records_two_contributions_but_one_original_ballot_per_voter():
    response = decide_governance(make_request(rule="approval"))
    assert len(response.certificate.ballots) == len(response.decision.representatives) == 2
    assert sum(response.decision.scores.values()) == 4
    assert response.decision.voted_policy == Policy.FARMING
    assert all(ballot.stop_reason == "direct_rule" for ballot in response.certificate.ballots)


@pytest.mark.parametrize("rule", VOTING_RULES)
def test_policy_score_ties_use_declaration_order(rule):
    request = make_request([resident("a", Policy.DEFENSE), resident("b", Policy.MEDICINE)], rule=rule)
    response = decide_governance(request)
    expected = Policy.FARMING if rule == "approval" else Policy.MEDICINE
    assert response.decision.voted_policy == expected


def test_equal_trust_uses_edge_order_and_skips_unknown_dead_or_sanctioned_targets():
    agents = [resident("voter"), resident("z", Policy.MEDICINE), resident("a", Policy.DEFENSE),
              resident("dead", alive=False), resident("excluded", sanctioned=True)]
    edges = [("voter", "unknown", 1.0), ("voter", "dead", 1.0), ("voter", "excluded", 1.0),
             ("voter", "z", 0.8), ("voter", "a", 0.8)]
    request = make_request(agents, edges, rule="expert_delegation")
    ballot = first_ballot(decide_governance(request))
    assert ballot.path == ("voter", "z")
    assert ballot.votes_for == (Policy.MEDICINE,)
    reversed_ties = make_request(agents, [*edges[:3], edges[4], edges[3]], rule="expert_delegation")
    assert first_ballot(decide_governance(reversed_ties)).representative == "a"
    assert request_digest(request) != request_digest(reversed_ties)


def test_topic_stays_with_origin_even_when_intermediate_holder_prefers_another_policy():
    agents = [resident("voter"), resident("farmer", Policy.MEDICINE),
              resident("next_farmer", Policy.DEFENSE), resident("doctor", Policy.EXPLORATION, Role.DOCTOR)]
    edges = [("voter", "farmer", 1.0), ("farmer", "doctor", 1.0), ("farmer", "next_farmer", 0.8)]
    ballot = first_ballot(decide_governance(make_request(agents, edges)))
    assert ballot.path == ("voter", "farmer", "next_farmer")
    assert ballot.topic == Policy.FARMING
    assert ballot.stop_reason == "no_eligible_expert"
    assert ballot.votes_for == (Policy.DEFENSE,)


@pytest.mark.parametrize("cycle_size", [1, 2, 3])
def test_cycles_keep_the_closing_edge_and_restore_the_origin(cycle_size):
    agents = [resident(str(index)) for index in range(cycle_size)]
    edges = [(str(index), str((index + 1) % cycle_size), 1.0) for index in range(cycle_size)]
    ballot = first_ballot(decide_governance(make_request(agents, edges)))
    assert ballot.path == (*[str(index) for index in range(cycle_size)], "0")
    assert ballot.stop_reason == "cycle" and ballot.representative == "0"


def test_cycle_repeating_an_intermediate_node_still_restores_the_origin():
    agents = [resident(name) for name in ("origin", "b", "c", "exit")]
    edges = [("origin", "b", 1.0), ("b", "c", 1.0), ("c", "b", 1.0), ("c", "exit", 0.8)]
    ballot = first_ballot(decide_governance(make_request(agents, edges)))
    assert ballot.path == ("origin", "b", "c", "b")
    assert ballot.representative == "origin" and ballot.stop_reason == "cycle"


def test_depth_limit_is_checked_before_a_fourth_hop_even_if_that_hop_would_close_a_cycle():
    agents = [resident(str(index)) for index in range(4)]
    edges = [(str(index), str((index + 1) % 4), 1.0) for index in range(4)]
    ballot = first_ballot(decide_governance(make_request(agents, edges)))
    assert ballot.path == ("0", "1", "2", "3")
    assert ballot.stop_reason == "depth_limit" and ballot.representative == "3"


def test_single_hop_self_delegation_is_not_the_liquid_cycle_case():
    request = make_request([resident("a")], [("a", "a", 1)], rule="expert_delegation")
    ballot = first_ballot(decide_governance(request))
    assert ballot.path == ("a", "a") and ballot.stop_reason == "single_hop"


def test_permissions_override_after_the_vote_without_reallocating_ballots():
    request = make_request([resident("a", Policy.EXPLORATION)], rule="majority", checks=True,
                           state=CommunityState(energy=1, security=14))
    response = decide_governance(request)
    assert response.decision.voted_policy == Policy.EXPLORATION
    assert response.decision.selected_policy == Policy.FARMING
    assert response.decision.permission_override
    assert response.decision.scores[Policy.EXPLORATION] == 1
    assert response.decision.scores[Policy.FARMING] == 0
    assert first_ballot(response).votes_for == (Policy.EXPLORATION,)
    assert response.certificate.permissions[-1].reason == "security_below_15"


def test_institutional_permission_does_not_claim_physical_affordability():
    request = make_request([resident("a", Policy.DEFENSE)], rule="majority", checks=True,
                           state=CommunityState(energy=2))
    decision = decide_governance(request).decision
    assert decision.selected_policy == Policy.DEFENSE and not decision.permission_override
    assert "policy_executed" not in decision.model_dump()


@pytest.mark.parametrize("energy,security,allowed", [
    (2.0, 15.0, True), (math.nextafter(2.0, 0.0), 15.0, False),
    (2.0, math.nextafter(15.0, 0.0), False),
])
def test_exact_transport_preserves_permission_boundaries(energy, security, allowed):
    request = make_request(checks=True, state=CommunityState(energy=energy, security=security))
    assert request.resources.energy.fraction() == Fraction(energy)
    assert request.resources.security.fraction() == Fraction(security)
    assert decide_governance(request).certificate.permissions[-1].allowed is allowed


def test_missing_trust_weight_defaults_to_zero_and_snapshot_does_not_follow_later_mutations():
    agents = [resident("a"), resident("b")]
    graph = nx.DiGraph([("a", "b")])
    state = CommunityState()
    request = snapshot_governance_request("expert_delegation", agents, graph, state, decision_id="snapshot")
    digest = request_digest(request)
    assert request.trust_links[0].weight.fraction() == 0
    agents[0].alive = False
    graph.clear()
    state.energy = 0
    assert request_digest(request) == digest
    assert first_ballot(decide_governance(request)).representative == "b"


@pytest.mark.parametrize("change", ["duplicate_resident", "duplicate_edge", "duplicate_policy",
                                    "missing_policy", "unknown_rule", "extra_field", "bad_order",
                                    "custom_depth", "custom_approval", "bool_as_count", "bad_weight"])
def test_invalid_states_are_explicit_errors_without_a_successful_decision(change):
    payload = make_request(edges=[("a", "b", 1)]).model_dump(mode="json")
    if change == "duplicate_resident":
        payload["residents"].append(deepcopy(payload["residents"][0]))
    elif change == "duplicate_edge":
        payload["trust_links"].append(deepcopy(payload["trust_links"][0]))
    elif change == "duplicate_policy":
        payload["residents"][0]["ranking"][1] = "farming"
    elif change == "missing_policy":
        payload["residents"][0]["ranking"].pop()
    elif change == "unknown_rule":
        payload["rule"] = "majority_absolute"
    elif change == "extra_field":
        payload["automatic_reroute"] = True
    elif change == "bad_order":
        payload["policy_order"].reverse()
    elif change == "custom_depth":
        payload["delegation_max_depth"] = 4
    elif change == "custom_approval":
        payload["approval_k"] = 1
    elif change == "bool_as_count":
        payload["resources"]["energy"]["numerator"] = True
    elif change == "bad_weight":
        payload["trust_links"][0]["weight"] = {"numerator": 2, "denominator": 1}
    response = handle_governance_request(payload)
    assert response.status == "error" and response.error.code == "invalid_request"
    assert "decision" not in response.model_dump() and "certificate" not in response.model_dump()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True, "0.5"])
def test_invalid_source_numbers_are_rejected(value):
    with pytest.raises(ValueError):
        ExactValue.from_number(value)


@pytest.mark.parametrize("numerator,denominator", [(1, 0), (2, 4), (0, 2), (-1, 1)])
def test_fraction_representation_is_unambiguous(numerator, denominator):
    with pytest.raises(ValidationError):
        ExactValue(numerator=numerator, denominator=denominator)


def test_version_and_duplicate_json_fields_are_rejected():
    payload = make_request().model_dump(mode="json")
    payload["schema_version"] = "future-version"
    assert handle_governance_request(payload).error.code == "unsupported_version"
    duplicate = '{"schema_version":"pcds-governance-v1","rule":"approval","rule":"majority"}'
    failure = handle_governance_request(duplicate)
    assert failure.error.code == "invalid_request" and "Duplicate JSON member" in failure.error.message
    assert handle_governance_request("{").status == "error"


def test_digest_normalizes_object_order_and_defaults_but_binds_the_decision_identity():
    request = make_request()
    data = request.model_dump(mode="json")
    for key in ("institutional_checks", "approval_k", "delegation_max_depth", "policy_order", "trust_links"):
        data.pop(key)
    reordered = dict(reversed(list(data.items())))
    assert request_digest(parse_request(reordered)) == request_digest(request)
    data["decision_id"] = "another-round"
    with pytest.raises(GovernanceContractError) as error:
        verify_governance_response(parse_request(data), decide_governance(request))
    assert error.value.problem.code == "request_mismatch"


@pytest.mark.parametrize("change", ["omit_ballot", "duplicate_ballot", "omit_voter", "omit_score",
    "wrong_score", "wrong_winner", "wrong_holder", "wrong_topic", "wrong_contribution",
    "short_path", "wrong_stop", "lower_trust", "wrong_permission", "wrong_selection", "false_mandate"])
def test_checker_rejects_tampered_or_incomplete_certificates(change):
    agents = [resident("a"), resident("b", Policy.MEDICINE), resident("c", Policy.DEFENSE)]
    request = make_request(agents, [("a", "b", 1), ("a", "c", 0.8)])
    data = decide_governance(request).model_dump(mode="json")
    ballot, decision = data["certificate"]["ballots"][0], data["decision"]
    if change == "omit_ballot":
        data["certificate"]["ballots"].pop()
    elif change == "duplicate_ballot":
        data["certificate"]["ballots"].append(deepcopy(ballot))
    elif change == "omit_voter":
        decision["eligible_voters"].pop()
    elif change == "omit_score":
        decision["scores"].pop("exploration")
    elif change == "wrong_score":
        decision["scores"]["exploration"] += 1
    elif change == "wrong_winner":
        decision["voted_policy"] = "exploration"
    elif change == "wrong_holder":
        decision["representatives"]["a"] = "c"
    elif change == "wrong_topic":
        ballot["topic"] = "medicine"
    elif change == "wrong_contribution":
        ballot["votes_for"] = ["exploration"]
    elif change == "short_path":
        ballot["path"] = ["a"]
    elif change == "wrong_stop":
        ballot["stop_reason"] = "depth_limit"
    elif change == "lower_trust":
        ballot.update(path=["a", "c"], representative="c", votes_for=["defense"])
        decision["representatives"]["a"] = "c"
    elif change == "wrong_permission":
        data["certificate"]["permissions"].pop()
    elif change == "wrong_selection":
        decision["selected_policy"] = "exploration"
    elif change == "false_mandate":
        decision["mandate"] = "recording_default"
    with pytest.raises(GovernanceContractError) as error:
        verify_governance_response(request, data)
    assert error.value.problem.code == "invalid_certificate"


def test_error_envelopes_and_unknown_response_fields_are_not_accepted_as_certificates():
    request = make_request()
    failure = handle_governance_request({"schema_version": "future-version"})
    with pytest.raises(GovernanceContractError, match="no decision certificate"):
        verify_governance_response(request, failure)
    data = decide_governance(request).model_dump(mode="json")
    data["lean_verified"] = True
    with pytest.raises(GovernanceContractError) as error:
        verify_governance_response(request, data)
    assert error.value.problem.code == "invalid_response"


def test_cycle_certificate_cannot_move_the_vote_to_its_repeated_intermediate_node():
    request = make_request([resident(name) for name in ("a", "b", "c")],
                           [("a", "b", 1), ("b", "c", 1), ("c", "b", 1)])
    data = decide_governance(request).model_dump(mode="json")
    data["certificate"]["ballots"][0]["representative"] = "b"
    data["decision"]["representatives"]["a"] = "b"
    with pytest.raises(GovernanceContractError, match="Incorrect final ballot holder"):
        verify_governance_response(request, data)


def test_checker_revalidates_model_instances_and_rejects_duplicate_response_members():
    request = make_request()
    response = decide_governance(request)
    # model_copy can bypass Pydantic validation; the boundary must not trust it.
    malformed = response.model_copy(update={"decision": {"scores": {"farming": True}}})
    with pytest.raises(GovernanceContractError) as error:
        verify_governance_response(request, malformed)
    assert error.value.problem.code == "invalid_response"
    with pytest.raises(GovernanceContractError, match="Duplicate JSON member"):
        verify_governance_response(request, '{"status":"ok","status":"error"}')


def test_cli_round_trip_and_failed_verification(tmp_path):
    request = tmp_path / "request.json"
    response = tmp_path / "response.json"
    request.write_text(make_request().model_dump_json(), encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["govern", "--request", str(request), "--output", str(response)])
    assert result.exit_code == 0 and "Python reference" in result.output
    command = ["check-governance", "--request", str(request), "--response", str(response)]
    assert runner.invoke(app, command).exit_code == 0
    data = json.loads(response.read_text(encoding="utf-8"))
    data["decision"]["voted_policy"] = "exploration"
    response.write_text(json.dumps(data), encoding="utf-8")
    assert runner.invoke(app, command).exit_code == 1
    assert runner.invoke(app, ["govern", "--request", str(request), "--output", str(request)]).exit_code == 2


def test_cli_invalid_request_writes_an_error_envelope_and_exits_unsuccessfully(tmp_path):
    request, response = tmp_path / "request.json", tmp_path / "error.json"
    request.write_text('{"schema_version":"future-version"}', encoding="utf-8")
    result = CliRunner().invoke(app, ["govern", "--request", str(request), "--output", str(response)])
    assert result.exit_code == 1
    assert json.loads(response.read_text(encoding="utf-8"))["status"] == "error"


def test_published_schemas_and_example_are_current_and_verifiable():
    folder = ROOT / "data/governance/v1"
    assert json.loads((folder / "request.schema.json").read_text(encoding="utf-8")) == GovernanceRequest.model_json_schema()
    assert json.loads((folder / "response.schema.json").read_text(encoding="utf-8")) == RESPONSE_ADAPTER.json_schema()
    request = parse_request((folder / "example_request.json").read_text(encoding="utf-8"))
    response = (folder / "example_response.json").read_text(encoding="utf-8")
    verify_governance_response(request, response)
    assert GovernanceSuccess.model_validate_json(response) == decide_governance(request)
    assert request.schema_version == CONTRACT_VERSION and request.policy_order == POLICY_ORDER
