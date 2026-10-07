"""Public state-based mission requirements; no agent report can satisfy them."""
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ObjectiveSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=48, pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$")
    targets: list[str] = Field(min_length=1, max_length=12)
    requires_privileged_hosts: list[str] = Field(default_factory=list, max_length=12)
    hold_ticks: int = Field(default=1, ge=1, le=1000)
    deadline_tick: int | None = Field(default=None, ge=1, le=10000)

    @model_validator(mode="after")
    def consistent(self):
        if len(set(self.targets)) != len(self.targets) or len(set(self.requires_privileged_hosts)) != len(self.requires_privileged_hosts):
            raise ValueError("Objective host lists must be unique")
        if set(self.targets) & set(self.requires_privileged_hosts):
            raise ValueError("A prerequisite must be distinct from the objective's targets")
        if self.deadline_tick is not None and self.hold_ticks > self.deadline_tick:
            raise ValueError("Objective hold duration exceeds its deadline")
        return self


class MissionSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hold_ticks: int = Field(default=1, ge=1, le=1000)
    deadline_tick: int | None = Field(default=None, ge=1, le=10000)
    objectives: list[ObjectiveSettings] = Field(default_factory=list, max_length=16)

    @model_validator(mode="after")
    def consistent(self):
        if len({o.id for o in self.objectives}) != len(self.objectives):
            raise ValueError("Objective IDs must be unique")
        if self.deadline_tick is not None and self.hold_ticks > self.deadline_tick:
            raise ValueError("Mission hold duration exceeds its deadline")
        return self
