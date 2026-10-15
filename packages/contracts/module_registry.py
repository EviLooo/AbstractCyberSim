"""Pure capability/compiler layer. No simulator, architecture input or RNG."""
import hashlib
import json
from packages.contracts.missions import MissionSettings
from packages.contracts.complexity import ComplexitySettings, RouteSettings

REGISTRY_VERSION = "1.0"


def describe_modules(profile):
    if profile != "enterprise_cc4":
        return []
    return [
        {"id": "native_population", "version": "1.0", "settings_path": "scenario.cc4",
         "parameters": ["user_hosts", "server_hosts", "addon_services"], "requires": [],
         "qualification": "native materialization; arbitrary topology and realism unqualified"},
        {"id": "observed_restore", "version": "1.0", "settings_path": "scenario.defender",
         "parameters": ["response_delay", "response_cooldown", "response_budget"],
         "requires": ["native_monitor"], "qualification": "bounded observed restoration"},
        {"id": "temporal_beliefs", "version": "1.0", "settings_path": "scenario.complexity.beliefs",
         "parameters": ["enabled", "stale_after", "observation_delay"], "requires": ["actor_private_evidence"],
         "qualification": "software checks; age denotes uncertainty, not actual invalidity",
         "status_model": "Own sessions, busy state and action outcomes immediate; host/service evidence delayed"},
        {"id": "communication", "version": "1.0", "settings_path": "communication",
         "parameters": ["extra_delay", "loss_probability", "bytes_per_tick", "envelopes_per_tick", "ttl", "interruptions"],
         "requires": [], "qualification": "overlay delivery; distinct from observation latency"},
        {"id": "segmented_routes", "version": "1.0", "settings_path": "scenario.complexity.routes",
         "parameters": ["enabled", "depth", "alternatives", "hardened_dead_end"],
         "requires": ["native_host_blocks", "EstablishPivot"],
         "qualification": "bounded native route fixtures; pivot deployment is an explicit extension"},
        {"id": "route_tradeoffs", "version": "1.0", "settings_path": "scenario.complexity.routes.tradeoffs",
         "parameters": ["enabled", "fast_exploit_ticks", "quiet_exploit_ticks", "privileged_route",
                        "privileged_exploit_ticks", "fast_detection_probability", "quiet_detection_probability",
                        "privileged_detection_probability", "reactive_blocks", "reaction_delay", "block_ticks", "response_budget"],
         "requires": ["segmented_routes", "native_service_templates", "native_multi_tick_actions"],
         "qualification": "synthetic gateway templates and traffic sensors; service ACL quarantine, not full host isolation"},
        {"id": "sustained_mission", "version": "1.0", "settings_path": "scenario.mission",
         "parameters": ["hold_ticks", "deadline_tick", "objectives"],
         "requires": ["active_native_privileged_sessions"],
         "qualification": "post-tick state-based objective monitor; durations are synthetic controls"},
    ]


def compile_modules(config):
    """Strict models already reject unknown/unqualified modules before launch."""
    scenario = config.scenario
    if scenario.research:
        resolved = {"registry_version": "2.0", "profile": scenario.profile,
            "modules": {"investigation": scenario.research.model_dump(),
                        "communication": config.communication.model_dump(),
                        "resources": config.resources.model_dump()},
            "seed_namespaces": {"world": scenario.world_seed, "transport": config.communication.seed,
                                "schedule": config.schedule.seed, **scenario.research.seed_namespaces.model_dump()},
            "mission": {"targets": list(scenario.targets), "settings": (scenario.mission or MissionSettings()).model_dump()},
            "unsupported": ["real_targets", "arbitrary_topology", "arbitrary_techniques", "isolation", "sensor_noise"]}
        return dict(resolved, manifest_hash=hashlib.sha256(json.dumps(resolved, sort_keys=True, separators=(",", ":")).encode()).hexdigest())
    beliefs = scenario.complexity.beliefs.model_dump() if scenario.complexity else {"enabled": False, "stale_after": 8, "observation_delay": 0}
    resolved = {"registry_version": REGISTRY_VERSION, "profile": scenario.profile,
        "modules": {"temporal_beliefs": {"version": "1.0", **beliefs},
            "segmented_routes": {"version": "1.0", **(scenario.complexity.routes.model_dump() if scenario.complexity else RouteSettings().model_dump())},
            "route_tradeoffs": {"version": "1.0", **(scenario.complexity.routes.tradeoffs.model_dump() if scenario.complexity else RouteSettings().tradeoffs.model_dump())},
            "defender": {"version": "1.0", "mode": scenario.defender,
                "response": {k: getattr(scenario.cc4, k) for k in ["response_delay", "response_cooldown", "response_budget"]} if scenario.cc4 else None},
            "native_population": {"version": "1.0", "parameters": {k: getattr(scenario.cc4, k) for k in ["user_hosts", "server_hosts", "addon_services"]} if scenario.cc4 else None},
            "communication": {"version": "1.0", **config.communication.model_dump()}},
        "seed_namespaces": {"world": scenario.world_seed, "transport": config.communication.seed, "schedule": config.schedule.seed},
        "mission": {"targets": list(scenario.targets), "objective": "sustained_privileged_access" if scenario.mission else "privileged_access_all",
                    "settings": (scenario.mission or MissionSettings()).model_dump()},
        "unsupported": ["arbitrary_topology", "patching", "isolation", "sensor_noise"]}
    # The module fingerprint excludes organizational routing (the treatment).
    resolved["modules"]["communication"].pop("links", None)
    if scenario.complexity and scenario.complexity.routes.tradeoffs.enabled:
        resolved["seed_namespaces"].update(route_templates=f"route-templates:1.0:{scenario.world_seed}",
                                           route_sensors=f"route-sensors:1.0:{scenario.world_seed}")
    return dict(resolved, manifest_hash=hashlib.sha256(json.dumps(resolved, sort_keys=True, separators=(",", ":")).encode()).hexdigest())


def complexity_presets():
    # Development bundles, not scientifically qualified C0/C1/C2/C3 levels.
    presets = [
        {"id": "native_static", "name": "Native static control", "defender": "passive",
         "complexity": {"version": "1.0", "beliefs": {"enabled": False, "stale_after": 8, "observation_delay": 0}, "routes": {"enabled": False, "depth": 1, "alternatives": 2, "hardened_dead_end": False}}},
        {"id": "observed_recovery", "name": "Observed recovery and evidence age", "defender": "reactive_restore",
         "complexity": {"version": "1.0", "beliefs": {"enabled": True, "stale_after": 8, "observation_delay": 2}, "routes": {"enabled": False, "depth": 1, "alternatives": 2, "hardened_dead_end": False}}},
        {"id": "segmented_routes", "name": "Segmented routes and alternatives", "defender": "monitor",
         "complexity": {"version": "1.0", "beliefs": {"enabled": True, "stale_after": 8, "observation_delay": 0}, "routes": {"enabled": True, "depth": 2, "alternatives": 2, "hardened_dead_end": True}}},
        {"id": "route_tradeoffs", "name": "Fast exposed / slower quiet routes", "defender": "passive",
         "complexity": {"version": "1.0", "beliefs": {"enabled": True, "stale_after": 12, "observation_delay": 0},
                        "routes": {"enabled": True, "depth": 1, "alternatives": 2, "hardened_dead_end": True,
                                   "tradeoffs": {"enabled": True}}}},
    ]
    return [dict(preset, complexity=ComplexitySettings.model_validate(preset["complexity"]).model_dump()) for preset in presets]
