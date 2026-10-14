"""Verify physical budgets, fair rationing, and observable failed actions."""

import random

import polars as pl
import pytest
from pydantic import ValidationError

from pcds.assessment import assess_policy, assessment_context
from pcds.events import EventRecorder
from pcds.models import Agent, CommunityState, Policy, Role, SimulationParameters
from pcds.narrative import render_report
from pcds.scenarios import AgentSpec, default_scenario_path, load_scenario
from pcds.simulation import _apply_policy, _replenish_energy, compare_rules, run_simulation


def patient(name="patient", health=0.4, **overrides):
    return Agent(name=name, health=health, role=Role.DOCTOR, preferences=list(Policy), **overrides)


@pytest.mark.parametrize("stock,expected", [(0, 2), (49, 50), (50, 50), (60, 60)])
def test_power_is_bounded_without_destroying_initial_reserves(stock, expected):
    state = CommunityState(energy=stock)
    _replenish_energy([patient()], state, SimulationParameters())
    assert state.energy == expected


def test_empty_colony_neither_generates_power_nor_executes_a_recording_default():
    agents = [patient(alive=False)]
    state = CommunityState(energy=1)
    before = state.model_copy()
    parameters = SimulationParameters()
    _replenish_energy(agents, state, parameters)
    assert _apply_policy(Policy.FARMING, agents, state, 42, 0, parameters) == "no_living_residents"
    assert state == before


@pytest.mark.parametrize("policy", list(Policy))
def test_energy_gate_is_atomic_for_every_policy(policy):
    agents = [patient()]
    state = CommunityState(energy=0)
    before = state.model_dump(), agents[0].model_dump()
    recorder = EventRecorder(0)
    assert _apply_policy(policy, agents, state, 42, 0, SimulationParameters(), recorder) == (
        "insufficient_energy"
    )
    assert before == (state.model_dump(), agents[0].model_dump())
    assert [event.kind for event in recorder.events] == ["policy_blocked"]


@pytest.mark.parametrize("resource", ["food", "water", "medicine", "security"])
def test_negative_policy_deltas_require_available_inputs(resource):
    parameters = SimulationParameters()
    impact = parameters.policy_impacts[Policy.MEDICINE]
    setattr(impact, f"{resource}_delta", -3.0)
    state = CommunityState(**{resource: 2.0})
    before = state.model_dump()
    assert _apply_policy(Policy.MEDICINE, [patient()], state, 42, 0, parameters) == (
        f"insufficient_{resource}"
    )
    assert state.model_dump() == before


def test_exact_inputs_are_paid_and_positive_output_cannot_fund_upfront_costs():
    parameters = SimulationParameters()
    impact = parameters.policy_impacts[Policy.MEDICINE]
    impact.energy_cost = 2
    impact.water_delta = -3
    state = CommunityState(energy=2, water=3)
    assert _apply_policy(Policy.MEDICINE, [patient()], state, 42, 0, parameters) is None
    assert state.energy == state.water == 0


@pytest.mark.parametrize("medicine", [0.0, 0.01, 0.15, 20.0])
def test_treatment_spends_only_actual_health_recovery_and_is_order_independent(medicine):
    parameters = SimulationParameters(treatment_medicine_per_health=2)
    impact = parameters.policy_impacts[Policy.MEDICINE]
    impact.medicine_delta = 0
    impact.health_boost = 2.0  # Deliberately exercise health caps before rationing.
    agents = [patient("alice"), patient("bob", 0.2), patient("healthy", 0.75)]
    reverse = [agent.model_copy(deep=True) for agent in reversed(agents)]
    state = CommunityState(medicine=medicine)
    other_state = state.model_copy()
    before = {agent.name: agent.health for agent in agents}
    recorder = EventRecorder(0)
    _apply_policy(Policy.MEDICINE, agents, state, 42, 0, parameters, recorder)
    _apply_policy(Policy.MEDICINE, reverse, other_state, 42, 0, parameters)
    recovered = sum(agent.health - before[agent.name] for agent in agents)
    assert medicine - state.medicine == pytest.approx(recovered * 2)
    assert 0 <= state.medicine <= medicine
    assert state == other_state
    assert {a.name: a.health for a in agents} == {a.name: a.health for a in reverse}
    assert agents[2].health == 0.75
    treatments = [event for event in recorder.events if event.kind == "treatment"]
    if medicine:
        assert len(treatments) == 2
        fractions = [(e.after - e.before) / e.requested_change for e in treatments]
        assert fractions[0] == pytest.approx(fractions[1])
    else:
        assert not treatments


def test_same_cycle_production_can_supply_treatment_but_not_operating_energy():
    parameters = SimulationParameters()
    agent = patient()
    state = CommunityState(medicine=0, energy=2)
    _apply_policy(Policy.MEDICINE, [agent], state, 42, 0, parameters)
    assert agent.health > 0.4
    assert 0 < state.medicine < 8


def test_extinct_recording_cycles_are_distinct_from_unaffordable_actions():
    scenario = load_scenario(default_scenario_path())
    scenario.parameters.shock.probability = 1
    scenario.parameters.shock.health_damage = 1
    raw = compare_rules(rules=["majority"], runs=1, steps=4, seed=42, scenario=scenario)
    assert raw["blocked_policy_count"].to_list() == [0]
    assert raw["inactive_cycle_count"].to_list() == [3]


def test_dead_and_healthy_patients_do_not_consume_treatment_stock():
    parameters = SimulationParameters()
    parameters.policy_impacts[Policy.MEDICINE].medicine_delta = 0
    state = CommunityState(medicine=3)
    agents = [patient(alive=False), patient("healthy", 0.75)]
    _apply_policy(Policy.MEDICINE, agents, state, 42, 0, parameters)
    assert state.medicine == 3


def test_failed_vote_and_next_cycle_recovery_are_visible_end_to_end():
    scenario = load_scenario(default_scenario_path())
    scenario.agents = [AgentSpec(name="doctor", role=Role.DOCTOR, preferences=[
        Policy.MEDICINE, Policy.FARMING, Policy.DEFENSE, Policy.EXPLORATION,
    ])]
    scenario.resources.energy = 0
    scenario.parameters.energy_replenishment = 1
    scenario.parameters.decision.mode = "fixed"
    scenario.parameters.shock.probability = 0
    results = run_simulation("majority", steps=2, seed=42, scenario=scenario, record_events=True)
    assert [r.policy_executed for r in results] == [False, True]
    assert [r.selected_policy for r in results] == [Policy.MEDICINE] * 2
    assert [r.resources["energy"] for r in results] == [1, 0]
    assert results[0].policy_block_reason == "insufficient_energy"
    report = render_report(results)
    assert "Policy not executed: insufficient_energy" in report
    assert "Routine power: energy +1.000" in report
    assert results[0].preference_satisfaction == 1  # Congruence with the vote, not delivery.
    raw = compare_rules(rules=["majority"], runs=1, steps=2, seed=42, scenario=scenario)
    assert raw["blocked_policy_count"].to_list() == [1]
    assert raw["physics_schema"].to_list() == ["stock-budgeted-v2"]


def test_exact_assessment_accounts_for_input_and_treatment_budgets():
    agent = patient()
    parameters = SimulationParameters()
    parameters.policy_impacts[Policy.MEDICINE].medicine_delta = 0

    def score(medicine, energy=50):
        context = assessment_context([agent], CommunityState(medicine=medicine, energy=energy),
                                     parameters)
        return assess_policy(agent, Policy.MEDICINE, context, parameters,
                             tuple(agent.preferences), random.Random(42), perfect_information=True)

    assert score(20) > score(0)
    assert score(20, energy=0) < 0


@pytest.mark.parametrize("field,value", [
    ("energy_replenishment", -1), ("energy_capacity", -1),
    ("treatment_medicine_per_health", 0), ("treatment_medicine_per_health", -1),
    ("energy_replenishment", float("inf")), ("energy_capacity", float("nan")),
])
def test_invalid_accounting_parameters_are_rejected(field, value):
    with pytest.raises(ValidationError):
        SimulationParameters(**{field: value})


def test_pairing_rejects_mixed_physics_even_with_matching_external_draws():
    from pcds.paired_analysis import build_paired_differences

    raw = compare_rules(rules=["majority", "approval"], runs=1, steps=1)
    mixed = raw.with_columns(
        pl.when(pl.col("rule") == "majority").then(pl.lit("old"))
        .otherwise(pl.col("physics_schema")).alias("physics_schema"),
        pl.lit("test").alias("experiment"),
    )
    with pytest.raises(ValueError, match="physics schemas"):
        build_paired_differences(mixed)
