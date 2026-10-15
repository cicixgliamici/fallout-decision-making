"""Read the community and its assumptions from a JSON scenario.

Keep inputs separate from mechanisms so comparisons can change one assumption at a time.

A scenario declares population, reserves, trust configuration, and parameters.
It contains no presentation profile: the same mechanical input can be described
using Vault or neutral vocabulary after the simulation has finished.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from pcds.models import CommunityState, Policy, Role, SimulationParameters


class AgentSpec(BaseModel):
    """A named member supplied by the scenario rather than generated at random."""

    name: str
    role: Role
    health: float = Field(default=0.8, ge=0.0, le=1.0)
    risk_aversion: float = Field(default=0.5, ge=0.0, le=1.0)
    cooperation: float = Field(default=0.5, ge=0.0, le=1.0)
    preferences: list[Policy] | None = None
    general_accuracy: float | None = Field(default=None, ge=0.0, le=1.0)
    expert_accuracy: float | None = Field(default=None, ge=0.0, le=1.0)


class TrustEdgeSpec(BaseModel):
    """One authored directed trust link; it supplements the generated network."""

    source: str
    target: str
    trust: float = Field(default=0.75, ge=0.0, le=1.0)


class Scenario(BaseModel):
    """The starting community and configurable assumptions for a trajectory.

    Some fields are reserved metadata; policies does not currently restrict the action space.
    """

    name: str
    description: str = ""
    # An integer requests a synthetic population; a list preserves authored
    # identities and attributes. The factory handles these two initialization paths.
    agents: int | list[AgentSpec] = 40
    resources: CommunityState = Field(default_factory=CommunityState)
    policies: list[Policy] = Field(default_factory=lambda: list(Policy))
    # Reserved/descriptive field: the voting and assessment code still considers
    # every Policy value. This list is not a policy-enablement switch.
    parameters: SimulationParameters = Field(default_factory=SimulationParameters)
    trust_topology: str = "expertise_clustered"
    trust_probability: float = Field(default=0.18, ge=0.0, le=1.0)
    trust_edges: list[TrustEdgeSpec] | None = None
    role_distribution: dict[Role, float] | None = None


def load_scenario(path: str | Path) -> Scenario:
    """Parse JSON and check the types and declared bounds of scenario fields.

    Additional requirements, such as unique member names, are checked when a run starts.
    """
    with Path(path).open("r", encoding="utf-8") as handle:
        data: dict[str, Any] = json.load(handle)
    return Scenario.model_validate(data)


def default_scenario_path() -> Path:
    """Locate Shelter Alpha relative to a source checkout, not the current directory."""
    return Path(__file__).resolve().parents[2] / "data" / "scenarios" / "shelter_alpha.json"
