"""Check the declared core permissions against real Prolog, without claiming a Prolog resolver."""

import math

import networkx as nx
import pytest

from pcds.governance_contract import snapshot_governance_request
from pcds.governance_reference import decide_governance, verify_governance_response
from pcds.models import Agent, CommunityState, Policy, Role
from pcds.prolog_rules import PrologRuleEngine

pytestmark = pytest.mark.prolog


def test_contract_core_eligibility_and_permissions_match_the_real_rule_file():
    engine = PrologRuleEngine(required=True)
    assert engine.info.backend == "swipl"
    agents = [Agent(name=name, role=Role.FARMER, preferences=list(Policy), **status)
              for name, status in (("living", {}), ("dead", {"alive": False}),
                                   ("sanctioned", {"sanctioned": True}))]
    graph = nx.DiGraph()
    for energy, security in ((2.0, 15.0), (math.nextafter(2.0, 0.0), 15.0),
                             (2.0, math.nextafter(15.0, 0.0)), (0.0, 0.0)):
        state = CommunityState(energy=energy, security=security)
        engine.sync_world(agents, graph, state)
        request = snapshot_governance_request("majority", agents, graph, state,
            decision_id=f"prolog-boundary:{energy}:{security}", institutional_checks=True)
        response = decide_governance(request)
        assert response.decision.eligible_voters == tuple(agent.name for agent in engine.filter_eligible(agents))
        for permission in response.certificate.permissions:
            assert permission.allowed == engine.allocation_allowed(permission.policy, state)
        verify_governance_response(request, response)
