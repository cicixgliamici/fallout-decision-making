from __future__ import annotations

from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field


class Role(str, Enum):
    DOCTOR = "doctor"
    FARMER = "farmer"
    ENGINEER = "engineer"
    GUARD = "guard"
    SCAVENGER = "scavenger"
    ELDER = "elder"


class Policy(str, Enum):
    FARMING = "farming"
    MEDICINE = "medicine"
    DEFENSE = "defense"
    EXPLORATION = "exploration"


EXPERTISE: dict[Role, Policy] = {
    Role.FARMER: Policy.FARMING,
    Role.DOCTOR: Policy.MEDICINE,
    Role.GUARD: Policy.DEFENSE,
    Role.SCAVENGER: Policy.EXPLORATION,
    Role.ENGINEER: Policy.DEFENSE,
    Role.ELDER: Policy.MEDICINE,
}


class Agent(BaseModel):
    """A member of the post-crisis community.

    The model is deliberately simple in MVP 0: each agent has a role, survival state,
    a preference ranking over policies, and behavioral parameters.
    """

    name: str
    role: Role
    alive: bool = True
    sanctioned: bool = False
    health: float = Field(default=1.0, ge=0.0, le=1.0)
    risk_aversion: float = Field(default=0.5, ge=0.0, le=1.0)
    cooperation: float = Field(default=0.5, ge=0.0, le=1.0)
    preferences: List[Policy]

    @property
    def expertise(self) -> Policy:
        return EXPERTISE[self.role]

    def top_choice(self) -> Policy:
        return self.preferences[0]

    def approves(self, policy: Policy, k: int = 2) -> bool:
        return policy in self.preferences[:k]


class CommunityState(BaseModel):
    food: float = Field(default=100.0, ge=0.0)
    water: float = Field(default=100.0, ge=0.0)
    medicine: float = Field(default=50.0, ge=0.0)
    energy: float = Field(default=50.0, ge=0.0)
    security: float = Field(default=50.0, ge=0.0)

    def as_dict(self) -> Dict[str, float]:
        return self.model_dump()


class RoundResult(BaseModel):
    step: int
    rule: str
    selected_policy: Policy
    survival_rate: float
    welfare: float
    inequality: float
    resources: Dict[str, float]
