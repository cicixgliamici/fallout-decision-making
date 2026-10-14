"""Audit replay, accounting floors, timing, and resident histories."""

import json

import pytest

from pcds.factory import create_agents_for_scenario
from pcds.events import SimulationEvent
from pcds.models import Policy, Role
from pcds.narrative import PROFILES, export_event_log, load_profile, render_report
from pcds.scenarios import AgentSpec, default_scenario_path, load_scenario
from pcds.simulation import run_simulation
from pcds.voting import VOTING_RULES


@pytest.mark.parametrize("rule", VOTING_RULES)
def test_recording_and_profiles_preserve_every_preexisting_result(rule):
    plain = run_simulation(rule, steps=40, seed=42)
    recorded = run_simulation(rule, steps=40, seed=42, record_events=True)
    assert [r.model_dump(exclude={"events"}) for r in plain] == [
        r.model_dump(exclude={"events"}) for r in recorded
    ]
    before = export_event_log(recorded)
    vault = render_report(recorded, PROFILES["vault47"])
    neutral = render_report(recorded, PROFILES["neutral"])
    assert vault != neutral
    assert vault == render_report(recorded, PROFILES["vault47"])
    assert before == export_event_log(recorded)
    replay = run_simulation(rule, steps=40, seed=42, record_events=True)
    assert before == export_event_log(replay)


def test_events_reconstruct_stocks_health_and_deaths():
    scenario = load_scenario(default_scenario_path())
    stocks = scenario.resources.as_dict()
    agents = create_agents_for_scenario(scenario, seed=42)
    health = {agent.name: agent.health for agent in agents}
    living = set(health)
    results = run_simulation(
        "liquid_democracy", steps=40, seed=42, scenario=scenario, record_events=True
    )
    for result in results:
        for sequence, event in enumerate(result.events):
            assert (event.step, event.sequence) == (result.step, sequence)
            if event.kind == "resource_change":
                assert event.before == stocks[event.subject]
                stocks[event.subject] = event.after
            elif event.kind in {"treatment", "injury", "health_damage"}:
                assert event.subject in living
                assert event.before == health[event.subject]
                health[event.subject] = event.after
                if event.kind == "health_damage":
                    assert -event.requested_change == pytest.approx(sum(event.details.values()))
            elif event.kind == "death":
                assert event.subject in living
                assert health[event.subject] <= event.details["threshold"]
                living.remove(event.subject)
        assert stocks == result.resources
        assert len(living) == result.survivors
        assert sum(health[name] for name in living) / len(health) == pytest.approx(
            result.population_health
        )


def _medical_scenario():
    scenario = load_scenario(default_scenario_path())
    policies = [Policy.MEDICINE, Policy.FARMING, Policy.DEFENSE, Policy.EXPLORATION]
    scenario.agents = [
        AgentSpec(name="alice", role=Role.DOCTOR, health=0.74, preferences=policies),
        AgentSpec(name="bob", role=Role.FARMER, health=0.20, preferences=policies),
    ]
    scenario.parameters.decision.mode = "fixed"
    scenario.parameters.random_health_damage_max = 0.0
    return scenario


def test_floors_treatment_and_extinction_do_not_invent_residents_or_losses():
    scenario = _medical_scenario()
    scenario.resources.energy = 2.0
    scenario.parameters.energy_replenishment = 0.0
    scenario.parameters.shock.probability = 1.0
    scenario.parameters.shock.health_damage = 1.0
    results = run_simulation("majority", steps=3, seed=42, scenario=scenario, record_events=True)
    first = results[0].events
    energy = next(e for e in first if e.kind == "resource_change" and e.subject == "energy")
    assert (energy.before, energy.after, energy.requested_change) == (2.0, 0.0, -2.0)
    assert {e.subject for e in first if e.kind == "treatment"} == {"alice", "bob"}
    assert {e.subject for e in first if e.kind == "death"} == {"alice", "bob"}
    for result in results[1:]:
        assert result.events[0].cause == "no_eligible_voters_recording_default"
        assert not any(
            e.kind in {"treatment", "injury", "death", "health_damage", "shortage"}
            for e in result.events
        )
    report = render_report(results, PROFILES["vault47"])
    assert "energy -2.000" in report
    assert "no eligible voters" in report and "Survivor health: N/A" in report
    assert report.count("Deaths: alice, bob") == 1
    assert report.index("Treatment:") < report.index("Consumption:")
    assert report.index("Consumption:") < report.index("External shock:")
    assert report.index("External shock:") < report.index("Environmental health loss")


def test_shock_stock_loss_causes_shortage_only_in_the_following_cycle():
    scenario = _medical_scenario()
    parameters = scenario.parameters
    for agent in scenario.agents:
        agent.health = 1.0
    scenario.resources.water = 2.0
    parameters.food_consumption = parameters.water_consumption = parameters.medicine_consumption = 0
    parameters.policy_impacts[Policy.MEDICINE].medicine_delta = 0
    parameters.policy_impacts[Policy.MEDICINE].health_boost = 0
    parameters.shock.probability = 1
    parameters.shock.food_loss = parameters.shock.medicine_loss = parameters.shock.security_loss = 0
    parameters.shock.water_loss = 2
    parameters.shock.health_damage = 0
    results = run_simulation("majority", steps=2, seed=42, scenario=scenario, record_events=True)
    assert not any(e.kind == "shortage" and e.subject == "water" for e in results[0].events)
    water = next(e for e in results[1].events if e.kind == "shortage" and e.subject == "water")
    assert water.details["health_damage"] == 0.06
    shock = next(e for e in results[1].events if e.kind == "shock")
    assert water.sequence < shock.sequence


def test_injuries_record_actual_floor_and_do_not_claim_an_expedition_crew():
    scenario = _medical_scenario()
    scenario.parameters.shock.probability = 0
    impact = scenario.parameters.policy_impacts[Policy.MEDICINE]
    impact.health_boost = 0
    impact.injury_probability = 1
    impact.injury_min = impact.injury_max = 0.4
    results = run_simulation("majority", steps=1, seed=42, scenario=scenario, record_events=True)
    injury = next(e for e in results[0].events if e.kind == "injury" and e.subject == "bob")
    assert (injury.before, injury.after, injury.requested_change) == (0.2, 0.0, -0.4)
    assert injury.cause == "medicine"
    assert not any(e.kind == "treatment" for e in results[0].events)


def test_custom_profile_changes_labels_without_changing_the_log(tmp_path):
    path = tmp_path / "lunar.json"
    profile = {
        "title": "LUNAR COLONY",
        "introduction": "Isolated lunar experiment.",
        "policy_labels": {"farming": "Greenhouse and water reclamation"},
    }
    path.write_text(json.dumps(profile), encoding="utf-8")
    scenario = load_scenario(default_scenario_path())
    scenario.parameters.decision.mode = "fixed"
    scenario.parameters.shock.probability = 0
    for impact in scenario.parameters.policy_impacts.values():
        impact.food_delta = 123.0
    results = run_simulation("majority", steps=1, seed=42, scenario=scenario, record_events=True)
    report = render_report(results, load_profile(str(path)))
    assert report.startswith("LUNAR COLONY")
    assert "food +123.000" in report
    assert "food +14.000" not in report


def test_missing_and_disordered_records_fail_clearly():
    with pytest.raises(ValueError, match="at least one"):
        render_report([])
    with pytest.raises(ValueError, match="record_events=True"):
        render_report(run_simulation("majority", steps=1, seed=42))
    recorded = run_simulation("majority", steps=2, seed=42, record_events=True)
    with pytest.raises(ValueError, match="consecutive"):
        export_event_log(list(reversed(recorded)))
    recorded[0].events.reverse()
    with pytest.raises(ValueError):
        export_event_log(recorded)


def test_incomplete_state_change_cannot_enter_the_typed_event_log():
    with pytest.raises(ValueError, match="before and after"):
        SimulationEvent(step=0, sequence=0, kind="injury", subject="alice", cause="exploration")


def test_institutional_override_preserves_both_requested_and_applied_policy(monkeypatch):
    class MedicalRestriction:
        # A controlled bridge isolates the recording boundary from optional SWI-Prolog.
        def sync_world(self, agents, graph, state):
            pass

        def filter_eligible(self, agents):
            return [agent for agent in agents if agent.alive and not agent.sanctioned]

        def allocation_allowed(self, policy, state):
            return policy != Policy.MEDICINE

    monkeypatch.setattr("pcds.simulation.PrologRuleEngine", MedicalRestriction)
    results = run_simulation(
        "majority",
        steps=1,
        seed=42,
        scenario=_medical_scenario(),
        use_prolog=True,
        record_events=True,
    )
    selection, override = [
        event for event in results[0].events
        if event.kind in {"policy_selected", "policy_override"}
    ]
    assert selection.subject == "medicine"
    assert override.kind == "policy_override" and override.subject == "farming"
    assert override.cause == "medicine"
    assert results[0].selected_policy == Policy.FARMING
    assert "Institutional override: medicine -> farming" in render_report(results)
