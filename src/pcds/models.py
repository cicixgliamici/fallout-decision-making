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
    utility_weights: Dict[Policy, float] = Field(default_factory=dict)

    @property
    def expertise(self) -> Policy:
        return EXPERTISE[self.role]

    def top_choice(self) -> Policy:
        return self.preferences[0]

    def approves(self, policy: Policy, k: int = 2) -> bool:
        return policy in self.preferences[:k]

    def utility_for(self, policy: Policy) -> float:
        if self.utility_weights:
            return self.utility_weights.get(policy, 0.0)
        ordinal_score = len(self.preferences) - self.preferences.index(policy)
        expertise_bonus = 0.5 if self.expertise == policy else 0.0
        risk_penalty = self.risk_aversion if policy == Policy.EXPLORATION else 0.0
        cooperation_bonus = self.cooperation if policy in {Policy.FARMING, Policy.MEDICINE} else 0.0
        return float(ordinal_score + expertise_bonus + cooperation_bonus - risk_penalty)


class CommunityState(BaseModel):
    food: float = Field(default=100.0, ge=0.0)
    water: float = Field(default=100.0, ge=0.0)
    medicine: float = Field(default=50.0, ge=0.0)
    energy: float = Field(default=50.0, ge=0.0)
    security: float = Field(default=50.0, ge=0.0)

    def as_dict(self) -> Dict[str, float]:
        return self.model_dump()


class PolicyImpact(BaseModel):
    """Resource and health effects of applying one policy for one round."""

    energy_cost: float = Field(default=2.0, ge=0.0)
    food_delta: float = 0.0
    water_delta: float = 0.0
    medicine_delta: float = 0.0
    security_delta: float = 0.0
    health_boost: float = Field(default=0.0, ge=0.0)
    injury_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    injury_min: float = Field(default=0.0, ge=0.0, le=1.0)
    injury_max: float = Field(default=0.0, ge=0.0, le=1.0)


class EnvironmentalShock(BaseModel):
    """Low-probability external event that consumes resources and harms health."""

    probability: float = Field(default=0.05, ge=0.0, le=1.0)
    food_loss: float = Field(default=0.0, ge=0.0)
    water_loss: float = Field(default=0.0, ge=0.0)
    medicine_loss: float = Field(default=0.0, ge=0.0)
    security_loss: float = Field(default=0.0, ge=0.0)
    health_damage: float = Field(default=0.0, ge=0.0, le=1.0)


class SimulationParameters(BaseModel):
    """Tunable dynamics for resource consumption, scarcity damage, and policies."""

    food_consumption: float = Field(default=0.8, ge=0.0)
    water_consumption: float = Field(default=0.7, ge=0.0)
    medicine_consumption: float = Field(default=0.08, ge=0.0)
    scarcity_food_threshold: float = Field(default=0.5, ge=0.0)
    scarcity_water_threshold: float = Field(default=0.5, ge=0.0)
    scarcity_medicine_threshold: float = Field(default=0.05, ge=0.0)
    scarcity_food_damage: float = Field(default=0.05, ge=0.0, le=1.0)
    scarcity_water_damage: float = Field(default=0.06, ge=0.0, le=1.0)
    scarcity_medicine_damage: float = Field(default=0.02, ge=0.0, le=1.0)
    low_security_threshold: float = Field(default=30.0, ge=0.0)
    low_security_damage: float = Field(default=0.02, ge=0.0, le=1.0)
    random_health_damage_max: float = Field(default=0.015, ge=0.0, le=1.0)
    death_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    shock: EnvironmentalShock = Field(default_factory=EnvironmentalShock)
    policy_impacts: Dict[Policy, PolicyImpact] = Field(
        default_factory=lambda: {
            Policy.FARMING: PolicyImpact(energy_cost=2.0, food_delta=14.0, water_delta=-3.0),
            Policy.MEDICINE: PolicyImpact(energy_cost=2.0, medicine_delta=8.0, health_boost=0.08),
            Policy.DEFENSE: PolicyImpact(energy_cost=4.0, security_delta=9.0),
            Policy.EXPLORATION: PolicyImpact(
                energy_cost=2.0,
                food_delta=7.0,
                water_delta=5.0,
                medicine_delta=2.5,
                injury_probability=0.02,
                injury_min=0.08,
                injury_max=0.20,
            ),
        }
    )


class RoundResult(BaseModel):
    """Snapshot recorded after one simulation step."""

    step: int
    rule: str
    selected_policy: Policy
    survival_rate: float
    welfare: float
    inequality: float
    resources: Dict[str, float]
    shock_occurred: bool = False
