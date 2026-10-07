"""Versioned public configuration. Unknown settings fail instead of disappearing."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from packages.contracts.complexity import ComplexitySettings
from packages.contracts.missions import MissionSettings
from packages.contracts.research_profile import ResearchSettings, ResourceSettings

ENGINE_COMMIT = "2742b5e0ce4330c9b14006b38acd3b5ebe00d6fd"
CC4_COMMIT = "8c3c50ca54b176c2de199847944e8dcc035497e3"
PROTOCOL_VERSION = "1.0"
LEGACY_TARGETS = ("User1", "User2", "User3", "User4", "Enterprise0", "Enterprise1", "Enterprise2", "Defender", "Op_Host0", "Op_Host1", "Op_Host2", "Op_Server0")
CC4_ZONES = ("contractor_network_subnet", "restricted_zone_a_subnet", "operational_zone_a_subnet", "restricted_zone_b_subnet", "operational_zone_b_subnet", "public_access_zone_subnet", "admin_network_subnet", "office_network_subnet")
CC4_TARGETS = tuple(zone + "_server_host_0" for zone in CC4_ZONES)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CC4Settings(StrictModel):
    user_hosts: int = Field(default=3, ge=3, le=10)
    server_hosts: int = Field(default=1, ge=1, le=6)
    addon_services: int = Field(default=4, ge=0, le=5)
    response_delay: int = Field(default=2, ge=1, le=100)
    response_cooldown: int = Field(default=10, ge=1, le=1000)
    response_budget: int = Field(default=4, ge=1, le=100)


class ScenarioConfig(StrictModel):
    profile: Literal["enterprise_legacy", "enterprise_cc4", "enterprise_cc4_research"] = "enterprise_legacy"
    world_seed: int = Field(default=7, ge=0, le=2**32 - 1)
    targets: list[str] = Field(default_factory=lambda: ["Op_Server0"], min_length=1, max_length=12)
    defender: Literal["passive", "monitor", "reactive_restore"] = "passive"
    cc4: CC4Settings | None = None
    complexity: ComplexitySettings | None = None
    mission: MissionSettings | None = None
    research: ResearchSettings | None = None

    @model_validator(mode="after")
    def unique_targets(self):
        if len(set(self.targets)) != len(self.targets):
            raise ValueError("Mission target names must be unique")
        cc4_profile = self.profile in ("enterprise_cc4", "enterprise_cc4_research")
        allowed = CC4_TARGETS if cc4_profile else LEGACY_TARGETS
        if any(target not in allowed for target in self.targets):
            raise ValueError("Mission targets must belong to the selected profile")
        if cc4_profile:
            self.cc4 = self.cc4 or CC4Settings()
        elif self.cc4 is not None or self.defender == "reactive_restore":
            raise ValueError("CC4 settings and reactive recovery require enterprise_cc4")
        if self.complexity is not None and self.profile != "enterprise_cc4":
            raise ValueError("Complexity modules currently require enterprise_cc4")
        if self.complexity and self.complexity.routes.enabled:
            if self.complexity.routes.alternatives >= self.cc4.user_hosts:
                raise ValueError("Alternative gateways require user_hosts >= alternatives + 1")
        if self.mission is not None:
            if not cc4_profile:
                raise ValueError("Sustained missions currently require enterprise_cc4")
            if self.mission.objectives:
                covered = {h for o in self.mission.objectives for h in o.targets}
                if covered != set(self.targets):
                    raise ValueError("Objective targets must cover exactly the mission targets")
                required = {h for o in self.mission.objectives for h in o.requires_privileged_hosts}
                if not required <= set(CC4_TARGETS):
                    raise ValueError("Physical prerequisites must be generated CC4 server hosts")
        if self.complexity and self.complexity.routes.enabled and self.complexity.routes.hardened_dead_end and "contractor_network_subnet_server_host_0" in self.targets:
            raise ValueError("Mission target cannot be the hardened route dead end")
        if self.mission and self.complexity and self.complexity.routes.enabled and self.complexity.routes.hardened_dead_end:
            if any("contractor_network_subnet_server_host_0" in o.requires_privileged_hosts for o in self.mission.objectives):
                raise ValueError("Hardened dead end cannot be a required privileged host")
        if self.profile == "enterprise_cc4_research":
            self.research = self.research or ResearchSettings()
            if self.defender != "passive" or self.complexity is not None:
                raise ValueError("Research profile uses its shared research defender, not historical modules")
            required_targets = {"restricted_zone_a_subnet_server_host_0"}
            if self.research.recipe == "combine":
                required_targets.add("operational_zone_a_subnet_server_host_0")
            if set(self.targets) != required_targets:
                raise ValueError("Targets must match the selected research recipe")
        elif self.research is not None:
            raise ValueError("Research settings require enterprise_cc4_research")
        return self


class TeamConfig(StrictModel):
    architecture: Literal["hierarchy", "swarm", "independent"] = "hierarchy"
    workers: int = Field(default=4, ge=1, le=8)
    claim_ttl: int = Field(default=5, ge=1, le=50)


class CommunicationLink(StrictModel):
    sender: str = Field(pattern=r"^(Red_[0-7]|Coordinator)$")
    recipient: str = Field(pattern=r"^(Red_[0-7]|Coordinator)$")


class LinkInterruption(StrictModel):
    start_tick: int = Field(ge=1, le=10000)
    end_tick: int = Field(ge=1, le=10000)
    sender: str | None = Field(default=None, pattern=r"^(Red_[0-7]|Coordinator)$")
    recipient: str | None = Field(default=None, pattern=r"^(Red_[0-7]|Coordinator)$")
    bidirectional: bool = True

    @model_validator(mode="after")
    def ordered_window(self):
        if self.end_tick < self.start_tick:
            raise ValueError("Interruption end must be at or after its start")
        if self.sender is not None and self.sender == self.recipient:
            raise ValueError("A communication link cannot connect an actor to itself")
        return self


class CommunicationConfig(StrictModel):
    extra_delay: int = Field(default=0, ge=0, le=100)
    loss_probability: float = Field(default=0, ge=0, le=1)
    bytes_per_tick: int = Field(default=65536, ge=256, le=10000000)
    envelopes_per_tick: int = Field(default=64, ge=1, le=10000)
    ttl: int = Field(default=10, ge=1, le=1000)
    seed: int = Field(default=17, ge=0, le=2**32 - 1)
    verified_intel: bool = True
    links: list[CommunicationLink] | None = Field(default=None, max_length=64)
    interruptions: list[LinkInterruption] = Field(default_factory=list, max_length=100)


class SearchSettings(StrictModel):
    risk_weight: float = Field(default=8, ge=0, le=100)
    failure_penalty: float = Field(default=6, ge=0, le=100)
    unknown_edge_penalty: float = Field(default=4, ge=0, le=100)
    max_expansions: int = Field(default=128, ge=1, le=4096)


class CognitionConfig(StrictModel):
    provider: Literal["scripted", "ollama"] = "scripted"
    scripted_policy: Literal["legacy", "local_rules", "local_replan", "local_search", "fixed_workflow", "evidence_controller", "observed_planner"] = "legacy"
    search: SearchSettings = Field(default_factory=SearchSettings)
    action_retry_limit: int = Field(default=2, ge=1, le=20)
    failure_backoff_ticks: int = Field(default=0, ge=0, le=100)
    model: str = Field(default="", max_length=120)
    # Endpoint is service-local configuration, never a user-supplied URL.
    temperature: float = Field(default=0, ge=0, le=2)
    max_output_tokens: int = Field(default=512, ge=64, le=4096)
    max_context_bytes: int = Field(default=24000, ge=4000, le=128000)
    max_team_tokens: int = Field(default=40000, ge=1000, le=10000000)
    timeout_seconds: int = Field(default=60, ge=1, le=300)

    @model_validator(mode="after")
    def require_model(self):
        if self.provider != "scripted" and self.scripted_policy != "legacy":
            raise ValueError("Select a scripted policy only with the scripted provider")
        if self.provider == "ollama" and not self.model.strip():
            raise ValueError("Choose an installed Ollama model before creating a run")
        return self


class ScheduleConfig(StrictModel):
    mode: Literal["per_worker", "team_cap_one"] = "per_worker"
    seed: int = Field(default=27, ge=0, le=2**32 - 1)
    max_ticks: int = Field(default=100, ge=1, le=10000)


class EpisodeConfig(StrictModel):
    schema_version: Literal["1.0", "2.0"] = "1.0"
    name: str = Field(default="Enterprise exploration", min_length=1, max_length=100)
    purpose: Literal["exploration", "evaluation"] = "exploration"
    scenario: ScenarioConfig = Field(default_factory=ScenarioConfig)
    team: TeamConfig = Field(default_factory=TeamConfig)
    communication: CommunicationConfig = Field(default_factory=CommunicationConfig)
    cognition: CognitionConfig = Field(default_factory=CognitionConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    resources: ResourceSettings | None = None

    @model_validator(mode="after")
    def validate_topology(self):
        research = self.scenario.profile == "enterprise_cc4_research"
        if research != (self.schema_version == "2.0"):
            raise ValueError("Research episodes require schema 2.0; historical profiles require 1.0")
        if research:
            self.resources = self.resources or ResourceSettings()
            if "communication" not in self.model_fields_set or "bytes_per_tick" not in self.communication.model_fields_set:
                # Core transport is healthy (or delayed), not accidentally
                # capacity-impaired by four evidence-bearing worker reports.
                self.communication.bytes_per_tick = 1000000
            if "cognition" not in self.model_fields_set or "max_context_bytes" not in self.cognition.model_fields_set:
                self.cognition.max_context_bytes = 128000
            if self.cognition.provider == "scripted" and self.cognition.scripted_policy not in ("fixed_workflow", "evidence_controller", "observed_planner"):
                raise ValueError("Research episodes require a research-catalog scripted policy")
            if self.team.workers not in (1, 2, 4):
                raise ValueError("Qualified research worker counts are 1, 2 and 4")
            if self.scenario.research.initial_access == "matched_split_entry" and self.team.workers == 1:
                raise ValueError("Split entry needs two or four workers")
            if self.communication.loss_probability or self.communication.extra_delay not in (0, 2) or self.communication.links is not None or self.communication.interruptions:
                raise ValueError("Core research supports healthy transport or delay 2; custom outages are historical only")
        elif self.resources is not None:
            raise ValueError("Team attempt resources require the research profile")
        if not research and self.cognition.scripted_policy in ("fixed_workflow", "evidence_controller", "observed_planner"):
            raise ValueError("Research policies require the research profile")
        mission = self.scenario.mission
        if mission:
            horizon = self.schedule.max_ticks
            if mission.hold_ticks > horizon or mission.deadline_tick is not None and mission.deadline_tick > horizon:
                raise ValueError("Mission duration and deadline must fit the episode tick limit")
            for objective in mission.objectives:
                if objective.hold_ticks + mission.hold_ticks - 1 > (mission.deadline_tick or horizon):
                    raise ValueError("Objective and final hold durations cannot fit the mission horizon")
                if objective.deadline_tick is not None and objective.deadline_tick > (mission.deadline_tick or horizon):
                    raise ValueError("Objective deadline must fit the mission horizon")
        actors = {f"Red_{i}" for i in range(self.team.workers)}
        reasoners = actors | ({"Coordinator"} if self.team.architecture == "hierarchy" else set())
        def possible(sender, recipient):
            return sender != recipient and self.team.architecture != "independent" and (self.team.architecture != "hierarchy" or ((sender == "Coordinator") != (recipient == "Coordinator")))
        seen = set()
        for link in self.communication.links or []:
            pair = (link.sender, link.recipient)
            if not set(pair) <= reasoners or not possible(*pair) or pair in seen:
                raise ValueError("Links must be unique directed edges within the configured organization")
            seen.add(pair)
        for interruption in self.communication.interruptions:
            if any(a is not None and a not in reasoners for a in [interruption.sender, interruption.recipient]):
                raise ValueError("Interruption names an unavailable reasoner")
            if interruption.sender and interruption.recipient and not possible(interruption.sender, interruption.recipient):
                raise ValueError("Interruption must name a possible organization link")
        return self


class ActionProposal(StrictModel):
    action: Literal["Sleep", "DiscoverRemoteSystems", "DiscoverNetworkServices", "ExploitRemoteService", "PrivilegeEscalate", "EstablishPivot", "Probe", "InspectArtifacts", "AttemptAccess"]
    session: int = Field(default=0, ge=0)
    target: str | None = Field(default=None, max_length=100)
    rationale: str = Field(default="", max_length=1000)
    method: Literal["web_rfi", "ssh_weak_auth", "credential_login"] | None = None
    probe: Literal["connectivity", "service_behavior", "auth_policy"] | None = None
    port: Literal[22, 80] | None = None
    token_ref: str | None = Field(default=None, max_length=100)
    source_host: str | None = Field(default=None, max_length=100)
    basis_evidence_ids: list[str] = Field(default_factory=list, max_length=16)

    @model_validator(mode="after")
    def require_target(self):
        if self.action != "Sleep" and not self.target:
            raise ValueError("This action needs an observed target")
        if (self.action == "AttemptAccess") != (self.method is not None):
            raise ValueError("Exactly AttemptAccess requires a method")
        if (self.action == "Probe") != (self.probe is not None and self.port is not None):
            raise ValueError("Exactly Probe requires a probe kind and port")
        if self.action != "Probe" and (self.probe is not None or self.port is not None):
            raise ValueError("Probe parameters only belong to Probe")
        if self.probe == "service_behavior" and self.port != 80 or self.probe == "auth_policy" and self.port != 22:
            raise ValueError("Probe port does not match protocol")
        if (self.method == "credential_login") != (self.token_ref is not None):
            raise ValueError("Exactly credential_login requires a token reference")
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
