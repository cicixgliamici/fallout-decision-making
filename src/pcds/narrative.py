"""Render recorded facts using replaceable labels, independently of the engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from pydantic import BaseModel, ConfigDict

from pcds.events import EVENT_SCHEMA, SimulationEvent
from pcds.metric_definitions import METRIC_SCHEMA
from pcds.models import Policy, RoundResult
from pcds.randomness import RANDOMNESS_SCHEME


class NarrativeProfile(BaseModel):
    """Presentation vocabulary; no physical parameters or random generators."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    title: str
    introduction: str
    policy_labels: dict[Policy, str]

    def label(self, policy: Policy) -> str:
        # Missing custom labels retain a truthful identifier rather than invent lore.
        return self.policy_labels.get(policy, policy.value)


PROFILES = {
    "neutral": NarrativeProfile(
        title="COLLECTIVE DECISION EXPERIMENT",
        introduction="Recorded decisions and consequences in abstract model units.",
        policy_labels={policy: policy.value for policy in Policy},
    ),
    "vault47": NarrativeProfile(
        title="OVERSEER RESEARCH TERMINAL / VAULT 47 / PROTOCOL 47-G",
        introduction=(
            "Isolated colony governance experiment. Continued habitation is an outcome "
            "to be recorded, not an assumption."
        ),
        policy_labels={
            Policy.FARMING: "Hydroponic production and water recovery",
            Policy.MEDICINE: "Infirmary support and medical supply preparation",
            Policy.DEFENSE: "Shelter security and access readiness",
            Policy.EXPLORATION: "Surface supply expedition",
        },
    ),
}


def load_profile(name_or_path: str) -> NarrativeProfile:
    """Use a built-in vocabulary or a standalone JSON presentation profile."""
    if name_or_path in PROFILES:
        return PROFILES[name_or_path]
    return NarrativeProfile.model_validate_json(Path(name_or_path).read_text(encoding="utf-8"))


def _validate_trace(results: Sequence[RoundResult]) -> None:
    """Reject unrecorded or mixed histories rather than fill gaps with fiction."""
    if not results:
        raise ValueError("a report requires at least one recorded round")
    first = results[0]
    identity = (first.rule, first.simulation_seed, first.initial_population, first.physics_schema)
    for index, result in enumerate(results):
        if (
            result.rule, result.simulation_seed, result.initial_population, result.physics_schema
        ) != identity:
            raise ValueError("rounds must belong to the same simulation")
        if index and result.step != results[index - 1].step + 1:
            raise ValueError("rounds must be consecutive and ordered")
        if not any(event.kind == "policy_selected" for event in result.events):
            raise ValueError("event records are required; use record_events=True")
        for sequence, event in enumerate(result.events):
            if event.step != result.step or event.sequence != sequence:
                raise ValueError("event order does not match its round")


def render_report(
    results: Sequence[RoundResult],
    profile: NarrativeProfile | None = None,
) -> str:
    """Produce identical text for identical records/profile, without mutating either."""
    _validate_trace(results)
    profile = profile or PROFILES["neutral"]
    first = results[0]
    lines = [
        profile.title,
        profile.introduction,
        f"Rule: {first.rule} | Seed: {first.simulation_seed}",
        f"Physics: {first.physics_schema}",
        "Cycles are decision allocations, not calendar days or work shifts.",
        "Resource amounts and health are abstract model units.",
        "",
    ]
    for result in results:
        lines.extend(_round_report(result, profile))
    return "\n".join(lines).rstrip() + "\n"


def _round_report(result: RoundResult, profile: NarrativeProfile) -> list[str]:
    """Keep decision-time representation separate from end-of-cycle outcomes."""
    events = result.events
    lines = [f"CYCLE {result.step + 1:04d} / simulation step {result.step}"]
    lines.extend(_resource_changes(events, "energy_replenishment", "Routine power"))
    if result.eligible_voters:
        lines.append(
            f"Priority: {profile.label(result.selected_policy)} [{result.selected_policy.value}]"
        )
    else:
        lines.append(f"Recording default: {result.selected_policy.value}; no eligible voters.")
    for event in events:
        if event.kind == "policy_override":
            lines.append(f"Institutional override: {event.cause} -> {event.subject}.")
    if not result.policy_executed:
        lines.append(f"Policy not executed: {result.policy_block_reason}.")
    lines.append(
        f"Eligible voters: {result.eligible_voters} | "
        f"Largest ballot share: {_optional(result.max_vote_share)} | "
        f"Preference satisfaction: {_optional(result.preference_satisfaction)}"
    )
    lines.extend(_resource_changes(events, result.selected_policy.value, "Policy effects"))
    lines.extend(_resource_changes(events, "treatment", "Treatment supplies"))
    lines.extend(_policy_health_report(events))
    lines.extend(_resource_changes(events, "consumption", "Consumption"))
    shortages = [event.subject for event in events if event.kind == "shortage"]
    lines.append("Post-consumption shortages: " + (", ".join(shortages) or "none") + ".")
    lines.append("External shock: " + ("recorded." if result.shock_occurred else "none."))
    lines.extend(_resource_changes(events, "external_shock", "Shock reserve losses"))
    lines.extend(_environment_health_report(events))
    lines.append(_reserve_report(result))
    lines.append(
        f"End population: {result.survivors}/{result.initial_population} | "
        f"Population health: {result.population_health:.3f} | "
        f"Survivor health: {_optional(result.survivor_health)}"
    )
    return [*lines, ""]


def _resource_changes(events: Sequence[SimulationEvent], cause: str, label: str) -> list[str]:
    """Use actual transactions, including floors, instead of baseline policy constants."""
    entries = [
        _transaction(event)
        for event in events
        if event.kind == "resource_change" and event.cause == cause
    ]
    return [label + ": " + "; ".join(entries) + "."] if entries else []


def _reserve_report(result: RoundResult) -> str:
    """Summarize the cycle endpoints after its chronological event summaries."""
    changes = [event for event in result.events if event.kind == "resource_change"]
    reserves = []
    for resource, final in result.resources.items():
        transactions = [event for event in changes if event.subject == resource]
        initial = transactions[0].before if transactions else final
        reserves.append(f"{resource} {initial:.3f} -> {final:.3f}")
    return "Reserves: " + "; ".join(reserves) + "."


def _transaction(event: SimulationEvent) -> str:
    actual = event.after - event.before
    text = f"{event.subject} {actual:+.3f}"
    # Floors and health caps mean a requested effect need not be fully realized.
    if event.requested_change is not None and abs(actual - event.requested_change) > 1e-9:
        text += f" (requested {event.requested_change:+.3f})"
    return text


def _policy_health_report(events: Sequence[SimulationEvent]) -> list[str]:
    """Describe treatment and injuries before subsequent environmental pressure."""
    lines = []
    for kind, label in (("treatment", "Treatment"), ("injury", "Policy injuries")):
        matches = [event for event in events if event.kind == kind]
        change = sum(event.after - event.before for event in matches)
        lines.append(f"{label}: {len(matches)} residents; total health change {change:+.3f}.")
    return lines


def _environment_health_report(events: Sequence[SimulationEvent]) -> list[str]:
    """Report actual environmental loss and threshold deaths after external shocks."""
    lines = []
    damage = [event for event in events if event.kind == "health_damage"]
    actual = sum(event.before - event.after for event in damage)
    lines.append(f"Environmental health loss, summed across residents: {actual:.3f}.")
    deaths = [event.subject for event in events if event.kind == "death"]
    lines.append(
        "Deaths: " + (", ".join(deaths) + " (health threshold reached)." if deaths else "none.")
    )
    return lines


def _optional(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.3f}"


def export_event_log(
    results: Sequence[RoundResult],
    scenario_configuration: dict | None = None,
    *,
    governance_checks_enabled: bool | None = None,
) -> str:
    """Export the complete neutral trace and ballots; timestamps would break replay."""
    _validate_trace(results)
    payload = {
        "event_schema": EVENT_SCHEMA,
        "randomness_scheme": RANDOMNESS_SCHEME,
        "metric_schema": METRIC_SCHEMA,
        "physics_schema": results[0].physics_schema,
        "rounds": [result.model_dump(mode="json") for result in results],
    }
    if scenario_configuration is not None:
        payload["scenario_configuration"] = scenario_configuration
    if governance_checks_enabled is not None:
        payload["governance_checks_enabled"] = governance_checks_enabled
    return json.dumps(payload, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
