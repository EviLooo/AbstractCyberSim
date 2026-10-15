"""Bounded software checks; truth addresses are test setup, never policy input."""
from packages.contracts.models import EpisodeConfig

TARGET_A = "restricted_zone_a_subnet_server_host_0"
TARGET_B = "operational_zone_a_subnet_server_host_0"


def config(variant="import_enabled", recipe="investigate", workers=2, architecture="independent", **settings):
    research = {"recipe": recipe, "condition_variant": variant, **settings}
    if recipe == "combine":
        research["capability_coupling"] = "bridge_and_token"
    return EpisodeConfig.model_validate({"schema_version": "2.0", "name": "Native research acceptance",
        "scenario": {"profile": "enterprise_cc4_research", "world_seed": 100,
            "targets": [TARGET_A, TARGET_B] if recipe == "combine" else [TARGET_A],
            "cc4": {"addon_services": 0}, "research": research},
        "team": {"workers": workers, "architecture": architecture},
        "cognition": {"scripted_policy": "evidence_controller"},
        "schedule": {"max_ticks": 180}}).model_dump()


async def finish(bridge, proposal, actor="Red_0"):
    result = await bridge.call("step", proposals={actor: proposal})
    for _ in range(8):
        if not result["views"][actor]["pending_action"]:
            return result
        result = await bridge.call("step", proposals={})
    raise AssertionError("Native action exceeded bounded continuation")


def ip(frame, hostname):
    host = next(h for h in frame["truth"]["hosts"] if h["id"] == hostname)
    return next(i["IP Address"] for i in host["interfaces"] if i["IP Address"] != "127.0.0.1")


def action(frame, actor="Red_0"):
    return next(a for a in frame["actions"] if a["actor"] == actor)


def evidence(frame, actor="Red_0"):
    return [e for fields in frame["observations"][actor]["data"].values() if isinstance(fields, dict)
            for e in fields.get("Research evidence", [])]
