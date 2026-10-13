"""Typed records for members, policy effects, settings, and round observations.

Validation checks declared data bounds; it does not establish realistic assumptions.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Role(str, Enum):
    """A member role identifies a specialist policy domain, not a privileged voting right."""

    DOCTOR = "doctor"
    FARMER = "farmer"
    ENGINEER = "engineer"
    GUARD = "guard"
    SCAVENGER = "scavenger"
    ELDER = "elder"


class Policy(str, Enum):
    """The four available collective actions; declaration order also breaks score ties."""

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


    Roles identify specialist domains. Adaptive rankings reflect private policy
    assessments; fixed mode retains the supplied ordinal preferences.
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
    general_accuracy: float | None = Field(default=None, ge=0.0, le=1.0)
    expert_accuracy: float | None = Field(default=None, ge=0.0, le=1.0)

    @property
    def expertise(self) -> Policy:
        return EXPERTISE[self.role]

    def top_choice(self) -> Policy:
        """Return the current first-ranked policy used for a first-choice ballot."""
        return self.preferences[0]

    def approves(self, policy: Policy, k: int = 2) -> bool:
        """Check whether a policy is within the current top-k approval set."""
        return policy in self.preferences[:k]

    def utility_for(self, policy: Policy) -> float:
        """Return the private assessment score when available, otherwise an ordinal proxy.

        These values are not the population welfare index or measured psychological utility.
        """
        if self.utility_weights:
            return self.utility_weights.get(policy, 0.0)
        ordinal_score = len(self.preferences) - self.preferences.index(policy)
        risk_penalty = self.risk_aversion if policy == Policy.EXPLORATION else 0.0
        cooperation_bonus = self.cooperation if policy in {Policy.FARMING, Policy.MEDICINE} else 0.0
        return float(ordinal_score + cooperation_bonus - risk_penalty)


class CommunityState(BaseModel):
    """Shared stock counters, not individual resource allocations or a market."""

    food: float = Field(default=100.0, ge=0.0)
    water: float = Field(default=100.0, ge=0.0)
    medicine: float = Field(default=50.0, ge=0.0)
    energy: float = Field(default=50.0, ge=0.0)
    security: float = Field(default=50.0, ge=0.0)

    def as_dict(self) -> Dict[str, float]:
        """Expose stocks by name for recorded outcomes and optional rule checks."""
        return self.model_dump()


class PolicyImpact(BaseModel):
    """Assumed changes in stocks and health when one policy is applied for a round."""

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
    """An outside event with an assumed chance, stock losses, and direct health damage."""

    probability: float = Field(default=0.05, ge=0.0, le=1.0)
    food_loss: float = Field(default=0.0, ge=0.0)
    water_loss: float = Field(default=0.0, ge=0.0)
    medicine_loss: float = Field(default=0.0, ge=0.0)
    security_loss: float = Field(default=0.0, ge=0.0)
    health_damage: float = Field(default=0.0, ge=0.0, le=1.0)


class DecisionParameters(BaseModel):
    """Assumptions about private information and how members score current policies.

    Accuracy reduces error spread; it is not a probability of selecting the best policy.
    """

    mode: Literal["adaptive", "fixed"] = "adaptive"
    general_accuracy: float = Field(default=0.55, ge=0.0, le=1.0)
    expert_accuracy: float = Field(default=0.90, ge=0.0, le=1.0)
    observation_noise: float = Field(default=0.6, ge=0.0)
    effect_noise: float = Field(default=0.6, ge=0.0)
    planning_horizon: int = Field(default=3, ge=1)
    preference_weight: float = Field(default=0.01, ge=0.0)
    reserve_weight: float = Field(default=0.02, ge=0.0)


class WelfareWeights(BaseModel):
    """Explicit normative priorities; weights must form a convex combination."""

    model_config = ConfigDict(allow_inf_nan=False, frozen=True)
    # Crisis priorities give survival the largest weight and reserves the
    # smallest proxy weight; reports also expose alternative priorities.
    survival: float = Field(default=0.65, ge=0.0, le=1.0)
    health: float = Field(default=0.25, ge=0.0, le=1.0)
    resources: float = Field(default=0.10, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def require_unit_sum(self) -> WelfareWeights:
        """Require a unit-sum weighting so the material index has a clear scale."""
        if not math.isclose(
            self.survival + self.health + self.resources, 1.0, rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError("welfare weights must sum to 1")
        return self


class ResourceReference(BaseModel):
    """Positive reference stocks make resource normalization explicit and finite."""

    model_config = ConfigDict(allow_inf_nan=False, frozen=True)
    # Shelter Alpha's stock scales are defaults, not universal resource values.
    food: float = Field(default=100.0, gt=0.0)
    water: float = Field(default=100.0, gt=0.0)
    medicine: float = Field(default=50.0, gt=0.0)
    energy: float = Field(default=50.0, gt=0.0)
    security: float = Field(default=50.0, gt=0.0)


class MetricParameters(BaseModel):
    """Reporting choices that do not feed back into policy selection or physical events."""

    welfare_weights: WelfareWeights = Field(default_factory=WelfareWeights)
    resource_reference: ResourceReference = Field(default_factory=ResourceReference)


class SimulationParameters(BaseModel):
    """Assumptions governing resource use, health effects, information, and reporting.

    Consumption is per living member; policy resource deltas are community-wide amounts.
    """

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
    decision: DecisionParameters = Field(default_factory=DecisionParameters)
    metrics: MetricParameters = Field(default_factory=MetricParameters)
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
    """One recorded round, combining two explicitly different observation times.

    Representation describes eligible voters before effects; material outcomes follow effects.
    None marks a conditional measure whose population is absent, not a numerical zero.
    """

    step: int
    rule: str
    selected_policy: Policy
    survival_rate: float
    welfare: float
    resilience: float = 0.0
    inequality: float
    resources: Dict[str, float]
    shock_occurred: bool = False
    preference_changes: int = 0
    mean_assessment_error: float = 0.0
    simulation_seed: int = 0
    environmental_shock_draw: float = 0.0
    environmental_health_damage: Dict[str, float] = Field(default_factory=dict)
    survivors: int = 0
    initial_population: int = 0
    survivor_health: float | None = None
    population_health: float = 0.0
    eligible_voters: int = 0
    preference_satisfaction: float | None = None
    prior_preference_satisfaction: float | None = None
    delegation_concentration: float | None = None
    max_vote_share: float | None = None
    delegated_vote_share: float | None = None
    vote_representatives: Dict[str, str] = Field(default_factory=dict)
    vote_weights: Dict[str, int] = Field(default_factory=dict)
    welfare_components: Dict[str, float] = Field(default_factory=dict)
    welfare_sensitivity: Dict[str, float] = Field(default_factory=dict)
