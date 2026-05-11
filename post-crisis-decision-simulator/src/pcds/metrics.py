from __future__ import annotations

import numpy as np

from pcds.models import Agent, CommunityState


def survival_rate(agents: list[Agent]) -> float:
    if not agents:
        return 0.0
    return sum(1 for a in agents if a.alive) / len(agents)


def social_welfare(agents: list[Agent], state: CommunityState) -> float:
    """A small welfare proxy combining survival, health, and resource availability."""
    if not agents:
        return 0.0
    avg_health = sum(a.health for a in agents if a.alive) / max(1, sum(1 for a in agents if a.alive))
    resource_score = np.mean([
        state.food / 100.0,
        state.water / 100.0,
        state.medicine / 50.0,
        state.energy / 50.0,
        state.security / 50.0,
    ])
    return float(0.65 * survival_rate(agents) + 0.25 * avg_health + 0.10 * resource_score)


def health_inequality(agents: list[Agent]) -> float:
    healths = np.array([a.health for a in agents], dtype=float)
    if len(healths) == 0:
        return 0.0
    return float(np.std(healths))
