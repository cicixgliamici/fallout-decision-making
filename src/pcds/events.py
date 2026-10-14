"""Record neutral facts without inspecting or advancing any random generator."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EVENT_SCHEMA = "simulation-events-v2"
EventKind = Literal[
    "policy_selected",
    "policy_override",
    "policy_blocked",
    "resource_change",
    "treatment",
    "injury",
    "shortage",
    "shock",
    "health_damage",
    "death",
]


class SimulationEvent(BaseModel):
    """An ordered fact; before/after are actual values, not intended effects."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)
    step: int = Field(ge=0)
    sequence: int = Field(ge=0)
    kind: EventKind
    subject: str = Field(min_length=1)
    cause: str = Field(min_length=1)
    before: float | None = None
    after: float | None = None
    requested_change: float | None = None
    details: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_observed_values(self) -> SimulationEvent:
        # State-changing events must carry both endpoints to support factual replay.
        if self.kind in {"resource_change", "treatment", "injury", "health_damage", "death"}:
            if self.before is None or self.after is None:
                raise ValueError("state-changing events require before and after values")
        return self


class EventRecorder:
    """Assign local sequence numbers while leaving physical calculations untouched."""

    def __init__(self, step: int):
        self.step = step
        self.events: list[SimulationEvent] = []

    def record(
        self,
        kind: EventKind,
        subject: str,
        cause: str,
        before: float | None = None,
        after: float | None = None,
        requested_change: float | None = None,
        details: dict[str, float] | None = None,
    ) -> None:
        # Capture scalars and copy details so later world changes cannot rewrite history.
        self.events.append(
            SimulationEvent(
                step=self.step,
                sequence=len(self.events),
                kind=kind,
                subject=subject,
                cause=cause,
                before=before,
                after=after,
                requested_change=requested_change,
                details=dict(details or {}),
            )
        )
