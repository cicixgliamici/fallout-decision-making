from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from pcds.models import CommunityState, Policy, Role, SimulationParameters


class AgentSpec(BaseModel):
    name: str
    role: Role
    health: float = Field(default=0.8, ge=0.0, le=1.0)
    risk_aversion: float = Field(default=0.5, ge=0.0, le=1.0)
    cooperation: float = Field(default=0.5, ge=0.0, le=1.0)
    preferences: list[Policy] | None = None


class TrustEdgeSpec(BaseModel):
    source: str
    target: str
    trust: float = Field(default=0.75, ge=0.0, le=1.0)


class Scenario(BaseModel):
    name: str
    description: str = ""
    agents: int | list[AgentSpec] = 40
    resources: CommunityState = Field(default_factory=CommunityState)
    policies: list[Policy] = Field(default_factory=lambda: list(Policy))
    parameters: SimulationParameters = Field(default_factory=SimulationParameters)
    trust_topology: str = "expertise_clustered"
    trust_probability: float = Field(default=0.18, ge=0.0, le=1.0)
    trust_edges: list[TrustEdgeSpec] | None = None
    role_distribution: dict[Role, float] | None = None


def load_scenario(path: str | Path) -> Scenario:
    with Path(path).open("r", encoding="utf-8") as handle:
        data: dict[str, Any] = json.load(handle)
    return Scenario.model_validate(data)


def default_scenario_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "scenarios" / "shelter_alpha.json"
