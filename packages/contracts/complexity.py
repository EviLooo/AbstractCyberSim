"""Additive module contract; this is not the proposed unrestricted v2 profile."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class RouteTradeoffs(BaseModel):
    """Synthetic durations and a separate traffic sensor, not exploit success odds."""
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    fast_exploit_ticks: int = Field(default=2, ge=1, le=20)
    quiet_exploit_ticks: int = Field(default=8, ge=2, le=30)
    privileged_route: bool = False
    privileged_exploit_ticks: int = Field(default=6, ge=1, le=30)
    fast_detection_probability: float = Field(default=0.9, ge=0, le=1)
    quiet_detection_probability: float = Field(default=0.1, ge=0, le=1)
    privileged_detection_probability: float = Field(default=0.4, ge=0, le=1)
    reactive_blocks: bool = True
    reaction_delay: int = Field(default=2, ge=1, le=100)
    block_ticks: int = Field(default=12, ge=1, le=1000)
    response_budget: int = Field(default=4, ge=1, le=100)

    @model_validator(mode="after")
    def distinct_tradeoffs(self):
        if self.enabled and (self.quiet_exploit_ticks <= self.fast_exploit_ticks or
                             self.quiet_detection_probability >= self.fast_detection_probability):
            raise ValueError("Quiet routes must take longer and have less route-sensor exposure than fast routes")
        return self


class BeliefSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    stale_after: int = Field(default=8, ge=1, le=1000)
    observation_delay: int = Field(default=0, ge=0, le=20)


class RouteSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    depth: int = Field(default=1, ge=1, le=3)
    alternatives: int = Field(default=2, ge=1, le=9)
    hardened_dead_end: bool = False
    tradeoffs: RouteTradeoffs = Field(default_factory=RouteTradeoffs)

    @model_validator(mode="after")
    def requires_routes(self):
        if self.tradeoffs.enabled and (not self.enabled or self.alternatives < 2):
            raise ValueError("Route tradeoffs require enabled routes and at least two alternatives")
        if self.tradeoffs.enabled and self.tradeoffs.privileged_route and self.alternatives < 3:
            raise ValueError("The privileged template requires at least three alternatives")
        return self


class ComplexitySettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal["1.0"] = "1.0"
    beliefs: BeliefSettings = Field(default_factory=BeliefSettings)
    routes: RouteSettings = Field(default_factory=RouteSettings)
