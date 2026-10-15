"""Researcher-only, recomputable diagnostics; never imported by agent policies."""
from math import prod

VERSION = "1.0"


def structure(config, snapshot):
    if config.scenario.research:
        research = config.scenario.research
        return {'version':VERSION,'qualification':'research structure; difficulty and realism unmeasured',
            'recipe':research.recipe,'service_conditions':research.conditions,
            'initial_access':research.initial_access,'capability_coupling':research.capability_coupling,
            'target_count':len(config.scenario.targets),
            'simultaneous_admission_capacity':config.team.workers if config.schedule.mode=='per_worker' else 1,
            'observation_delay':research.evidence.observation_delay,
            'stale_after':research.evidence.stale_after,'change_mode':research.change.mode,
            'shared_response_budget':research.change.response_budget,
            'response_delay':research.change.response_delay,
            'mission_hold_ticks':config.scenario.mission.hold_ticks if config.scenario.mission else 1,
            'limits':['Finite recipe on fixed CC4 background; no hidden data is supplied to policies.',
                      'These controls are synthetic; counts do not establish difficulty or behavioral realism.']}
    routes = snapshot.get("route_manifest") or {}
    layers = routes.get("layers", []) if routes.get("enabled") else []
    beliefs = config.scenario.complexity.beliefs if config.scenario.complexity else None
    return {"version": VERSION, "qualification": "structural description; difficulty and realism unmeasured",
            "gateway_layers": len(layers), "gateway_widths": [len(layer) for layer in layers],
            "declared_gateway_combinations": prod(len(layer) for layer in layers) if layers else None,
            "hardened_dead_ends": len(routes.get("dead_ends", [])),
            "route_tradeoffs": routes.get("tradeoffs", {}).get("enabled", False),
            "gateway_templates": [r["template"] for r in routes.get("rules", []) if r.get("tradeoff")],
            "target_count": len(config.scenario.targets),
            "simultaneous_admission_capacity": config.team.workers if config.schedule.mode == "per_worker" else 1,
            "reactive_restore": config.scenario.defender == "reactive_restore",
            "observation_delay": beliefs.observation_delay if beliefs and beliefs.enabled else 0,
            "mission_hold_ticks": config.scenario.mission.hold_ticks if config.scenario.mission else 1,
            "limits": ["gateway counts do not prove difficulty", "service times and sensor rates are synthetic controls", "recovery solvability not inferred"]}


def reduce_decisions(frames):
    decisions = [d for frame in frames for d in frame.get("decisions", {}).values()]
    # Repeated IN_PROGRESS rows are continuations, not new completed actions.
    finished = [a for frame in frames[1:] for a in frame["actions"]
                if a["proposal"]["action"] != "Sleep" and a.get("remaining_ticks", 0) == 0
                and a.get("outcome") != "IN_PROGRESS"]
    assignment_keys, assignments = {}, 0
    claim_keys, claims = {}, 0
    sources, switches = {}, 0
    for frame in frames:
        for message in frame.get("messages", []):
            if message["status"] != "delivered" or message["id"] in assignment_keys or message["id"] in claim_keys:
                continue
            if message["kind"] == "assignment":
                assignment_keys[message["id"]] = True
                assignments += 1
            elif message["kind"] == "claim":
                claim_keys[message["id"]] = True
                claims += 1
        for action in frame.get("actions", []):
            if action["proposal"]["action"] == "Sleep" or not action.get("submitted", True):
                continue
            actor, source = action["actor"], action["proposal"].get("session", 0)
            switches += int(actor in sources and sources[actor] != source)
            sources[actor] = source
    return {"version": VERSION, "decision_count": len(decisions),
            "multiple_candidate_decisions": sum(d.get("candidate_count", 0) > 1 for d in decisions),
            "changed_state_decisions": sum(bool(d.get("state_change", {}).get("changed")) for d in decisions),
            "holding_decisions": sum(d.get("status") == "holding_own_goals" for d in decisions),
            "completed_failed_actions": sum(a.get("outcome") == "FALSE" for a in finished),
            "completed_service_scans": sum(a["proposal"]["action"] == "DiscoverNetworkServices" and a.get("outcome") == "TRUE" for a in finished),
            "source_switches": switches, "delivered_assignments": assignments, "delivered_claims": claims,
            "note": "Counts describe saved behavior; they do not prove reasoning, difficulty or LLM superiority."}
