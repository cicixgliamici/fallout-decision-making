"""Give each random event a reproducible identity.

A policy choice or death must not change the next external event faced by another rule.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass

from pcds.models import Agent, SimulationParameters

RANDOMNESS_SCHEME = "event-keyed-v1"


def event_rng(seed: int, domain: str, step: int, *identifiers: str) -> random.Random:
    # Structured keys avoid ambiguous names and Python's process-randomized hash.
    """Create the random generator for one named event, without advancing other events.

    The same seed and event identity reproduce the same draws.
    """
    key = json.dumps([domain, seed, step, *identifiers], separators=(",", ":"))
    return random.Random(key)


@dataclass(frozen=True)
class EnvironmentalDraws:
    """Potential external exposure for this round, including members who already died."""

    shock_draw: float
    health_damage: dict[str, float]


def sample_environment(
    seed: int, step: int, agents: list[Agent], parameters: SimulationParameters
) -> EnvironmentalDraws:
    # Sample potential exposure for every original member, even after death.
    # Survivor counts and iteration order must not shift other members' draws.
    """Generate the shared shock draw and a separate health draw per original member.

    Only living members receive damage later; retaining all identities prevents drift.
    """
    return EnvironmentalDraws(
        shock_draw=event_rng(seed, "environment_shock", step).random(),
        health_damage={
            agent.name: event_rng(seed, "environment_health", step, agent.name).uniform(
                0.0, parameters.random_health_damage_max
            )
            for agent in agents
        },
    )
