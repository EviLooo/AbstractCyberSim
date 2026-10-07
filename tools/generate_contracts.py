"""Generate checked-in JSON Schemas used by UI and API validation."""
import json
from pathlib import Path
from packages.contracts.models import ActionProposal, EpisodeConfig, ExperimentSpec
from packages.contracts.capabilities import profiles
from packages.contracts.complexity import ComplexitySettings
from packages.contracts.missions import MissionSettings

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / "packages/contracts/schemas"
    target.mkdir(parents=True, exist_ok=True)
    for model in [ActionProposal, EpisodeConfig, ExperimentSpec]:
        (target / (model.__name__ + ".json")).write_text(json.dumps(model.model_json_schema(), indent=2) + "\n", encoding="utf-8")
    examples = ROOT / "configs"
    examples.mkdir(exist_ok=True)
    for name, architecture in [("hierarchy", "hierarchy"), ("swarm", "swarm")]:
        config = EpisodeConfig()
        config.team.architecture = architecture
        (examples / (name + ".json")).write_text(config.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (examples / "comparison.json").write_text(ExperimentSpec().model_dump_json(indent=2) + "\n", encoding="utf-8")
    for profile in profiles():
        if profile["id"] == "enterprise_cc4":
            (examples / "cc4.json").write_text(json.dumps(profile["default_config"], indent=2) + "\n", encoding="utf-8")
            preset = next(p for p in profile["complexity_presets"] if p["id"] == "observed_recovery")
            recovery = EpisodeConfig.model_validate(profile["default_config"])
            recovery.name = "CC4 observed recovery"
            recovery.scenario.defender = preset["defender"]
            recovery.scenario.complexity = ComplexitySettings.model_validate(preset["complexity"])
            (examples / "cc4-recovery.json").write_text(recovery.model_dump_json(indent=2) + "\n", encoding="utf-8")
            preset = next(p for p in profile["complexity_presets"] if p["id"] == "segmented_routes")
            recovery.name = "CC4 segmented routes"
            recovery.scenario.defender = preset["defender"]
            recovery.scenario.complexity = ComplexitySettings.model_validate(preset["complexity"])
            recovery.schedule.max_ticks = 300
            (examples / "cc4-routes.json").write_text(recovery.model_dump_json(indent=2) + "\n", encoding="utf-8")
            recovery.name = "CC4 sustained two-target mission"
            recovery.scenario.targets = ["restricted_zone_a_subnet_server_host_0", "restricted_zone_b_subnet_server_host_0"]
            recovery.scenario.mission = MissionSettings(hold_ticks=5, deadline_tick=250)
            (examples / "cc4-mission.json").write_text(recovery.model_dump_json(indent=2) + "\n", encoding="utf-8")
            for policy in ['local_rules', 'local_replan', 'local_search']:
                baseline = recovery.model_copy(deep=True)
                baseline.name = 'CC4 development baseline - ' + policy
                baseline.team.architecture = 'independent'
                baseline.team.workers = 1
                baseline.scenario.defender = 'passive'
                baseline.scenario.cc4.addon_services = 0
                baseline.scenario.complexity.routes.depth = 1
                baseline.scenario.complexity.beliefs.enabled = False
                baseline.scenario.mission = MissionSettings(hold_ticks=3)
                baseline.cognition.scripted_policy = policy
                baseline.cognition.action_retry_limit = 3
                baseline.cognition.failure_backoff_ticks = 3
                (examples / ('cc4-' + policy.replace('_', '-') + '.json')).write_text(baseline.model_dump_json(indent=2) + '\n', encoding='utf-8')
            tradeoff = baseline.model_copy(deep=True)
            tradeoff.cognition.scripted_policy = 'local_replan'
            tradeoff.name = "CC4 route tradeoffs under a deadline"
            preset = next(p for p in profile["complexity_presets"] if p["id"] == "route_tradeoffs")
            tradeoff.scenario.complexity = ComplexitySettings.model_validate(preset["complexity"])
            tradeoff.scenario.mission = MissionSettings(hold_ticks=5, deadline_tick=180)
            tradeoff.schedule.max_ticks = 240
            (examples / 'cc4-tradeoffs.json').write_text(tradeoff.model_dump_json(indent=2) + '\n', encoding='utf-8')
            tradeoff.name = 'CC4 observed search under route pressure'
            tradeoff.cognition.scripted_policy = 'local_search'
            tradeoff.cognition.action_retry_limit = 6
            tradeoff.cognition.failure_backoff_ticks = 8
            (examples / 'cc4-search-tradeoffs.json').write_text(tradeoff.model_dump_json(indent=2) + '\n', encoding='utf-8')


if __name__ == "__main__":
    main()
