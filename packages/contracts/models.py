"""Versioned public configuration. Unknown settings fail instead of disappearing."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

ENGINE_COMMIT = "2742b5e0ce4330c9b14006b38acd3b5ebe00d6fd"
PROTOCOL_VERSION = "1.0"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ScenarioConfig(StrictModel):
    profile: Literal["enterprise_legacy"] = "enterprise_legacy"
    world_seed: int = Field(default=7, ge=0, le=2**32 - 1)
    targets: list[str] = Field(default_factory=lambda: ["Op_Server0"], min_length=1)
    defender: Literal["passive", "monitor"] = "passive"


class TeamConfig(StrictModel):
    architecture: Literal["hierarchy", "swarm", "independent"] = "hierarchy"
    workers: int = Field(default=4, ge=1, le=8)
    claim_ttl: int = Field(default=5, ge=1, le=50)


class CommunicationConfig(StrictModel):
    extra_delay: int = Field(default=0, ge=0, le=100)
    loss_probability: float = Field(default=0, ge=0, le=1)
    bytes_per_tick: int = Field(default=65536, ge=256, le=10000000)
    envelopes_per_tick: int = Field(default=64, ge=1, le=10000)
    ttl: int = Field(default=10, ge=1, le=1000)
    seed: int = Field(default=17, ge=0, le=2**32 - 1)
    verified_intel: bool = True


class CognitionConfig(StrictModel):
    provider: Literal["scripted", "ollama"] = "scripted"
    model: str = Field(default="", max_length=120)
    # Endpoint is service-local configuration, never a user-supplied URL.
    temperature: float = Field(default=0, ge=0, le=2)
    max_output_tokens: int = Field(default=512, ge=64, le=4096)
    max_context_bytes: int = Field(default=24000, ge=4000, le=128000)
    max_team_tokens: int = Field(default=40000, ge=1000, le=10000000)
    timeout_seconds: int = Field(default=60, ge=1, le=300)

    @model_validator(mode="after")
    def require_model(self):
        if self.provider == "ollama" and not self.model.strip():
            raise ValueError("Choose an installed Ollama model before creating a run")
        return self


class ScheduleConfig(StrictModel):
    mode: Literal["per_worker", "team_cap_one"] = "per_worker"
    seed: int = Field(default=27, ge=0, le=2**32 - 1)
    max_ticks: int = Field(default=100, ge=1, le=10000)


class EpisodeConfig(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    name: str = Field(default="Enterprise exploration", min_length=1, max_length=100)
    purpose: Literal["exploration", "evaluation"] = "exploration"
    scenario: ScenarioConfig = Field(default_factory=ScenarioConfig)
    team: TeamConfig = Field(default_factory=TeamConfig)
    communication: CommunicationConfig = Field(default_factory=CommunicationConfig)
    cognition: CognitionConfig = Field(default_factory=CognitionConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)


class ActionProposal(StrictModel):
    action: Literal["Sleep", "DiscoverRemoteSystems", "DiscoverNetworkServices", "ExploitRemoteService", "PrivilegeEscalate"]
    session: int = Field(default=0, ge=0)
    target: str | None = Field(default=None, max_length=100)
    rationale: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def require_target(self):
        if self.action != "Sleep" and not self.target:
            raise ValueError("This action needs an observed target")
        return self


class StepRequest(StrictModel):
    overrides: dict[str, ActionProposal] = Field(default_factory=dict)


class ExperimentSpec(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    name: str = Field(default="Organization comparison", max_length=100)
    base: EpisodeConfig = Field(default_factory=EpisodeConfig)
    architectures: list[Literal["hierarchy", "swarm", "independent"]] = Field(default_factory=lambda: ["hierarchy", "swarm"], min_length=1, max_length=3)
    worker_counts: list[int] = Field(default_factory=lambda: [2, 4], min_length=1, max_length=8)
    world_seeds: list[int] = Field(default_factory=lambda: [101, 102], min_length=1, max_length=1000)
    delays: list[int] = Field(default_factory=lambda: [0], min_length=1, max_length=20)
    losses: list[float] = Field(default_factory=lambda: [0], min_length=1, max_length=20)
    replicates: int = Field(default=1, ge=1, le=100)

    @model_validator(mode="after")
    def check_dimensions(self):
        for name in ["architectures", "worker_counts", "world_seeds", "delays", "losses"]:
            values = getattr(self, name)
            if len(set(values)) != len(values):
                raise ValueError(f"Repeated values in {name}")
        if any(x < 1 or x > 8 for x in self.worker_counts):
            raise ValueError("Worker count must be 1–8")
        if any(x < 0 or x >= 2**32 for x in self.world_seeds):
            raise ValueError("Invalid world seed")
        if any(x < 0 or x > 100 for x in self.delays):
            raise ValueError("Invalid delay")
        if any(x < 0 or x > 1 for x in self.losses):
            raise ValueError("Invalid loss probability")
        size = len(self.architectures) * len(self.worker_counts) * len(self.world_seeds) * len(self.delays) * len(self.losses) * self.replicates
        if size > 10000:
            raise ValueError("Matrix exceeds 10,000 jobs; split the study")
        return self
