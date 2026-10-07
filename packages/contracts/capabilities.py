"""Profile registry shared by configuration/API; no simulator imports."""
from packages.contracts.models import CC4_COMMIT, CC4_TARGETS, ENGINE_COMMIT, LEGACY_TARGETS, EpisodeConfig
from packages.contracts.module_registry import describe_modules, complexity_presets

ENGINE_LOCKS = {
    "enterprise_legacy": {"engine_commit": ENGINE_COMMIT, "python_prefix": "3.8.", "gym": "0.23.1", "numpy": "1.21.6"},
    "enterprise_cc4": {"engine_commit": CC4_COMMIT, "python_prefix": "3.12.", "gym": "0.26.2", "numpy": "1.26.4"},
    "enterprise_cc4_research": {"engine_commit": CC4_COMMIT, "python_prefix": "3.12.", "gym": "0.26.2", "numpy": "1.26.4"},
}


def profiles():
    cc4 = EpisodeConfig.model_validate({"name": "CC4 enterprise exploration", "scenario": {
        "profile": "enterprise_cc4", "world_seed": 100,
        "targets": ["restricted_zone_a_subnet_server_host_0"], "defender": "monitor"}})
    research = EpisodeConfig.model_validate({"schema_version": "2.0", "name": "Investigative research demo",
        "scenario": {"profile": "enterprise_cc4_research", "world_seed": 100, "targets": ["restricted_zone_a_subnet_server_host_0"],
                     "research": {}, "cc4": {"addon_services": 0}},
        "cognition": {"scripted_policy": "evidence_controller"}, "schedule": {"max_ticks": 180}})
    return [
        {"id": "enterprise_legacy", "name": "Enterprise · legacy Scenario2", "targets": list(LEGACY_TARGETS),
         "defenders": ["passive", "monitor"], "actions": ["Sleep", "DiscoverRemoteSystems", "DiscoverNetworkServices", "ExploitRemoteService", "PrivilegeEscalate"],
         "default_config": EpisodeConfig().model_dump(), "qualification": "Legacy software acceptance; research calibration pending"},
        {"id": "enterprise_cc4", "name": "Enterprise · CAGE Challenge 4", "targets": list(CC4_TARGETS),
         "defenders": ["passive", "monitor", "reactive_restore"], "actions": ["Sleep", "DiscoverRemoteSystems", "DiscoverNetworkServices", "ExploitRemoteService", "PrivilegeEscalate", "EstablishPivot"],
         "default_config": cc4.model_dump(), "qualification": "CC4 integration; research calibration pending",
         "complexity_modules": describe_modules("enterprise_cc4"), "complexity_presets": complexity_presets(),
         "features": ["multi_tick_actions", "private_mobile_workers", "native_recovery", "mission_phase_policy"]},
        {"id": "enterprise_cc4_research", "name": "Graduation · investigative CC4", "targets": ["restricted_zone_a_subnet_server_host_0", "operational_zone_a_subnet_server_host_0"],
         "defenders": ["passive"], "actions": ["Sleep", "DiscoverRemoteSystems", "DiscoverNetworkServices", "PrivilegeEscalate", "EstablishPivot", "Probe", "InspectArtifacts", "AttemptAccess"],
         "default_config": research.model_dump(), "qualification": "Bounded native feasibility checked per world; scientific calibration outstanding",
         "features": ["explicit_methods", "private_typed_evidence", "simulated_tokens", "shared_patch_or_restore", "matched_split_entry"]},
    ]
