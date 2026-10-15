"""Metrics and matrix planning; importing or previewing never runs episodes."""
import copy
import itertools
import random
from statistics import mean
from backend.app.storage import digest
from packages.contracts.models import EpisodeConfig


def metrics(frames, cognition, horizon=None, termination_reason=None):
    actions = [a for f in frames[1:] for a in f["actions"] if a["proposal"]["action"] != "Sleep" and a.get("submitted", True)]
    duplicate = 0
    for frame in frames[1:]:
        keys = [(a["proposal"]["action"], a["proposal"].get("target")) for a in frame["actions"] if a["proposal"]["action"] != "Sleep" and a.get("submitted", True)]
        duplicate += len(keys) - len(set(keys))
    messages = frames[-1].get("messages", [])
    invalid = sum(not a["valid"] for a in actions)
    success_tick = next((f["tick"] for f in frames if f["score"]["mission_success"]), None)
    result = {"formula_version": "1.0", "success": frames[-1]["score"]["mission_success"], "success_tick": success_tick, "time_to_success_censored": success_tick is None, "attempted_actions": len(actions), "invalid_actions": invalid, "invalid_rate": invalid / len(actions) if actions else None, "duplicate_actions": duplicate, "message_delivered": sum(m["status"] == "delivered" for m in messages), "message_dropped": sum(m["status"].startswith("dropped") or m["status"] == "expired" for m in messages), "message_pending": sum(m["status"] == "pending" for m in messages), **cognition}
    mission = frames[-1]["score"].get("mission")
    if mission:
        result.update(mission_formula_version="1.0", mission_hold_ticks=mission["hold_ticks"],
            mission_best_hold_ticks=mission["best_hold_ticks"], mission_resets=mission["reset_count"],
            objective_resets=sum(o["reset_count"] for o in mission["objectives"]),
            mission_deadline_tick=mission["deadline_tick"], mission_failure=mission["failure"])
    behavior = frames[-1].get("diagnostics", {}).get("behavior")
    if behavior:
        result.update(decision_formula_version=behavior["version"],
            multiple_candidate_decisions=behavior["multiple_candidate_decisions"],
            changed_state_decisions=behavior["changed_state_decisions"],
            completed_failed_actions=behavior["completed_failed_actions"],
            source_switches=behavior["source_switches"])
    if frames[-1].get('engine_profile') == 'enterprise_cc4_research':
        from backend.app.research_metrics import reduce_research
        result.update(reduce_research(frames, horizon, termination_reason))
    return result



def expand(spec):
    jobs = []
    dimensions = itertools.product(spec.architectures, spec.worker_counts, spec.world_seeds, spec.delays, spec.losses, range(spec.replicates))
    for architecture, workers, world_seed, delay, loss, replicate in dimensions:
        # Pydantic defaults and JSON validation can represent zero as int/float.
        # Pair identity must be independent of whether a spec passed through HTTP.
        loss = float(loss)
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
    research = [m.get('profile')=='enterprise_cc4_research' for m in selected]
    if any(research):
        if not all(research):
            raise ValueError('Compare a single profile at a time; action catalogs and metrics differ')
        return compare_research(selected)
    eligible, excluded = [], []
    for m in selected:
        if m["status"] != "completed" or m["manual_intervention"] or m["purpose"] != "evaluation" or m.get("metrics", {}).get("unknown_usage_calls", 0):
            excluded.append({"id": m["id"], "reason": "Requires completed, non-intervened evaluation with known usage"})
        elif m.get('profile')=='enterprise_cc4_research' and (not m.get('freeze_id') or m.get('feasibility_status')!='native_witness_validated'):
            excluded.append({'id':m['id'],'reason':'Research comparison requires a frozen study and a validated native world; software checks are not study results'})
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


def compare_research(selected):
    """Failure-aware primary organization contrast; causal worlds are clusters."""
    from collections import Counter
    eligible, excluded, groups = [], [], {}
    for meta in selected:
        reason = None
        if not meta.get('freeze_id') or meta.get('freeze_purpose')!='proposed_study' or meta.get('feasibility_status')!='native_witness_validated':
            reason = 'Requires a frozen proposed study and validated native world; software checks are not study results'
        elif meta['status']!='completed' or meta['manual_intervention'] or meta['purpose']!='evaluation':
            reason = 'Requires terminal non-intervened evaluation; technical/interrupted episodes are separate'
        elif meta.get('metrics',{}).get('unknown_usage_calls'):
            reason = 'Unknown model usage; retained as an excluded outcome, never recorded as free'
        elif meta.get('metrics',{}).get('research_formula_version') != 'research_metrics_v1.1':
            reason = 'Missing or incompatible research metric formula; reproduce with the frozen source, do not mix versions'
        elif not meta.get('causal_world_hash') or not meta.get('pair_key') or not meta.get('condition_hash'):
            reason = 'Missing frozen pairing or causal-world identity'
        if reason:
            excluded.append({'id':meta['id'],'reason':reason,'outcome':meta.get('termination_reason')})
        else:
            eligible.append(meta)
            key = (meta['freeze_id'],meta['split'],meta['causal_world_hash'],meta['condition_hash'],meta['pair_key'])
            groups.setdefault(key,{}).setdefault(meta['architecture'],[]).append(meta)
    pairs, paired_ids = [], set()
    if len({(m['freeze_id'],m['split']) for m in eligible})>1:
        raise ValueError('Compare one frozen study split at a time')
    for key, modes in groups.items():
        a,b = modes.get('hierarchy',[]),modes.get('swarm',[])
        if len(a)!=1 or len(b)!=1:
            continue
        left,right = a[0],b[0]
        paired_ids.update((left['id'],right['id']))
        lm,rm = left['metrics'],right['metrics']
        pair = {'freeze_id':key[0],'split':key[1],'causal_world_hash':key[2],'condition_hash':key[3],
                'pair_key':key[4],'run_ids':[left['id'],right['id']],
                'success_difference':int(lm['success'])-int(rm['success']),
                'token_difference':lm['charged_tokens']-rm['charged_tokens']}
        lh,rh = lm.get('declared_horizon'),rm.get('declared_horizon')
        pair['restricted_completion_difference'] = lm['restricted_completion_ticks']-rm['restricted_completion_ticks'] if lh==rh and lm.get('restricted_completion_ticks') is not None and rm.get('restricted_completion_ticks') is not None else None
        pairs.append(pair)
    unpaired = [{'id':m['id'],'reason':'No unique matching hierarchy/swarm observation; duplicate selections and other controls contribute no primary estimate'} for m in eligible if m['id'] not in paired_ids]
    worlds = {}
    for pair in pairs:
        worlds.setdefault(pair['causal_world_hash'],[]).append(pair)
    estimates = {}
    for metric in ('success_difference','token_difference','restricted_completion_difference'):
        values = [mean(p[metric] for p in cluster if p[metric] is not None) for cluster in worlds.values() if any(p[metric] is not None for p in cluster)]
        interval = None
        if len(values)>=2:
            rng = random.Random(2026)
            samples = sorted(mean(rng.choices(values,k=len(values))) for _ in range(2000))
            interval = [samples[49],samples[1949]]
        estimates[metric] = {'estimate':mean(values) if values else None,'world_cluster_bootstrap_95_ci':interval,'worlds':len(values)}
    return {'formula_version':'research_comparison_v1','direction':'hierarchy minus swarm',
            'selected_episodes':len(selected),'eligible_episodes':len(eligible),'paired_episodes':len(paired_ids),
            'paired_worlds':len(worlds),'paired_conditions':len(pairs),
            'success_difference':estimates['success_difference']['estimate'],
            'world_cluster_bootstrap_95_ci':estimates['success_difference']['world_cluster_bootstrap_95_ci'],
            'estimates':estimates,'outcome_counts':dict(Counter(m.get('termination_reason') or 'unknown' for m in selected)),
            'pairs':pairs,'excluded':excluded,'unpaired':unpaired,'bootstrap_seed':2026,'bootstrap_samples':2000,
            'note':'Descriptive only; causal combinations on the fixed scaffold are conservative clusters. Failures retain their horizon time; no success-only time average. Counts include every selected outcome.'}
