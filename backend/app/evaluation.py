"""Metrics and matrix planning; importing or previewing never runs episodes."""
import copy
import itertools
import random
from statistics import mean
from backend.app.storage import digest
from packages.contracts.models import EpisodeConfig


def metrics(frames, cognition):
    actions = [a for f in frames[1:] for a in f["actions"] if a["proposal"]["action"] != "Sleep"]
    duplicate = 0
    for frame in frames[1:]:
        keys = [(a["proposal"]["action"], a["proposal"].get("target")) for a in frame["actions"] if a["proposal"]["action"] != "Sleep"]
        duplicate += len(keys) - len(set(keys))
    messages = frames[-1].get("messages", [])
    invalid = sum(not a["valid"] for a in actions)
    success_tick = next((f["tick"] for f in frames if f["score"]["mission_success"]), None)
    return {"formula_version": "1.0", "success": frames[-1]["score"]["mission_success"], "success_tick": success_tick, "time_to_success_censored": success_tick is None, "attempted_actions": len(actions), "invalid_actions": invalid, "invalid_rate": invalid / len(actions) if actions else None, "duplicate_actions": duplicate, "message_delivered": sum(m["status"] == "delivered" for m in messages), "message_dropped": sum(m["status"].startswith("dropped") or m["status"] == "expired" for m in messages), "message_pending": sum(m["status"] == "pending" for m in messages), **cognition}


def expand(spec):
    jobs = []
    dimensions = itertools.product(spec.architectures, spec.worker_counts, spec.world_seeds, spec.delays, spec.losses, range(spec.replicates))
    for architecture, workers, world_seed, delay, loss, replicate in dimensions:
        cfg = copy.deepcopy(spec.base.model_dump())
        cfg["purpose"] = "evaluation"
        cfg["team"].update(architecture=architecture, workers=workers)
        cfg["scenario"]["world_seed"] = world_seed
        cfg["communication"].update(extra_delay=delay, loss_probability=loss, seed=(spec.base.communication.seed + replicate) % 2**32)
        cfg["schedule"]["seed"] = (spec.base.schedule.seed + replicate) % 2**32
        cfg["name"] = f"{spec.name} · {architecture} · {world_seed} · {replicate}"
        config = EpisodeConfig.model_validate(cfg).model_dump()
        pair = {"world_seed": world_seed, "workers": workers, "delay": delay, "loss": loss, "replicate": replicate, "provider": cfg["cognition"]["provider"], "model": cfg["cognition"]["model"]}
        jobs.append({"job_id": digest({"config": config, "replicate": replicate})[:24], "pair_key": digest(pair), "replicate": replicate, "config": config})
    return {"name": spec.name, "job_count": len(jobs), "team_token_upper_bound": len(jobs) * spec.base.cognition.max_team_tokens if spec.base.cognition.provider != "scripted" else 0, "jobs": jobs, "warning": "Planning only. Legacy scenario calibration and pilot qualification are required before publication."}


def compare_runs(metadata, ids):
    selected = [m for m in metadata if m["id"] in set(ids)]
    if len(selected) != len(set(ids)):
        raise ValueError("Some selected runs do not exist")
    eligible, excluded = [], []
    for m in selected:
        if m["status"] != "completed" or m["manual_intervention"] or m["purpose"] != "evaluation" or m.get("metrics", {}).get("unknown_usage_calls", 0):
            excluded.append({"id": m["id"], "reason": "Requires completed, non-intervened evaluation with known usage"})
        else:
            eligible.append(m)
    # Treat repeated observations of the same technical world as a cluster.
    clusters = {}
    for m in eligible:
        clusters.setdefault((m["world_id"], m["condition_hash"]), {}).setdefault(m["architecture"], []).append(m)
    deltas = []
    for (world, condition), group in clusters.items():
        if "hierarchy" in group and "swarm" in group:
            a, b = group["hierarchy"], group["swarm"]
            if len(a) != len(b):
                excluded.extend({"id": m["id"], "reason": "Unbalanced replicate counts within paired world"} for m in a + b)
                continue
            deltas.append({"world_id": world, "condition_hash": condition, "success_difference": mean(int(m["metrics"]["success"]) for m in a) - mean(int(m["metrics"]["success"]) for m in b), "token_difference": mean(m["metrics"]["charged_tokens"] for m in a) - mean(m["metrics"]["charged_tokens"] for m in b), "replicates_per_mode": len(a)})
    # Cluster by underlying world across transport conditions; do not count
    # repeated conditions on one network as independent world samples.
    world_deltas = {}
    for d in deltas:
        world_deltas.setdefault(d["world_id"], []).append(d["success_difference"])
    values = [mean(v) for v in world_deltas.values()]
    estimate = mean(values) if values else None
    interval = None
    if len(values) >= 2:
        rng = random.Random(2026)
        samples = sorted(mean(rng.choices(values, k=len(values))) for _ in range(2000))
        interval = [samples[49], samples[1949]]
    return {"formula_version": "1.0", "direction": "hierarchy minus swarm", "paired_worlds": len(values), "paired_conditions": len(deltas), "success_difference": estimate, "world_cluster_bootstrap_95_ci": interval, "bootstrap_seed": 2026, "bootstrap_samples": 2000, "pairs": deltas, "excluded": excluded, "note": "Descriptive comparison only. Unpaired runs contribute no estimate; one world has no confidence interval. Success time is censored and not averaged here."}
