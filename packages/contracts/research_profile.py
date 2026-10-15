"""Bounded investigative profile. Hidden settings are researcher configuration.

These fields must never be copied into an actor prompt or candidate generator.
"""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResearchModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceSettings(ResearchModel):
    observation_delay: int = Field(default=0, ge=0, le=2)
    stale_after: int = Field(default=8, ge=4, le=12)


class ChangeSettings(ResearchModel):
    mode: Literal["none", "patch_rfi", "restore"] = "none"
    response_delay: int = Field(default=4, ge=2, le=8)
    response_budget: int = Field(default=0, ge=0, le=1)

    @model_validator(mode="after")
    def budget_matches_mode(self):
        if (self.mode == "none") != (self.response_budget == 0):
            raise ValueError("Choose no response, or exactly one shared response")
        return self


class SeedNamespaces(ResearchModel):
    recipe: int = Field(default=401, ge=0, le=2**32 - 1)
    event: int = Field(default=701, ge=0, le=2**32 - 1)


class ResearchSettings(ResearchModel):
    module_version: Literal["1.0"] = "1.0"
    recipe: Literal["linear_control", "investigate", "combine", "recover"] = "investigate"
    conditions: Literal["single", "paired"] = "paired"
    # Fixture overrides remain researcher-only; seeded is the ordinary setting.
    condition_variant: Literal["seeded", "import_disabled", "source_denied", "import_enabled", "ssh_hardened"] = "seeded"
    credential_variant: Literal["seeded", "valid", "wrong_scope", "invalid"] = "seeded"
    capability_coupling: Literal["separate", "bridge_and_token"] = "separate"
    initial_access: Literal["common_entry", "matched_split_entry"] = "common_entry"
    evidence: EvidenceSettings = Field(default_factory=EvidenceSettings)
    change: ChangeSettings = Field(default_factory=ChangeSettings)
    seed_namespaces: SeedNamespaces = Field(default_factory=SeedNamespaces)
    catalog: Literal["minimal_access_v1"] = "minimal_access_v1"
    background_access: Literal["deny"] = "deny"
    native_mission_phase_policy: Literal["fixed_research_policy_v1"] = "fixed_research_policy_v1"

    @model_validator(mode="after")
    def supported_recipe(self):
        if (self.recipe == "combine") != (self.capability_coupling == "bridge_and_token"):
            raise ValueError("combine requires bridge_and_token; other recipes use separate")
        if (self.recipe == "recover") != (self.change.mode != "none"):
            raise ValueError("Only recover enables one defensive change")
        return self


class ResourceSettings(ResearchModel):
    team_access_attempts: int = Field(default=12, ge=1, le=100)


from packages.contracts.research_catalog import PUBLIC_CATALOG
