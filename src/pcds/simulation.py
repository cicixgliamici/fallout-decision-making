"""Coordinate repeated choices, physical consequences, and measurements.

Decision-time representation and end-of-round health have different populations.

run_simulation owns a trajectory's mutable agents and shared stocks. Helpers
apply individual physical mechanisms; each RoundResult captures an observation.
compare_rules repeats complete trajectories and exports their final outcomes.
Neither function selects narrative vocabulary or writes presentation artifacts.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

import networkx as nx
import polars as pl

from pcds.assessment import update_preferences
from pcds.events import EventRecorder
from pcds.factory import create_agents_for_scenario, create_trust_graph_for_scenario
from pcds.governance_contract import snapshot_governance_request
from pcds.governance_prolog import decide_prolog
from pcds.metric_definitions import METRIC_SCHEMA, NULLABLE_METRICS
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
from pcds.models import (
    PHYSICS_SCHEMA, Agent, CommunityState, GovernanceBackend, Policy, RoundResult,
    SimulationParameters,
)
from pcds.prolog_rules import PrologRuleEngine
from pcds.randomness import RANDOMNESS_SCHEME, EnvironmentalDraws, event_rng, sample_environment
from pcds.scenarios import Scenario, default_scenario_path, load_scenario
from pcds.voting import (
    VOTING_RULES,
    VotingOutcome,
    voting_outcome,
)


def run_simulation(
    rule: str,
    steps: int = 25,
    n_agents: int | None = None,
    seed: int | None = None,
    use_prolog: bool = False,
    scenario: Scenario | str | Path | None = None,
    record_events: bool = False,
    require_prolog: bool = False,
    governance_resolver: str = "auto",
) -> list[RoundResult]:
    """Run one mechanism over a fixed number of rounds and retain its full trajectory.

    A seed identifies the initial population and separate random events. An explicit
    population override applies only to generated members. Representation is measured
    before effects; survival and material wellbeing are measured afterward.
    """
    if governance_resolver not in {"auto", "python_reference"}:
        raise ValueError("governance_resolver must be auto or python_reference")
    if steps <= 0:
        raise ValueError("steps must be greater than zero")
    if n_agents is not None and n_agents <= 0:
        raise ValueError("n_agents must be greater than zero")

    # Even an exploratory run gets a recorded root seed so it can be replayed.
    run_seed = seed if seed is not None else random.SystemRandom().getrandbits(64)
    scenario_obj = _resolve_scenario(scenario, n_agents=n_agents)
    agents = create_agents_for_scenario(scenario_obj, seed=run_seed)
    if not agents:
        raise ValueError("scenario must contain at least one agent")
    # Names identify both private draws and original ballots; collisions would
    # silently merge voting power and invalidate its denominator.
    if len({agent.name for agent in agents}) != len(agents):
        raise ValueError("agent names must be unique")
    trust_graph = create_trust_graph_for_scenario(scenario_obj, agents, seed=run_seed)
    state = scenario_obj.resources.model_copy(deep=True)
    parameters = scenario_obj.parameters
    priors = {agent.name: tuple(agent.preferences) for agent in agents}
    # Keep the original rankings separately: current rankings change each round.
    # Required mode implies enabled checks and must never silently substitute Python.
    prolog = PrologRuleEngine(required=require_prolog) if use_prolog or require_prolog else None
    governance = prolog.info if prolog else GovernanceBackend()

    # Keep every original member in agents, including deaths: names anchor random
    # events, and the original population remains the survival denominator.
    results: list[RoundResult] = []

    for step in range(steps):
        # Stage 1: prepare outside exposure and the stocks visible to voters.
        # Sampling exposure now does not apply its damage before the election.
        recorder = EventRecorder(step) if record_events else None
        # A round separates outside conditions, the decision, and its effects.
        environment = sample_environment(run_seed, step, agents, parameters)
        _replenish_energy(agents, state, parameters, recorder)
        # Stage 2: private assessments become rankings, then the rule aggregates
        # ballots. Eligibility governs participation, not access to shared supplies.
        preference_changes, assessment_error = update_preferences(
            agents, state, parameters, priors, run_seed, step
        )
        # Prolog is optional: when enabled, it receives the current Python world
        # before eligibility and policy-admissibility checks are evaluated.
        native_decision = None
        if prolog and getattr(prolog, "available", False) and governance_resolver == "auto":
            # Prolog owns eligibility, paths, tally and permission. The checker
            # rejects a bad witness before any physical policy effect is applied.
            request = snapshot_governance_request(rule, agents, trust_graph, state,
                decision_id=f"{run_seed}:{step}", institutional_checks=True)
            native_decision = decide_prolog(request, prolog).decision
            by_name = {agent.name: agent for agent in agents}
            eligible_agents = [by_name[name] for name in native_decision.eligible_voters]
            outcome = VotingOutcome(native_decision.voted_policy, native_decision.representatives)
            governance = prolog.info
        else:
            # Keep the old implementation selectable under identical institutional
            # checks so migration comparisons do not conflate two treatments.
            if prolog:
                prolog.sync_world(agents, trust_graph, state)
            eligible_agents = prolog.filter_eligible(agents) if prolog else _eligible_agents(agents)
            outcome = _select_policy(rule, eligible_agents, trust_graph)
        selected = outcome.policy
        if recorder:
            recorder.record(
                "policy_selected",
                selected.value,
                "vote" if eligible_agents else "no_eligible_voters_recording_default",
                details={"eligible_voters": float(len(eligible_agents))},
            )
        if native_decision is not None:
            selected = native_decision.selected_policy
            if recorder and native_decision.permission_override:
                recorder.record("policy_override", selected.value, outcome.policy.value)
        elif prolog and not prolog.allocation_allowed(selected, state):
            selected = _first_allowed_policy(prolog, state)
            if recorder:
                recorder.record("policy_override", selected.value, outcome.policy.value)
        # Satisfaction and ballot ownership describe the decision-time
        # electorate, before effects can kill a voter or change their health.
        satisfaction = preference_satisfaction(eligible_agents, selected)
        prior_satisfaction = preference_satisfaction(eligible_agents, selected, priors)
        power = delegation_power(outcome.representatives)
        # Stage 3: institutional permission and physical affordability are separate.
        # A selected but unaffordable action stays recorded and produces no effects;
        # environmental consumption and damage still proceed during that round.
        block_reason = _apply_policy(selected, agents, state, run_seed, step, parameters, recorder)
        shock_occurred = _apply_environmental_pressure(
            agents, state, environment, parameters, recorder
        )

        # Stage 4: snapshot values rather than retain the mutable world objects.
        # The fixed horizon includes post-extinction rounds for aligned comparisons.
        results.append(
            RoundResult(
                step=step,
                rule=rule,
                governance=governance,
                selected_policy=selected,
                policy_executed=block_reason is None,
                policy_block_reason=block_reason,
                survival_rate=survival_rate(agents),
                **_material_metrics(agents, state, parameters),
                inequality=health_inequality(agents),
                resources=state.as_dict(),
                shock_occurred=shock_occurred,
                preference_changes=preference_changes,
                mean_assessment_error=assessment_error,
                simulation_seed=run_seed,
                environmental_shock_draw=environment.shock_draw,
                environmental_health_damage=environment.health_damage,
                eligible_voters=len(eligible_agents),
                preference_satisfaction=satisfaction,
                prior_preference_satisfaction=prior_satisfaction,
                vote_representatives=outcome.representatives,
                vote_weights=dict(Counter(outcome.representatives.values())),
                events=recorder.events if recorder else [],
                **power,
            )
        )

    return results


def compare_rules(
    rules: list[str] | None = None,
    runs: int = 20,
    steps: int = 30,
    n_agents: int | None = None,
    seed: int = 42,
    scenario: Scenario | str | Path | None = None,
    use_prolog: bool = False,
    require_prolog: bool = False,
    governance_resolver: str = "auto",
) -> pl.DataFrame:
    """Repeat each rule on the same seed schedule and export final outcomes.

    One row is one rule/seed trajectory, not one member or one round. Paired statistical
    inference is performed separately by the experiment/CLI pipeline.
    """
    if runs <= 0:
        raise ValueError("runs must be greater than zero")

    rules = rules or list(VOTING_RULES)
    rows: list[dict] = []

    for rule in rules:
        for run_id in range(runs):
            # Every rule receives this same trial identity, not a new population.
            run_seed = seed + run_id
            results = run_simulation(
                rule=rule,
                steps=steps,
                n_agents=n_agents,
                seed=run_seed,
                scenario=scenario,
                use_prolog=use_prolog,
                require_prolog=require_prolog,
                governance_resolver=governance_resolver,
            )
            # A trial contributes one final observation to inference. Its rounds
            # are dependent observations, not additional independent replications.
            last = results[-1]
            rows.append(
                {
                    "rule": rule,
                    "run_id": run_id,
                    "seed": run_seed,
                    "initial_population": last.initial_population,
                    "final_survival_rate": last.survival_rate,
                    "final_welfare": last.welfare,
                    "final_inequality": last.inequality,
                    "final_resilience": last.resilience,
                    "final_survivors": last.survivors,
                    "final_survivor_health": last.survivor_health,
                    "final_population_health": last.population_health,
                    "final_eligible_voters": last.eligible_voters,
                    "final_preference_satisfaction": last.preference_satisfaction,
                    "final_prior_preference_satisfaction": last.prior_preference_satisfaction,
                    "final_delegation_concentration": last.delegation_concentration,
                    "final_max_vote_share": last.max_vote_share,
                    "final_delegated_vote_share": last.delegated_vote_share,
                    **{
                        f"final_welfare_{name}": value
                        for name, value in last.welfare_sensitivity.items()
                    },
                    **{
                        f"final_welfare_component_{name}": value
                        for name, value in last.welfare_components.items()
                    },
                    "final_food": last.resources["food"],
                    "final_water": last.resources["water"],
                    "final_medicine": last.resources["medicine"],
                    "final_energy": last.resources["energy"],
                    "final_security": last.resources["security"],
                    "final_assessment_error": last.mean_assessment_error,
                    "total_preference_changes": sum(
                        result.preference_changes for result in results
                    ),
                    "shock_count": sum(result.shock_occurred for result in results),
                    "environment_trace_digest": _environment_trace_digest(results),
                    "randomness_scheme": RANDOMNESS_SCHEME,
                    "metric_schema": METRIC_SCHEMA,
                    "physics_schema": PHYSICS_SCHEMA,
                    **{f"governance_{key}": value
                       for key, value in last.governance.model_dump().items()},
                    # Extinct-colony placeholders are inactive observations,
                    # not failed attempts to pay for a policy.
                    "blocked_policy_count": sum(
                        (result.policy_block_reason or "").startswith("insufficient_")
                        for result in results
                    ),
                    "inactive_cycle_count": sum(
                        result.policy_block_reason == "no_living_residents" for result in results
                    ),
                }
            )

    # Entire conditions can lose their electorate. Preserve numeric nullable
    # types so these conditions can still be concatenated with surviving ones.
    return pl.DataFrame(rows, schema_overrides={
        **{metric: pl.Float64 for metric in NULLABLE_METRICS},
        **{f"governance_{key}": pl.String for key in GovernanceBackend.model_fields},
    })


def _select_policy(rule: str, agents: list[Agent], trust_graph: nx.DiGraph) -> VotingOutcome:
    """Dispatch to a decision rule while preserving its actual ballot-control trace."""
    return voting_outcome(rule, agents, trust_graph)


def _material_metrics(
    agents: list[Agent], state: CommunityState, parameters: SimulationParameters
) -> dict:
    """Measure end-of-round material outcomes and score alternative welfare priorities.

    These reporting choices never alter the decisions or physical random draws.
    """
    metric_parameters = parameters.metrics
    reference = metric_parameters.resource_reference
    components = welfare_components(agents, state, metric_parameters.welfare_weights, reference)
    return {
        "welfare": sum(components.values()),
        "resilience": resource_resilience(state, reference),
        "survivors": sum(agent.alive for agent in agents),
        "initial_population": len(agents),
        "survivor_health": survivor_health(agents),
        "population_health": population_health(agents),
        "welfare_components": components,
        "welfare_sensitivity": {
            name: social_welfare(agents, state, weights, reference)
            for name, weights in WELFARE_PROFILES.items()
        },
    }


def _environment_trace_digest(results: list[RoundResult]) -> str:
    # The digest audits external draws, not endogenous health/resources.
    """Fingerprint only the external draw schedule so paired runs can be checked.

    Different resulting health or stocks are expected and are not included in this check.
    """
    trace = [
        [
            result.step,
            result.environmental_shock_draw,
            result.shock_occurred,
            result.environmental_health_damage,
        ]
        for result in results
    ]
    encoded = json.dumps(trace, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _apply_policy(
    policy: Policy,
    agents: list[Agent],
    state: CommunityState,
    seed: int,
    step: int,
    parameters: SimulationParameters,
    recorder: EventRecorder | None = None,
) -> str | None:
    """Apply the scenario's community-wide stock changes and individual health effects.

    This is the physical model, separate from what members believed before choosing.
    """
    reason = _policy_block_reason(policy, agents, state, parameters)
    if reason:
        if recorder:
            recorder.record("policy_blocked", policy.value, reason)
        return reason
    impact = parameters.policy_impacts[policy]

    # Policy impacts update shared resources first; individual health effects
    # are applied afterward so the same decision can affect both the shelter and
    # its members.
    _change_resource(state, "energy", -impact.energy_cost, policy.value, recorder)
    for resource in ("food", "water", "medicine"):
        delta = getattr(impact, f"{resource}_delta")
        rng = event_rng(seed, "policy_resource", step, policy.value, resource)
        _change_resource(
            state, resource, _stochastic_gain(delta, rng, policy), policy.value, recorder
        )
    _change_resource(state, "security", impact.security_delta, policy.value, recorder)

    _apply_treatment(policy, agents, state, seed, step, parameters, recorder)
    _apply_injuries(policy, agents, seed, step, parameters, recorder)
    return None


def _replenish_energy(
    agents: list[Agent],
    state: CommunityState,
    parameters: SimulationParameters,
    recorder: EventRecorder | None = None,
) -> None:
    """Generate routine power before assessment, only while the colony is inhabited."""
    if not any(agent.alive for agent in agents):
        return
    headroom = max(0.0, parameters.energy_capacity - state.energy)
    gain = min(parameters.energy_replenishment, headroom)
    _change_resource(state, "energy", gain, "energy_replenishment", recorder)


def _policy_block_reason(
    policy: Policy,
    agents: list[Agent],
    state: CommunityState,
    parameters: SimulationParameters,
) -> str | None:
    """Require all inputs up front: a policy cannot finance its own operating costs."""
    if not any(agent.alive for agent in agents):
        return "no_living_residents"
    for resource, cost in parameters.policy_impacts[policy].required_inputs().items():
        if getattr(state, resource) < cost:
            return f"insufficient_{resource}"
    return None


def _change_resource(
    state: CommunityState,
    resource: str,
    change: float,
    cause: str,
    recorder: EventRecorder | None,
) -> None:
    """Retain intended and actual changes so depleted stocks are not overreported."""
    before = getattr(state, resource)
    after = max(0.0, before + change)
    setattr(state, resource, after)
    if recorder and change != 0.0:
        recorder.record("resource_change", resource, cause, before, after, change)


def _apply_treatment(
    policy: Policy,
    agents: list[Agent],
    state: CommunityState,
    seed: int,
    step: int,
    parameters: SimulationParameters,
    recorder: EventRecorder | None,
) -> None:
    """Share a limited medicine budget proportionally across capped health requests."""
    impact = parameters.policy_impacts[policy]
    if impact.health_boost <= 0 or state.medicine <= 0:
        return
    requests = []
    # Sorting plus fsum makes rationing independent of authored population order.
    for agent in sorted(agents, key=lambda member: member.name):
        if agent.alive and agent.health < 0.75:
            rng = event_rng(seed, "policy_healing", step, policy.value, agent.name)
            boost = rng.uniform(impact.health_boost * 0.5, impact.health_boost * 1.5)
            requests.append((agent, min(1.0 - agent.health, boost)))
    requested_health = math.fsum(boost for _, boost in requests)
    if not requested_health:
        return
    unit_cost = parameters.treatment_medicine_per_health
    # Example: enough medicine for half the total requested recovery gives every
    # patient half their request, rather than favoring the first name in the list.
    coverage = min(1.0, state.medicine / unit_cost / requested_health)
    # Debit only actual capped recovery; unused supply stays available for routine use.
    healed = []
    for agent, requested in requests:
        before = agent.health
        agent.health = min(1.0, before + requested * coverage)
        healed.append((agent, before, requested))
    medicine_used = min(
        state.medicine,
        math.fsum(agent.health - before for agent, before, _ in healed) * unit_cost,
    )
    _change_resource(state, "medicine", -medicine_used, "treatment", recorder)
    if recorder:
        for agent, before, requested in healed:
            recorder.record(
                "treatment", agent.name, policy.value, before, agent.health, requested,
                details={"coverage": coverage},
            )


def _apply_injuries(
    policy: Policy,
    agents: list[Agent],
    seed: int,
    step: int,
    parameters: SimulationParameters,
    recorder: EventRecorder | None,
) -> None:
    """Use the existing draw exactly once, then observe its effect."""
    impact = parameters.policy_impacts[policy]

    for agent in agents:
        # Per-agent policy draws preserve the same potential outcome when
        # another member dies or receives treatment in only one trajectory.
        if not agent.alive or impact.injury_probability == 0.0:
            continue
        rng = event_rng(seed, "policy_injury", step, policy.value, agent.name)
        if rng.random() < impact.injury_probability:
            injury = rng.uniform(impact.injury_min, impact.injury_max)
            before = agent.health
            agent.health = max(0.0, agent.health - injury)
            if recorder:
                recorder.record("injury", agent.name, policy.value, before, agent.health, -injury)


def _apply_environmental_pressure(
    agents: list[Agent],
    state: CommunityState,
    environment: EnvironmentalDraws,
    parameters: SimulationParameters,
    recorder: EventRecorder | None = None,
) -> bool:
    """Consume supplies, calculate scarcity, apply shocks, and update survival.

    Scarcity is calculated before shock stock losses; direct shock health damage is
    applied now, while additional shortage consequences can appear next round.
    """
    alive_agents = [a for a in agents if a.alive]
    population = len(alive_agents)

    # Scarcity pressure is intentionally simple: resources are consumed by the
    # surviving population, then shortages translate into health damage.
    for resource in ("food", "water", "medicine"):
        consumption = getattr(parameters, f"{resource}_consumption") * population
        _change_resource(state, resource, -consumption, "consumption", recorder)

    scarcity = _scarcity_pressure(state, population, parameters, recorder)
    shortage_damage = scarcity

    shock_occurred = environment.shock_draw < parameters.shock.probability
    # Shock losses do not trigger a second scarcity calculation in this round.
    if shock_occurred:
        if recorder:
            recorder.record(
                "shock",
                "community",
                "external_shock",
                details={"health_damage": parameters.shock.health_damage},
            )
        for resource in ("food", "water", "medicine", "security"):
            loss = getattr(parameters.shock, f"{resource}_loss")
            _change_resource(state, resource, -loss, "external_shock", recorder)
        scarcity += parameters.shock.health_damage

    _damage_residents(
        alive_agents,
        environment,
        parameters,
        scarcity,
        shortage_damage,
        shock_occurred,
        recorder,
    )
    return shock_occurred


def _scarcity_pressure(
    state: CommunityState,
    population: int,
    parameters: SimulationParameters,
    recorder: EventRecorder | None,
) -> float:
    """Check shortages before shock losses, preserving the existing update order."""
    scarcity = 0.0
    for resource in ("food", "water", "medicine", "security"):
        threshold = (
            parameters.low_security_threshold
            if resource == "security"
            else population * getattr(parameters, f"scarcity_{resource}_threshold")
        )
        stock = getattr(state, resource)
        insufficient = stock < threshold if resource == "security" else stock <= threshold
        if not insufficient:
            continue
        damage = (
            parameters.low_security_damage
            if resource == "security"
            else getattr(parameters, f"scarcity_{resource}_damage")
        )
        scarcity += damage
        # Extinct communities have no exposed residents, even when a zero stock
        # satisfies the numerical threshold comparison retained by the engine.
        if recorder and population:
            recorder.record(
                "shortage",
                resource,
                "post_consumption_threshold",
                before=stock,
                after=stock,
                details={"threshold": threshold, "health_damage": damage},
            )
    return scarcity


def _damage_residents(
    alive_agents: list[Agent],
    environment: EnvironmentalDraws,
    parameters: SimulationParameters,
    scarcity: float,
    shortage_damage: float,
    shock_occurred: bool,
    recorder: EventRecorder | None,
) -> None:
    """Record damage components and threshold deaths, without attributing a sole cause."""
    for agent in alive_agents:
        damage = scarcity + environment.health_damage[agent.name]
        before = agent.health
        agent.health = max(0.0, agent.health - damage)
        if recorder and damage != 0.0:
            recorder.record(
                "health_damage",
                agent.name,
                "environmental_pressure",
                before,
                agent.health,
                -damage,
                details={
                    "shortage": shortage_damage,
                    "shock": parameters.shock.health_damage if shock_occurred else 0.0,
                    "background": environment.health_damage[agent.name],
                },
            )
        # Death status is finalized here, after policy and environmental damage.
        # Health may remain positive at this numerical threshold; later population
        # metrics explicitly assign zero to members whose alive flag is False.
        if agent.health <= parameters.death_threshold:
            agent.alive = False
            if recorder:
                recorder.record(
                    "death",
                    agent.name,
                    "health_at_or_below_death_threshold",
                    1.0,
                    0.0,
                    details={"health": agent.health, "threshold": parameters.death_threshold},
                )


def _eligible_agents(agents: list[Agent]) -> list[Agent]:
    """Select the living, unsanctioned decision-time electorate."""
    return [a for a in agents if a.alive and not a.sanctioned]


def _first_allowed_policy(prolog: PrologRuleEngine, state: CommunityState) -> Policy:
    """Use the first institutionally allowed policy as a simple replacement.

    This fallback is not a search for the policy with the best expected outcome.
    """
    for policy in Policy:
        if prolog.allocation_allowed(policy, state):
            return policy
    return Policy.FARMING


def _resolve_scenario(scenario: Scenario | str | Path | None, n_agents: int | None) -> Scenario:
    """Copy or load scenario inputs so overrides do not mutate the caller's scenario."""
    if isinstance(scenario, Scenario):
        scenario_obj = scenario.model_copy(deep=True)
    else:
        scenario_obj = load_scenario(default_scenario_path() if scenario is None else scenario)
    if n_agents is not None:
        # An explicit override controls synthetic populations; named agents
        # cannot be resized without changing their authored identities/links.
        if not isinstance(scenario_obj.agents, int):
            raise ValueError("n_agents cannot override an explicit agent list")
        scenario_obj.agents = n_agents
    return scenario_obj


def _stochastic_gain(delta: float, rng: random.Random, policy: Policy) -> float:
    """Give exploration a variable positive stock gain; other deltas are deterministic."""
    if policy == Policy.EXPLORATION and delta > 0:
        return rng.uniform(0.0, delta * 2.0)
    return delta
