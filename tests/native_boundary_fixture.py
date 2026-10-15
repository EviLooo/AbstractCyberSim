"""Python 3.8-only fixture runner; privileged setup is never exposed by the API.

The parent pytest process supplies the normal resolved config on stdin. Each
case creates a fresh native world. Setup mutations isolate prerequisites; these
are test interventions, not legal agent decisions or research scenarios.
"""
import contextlib
import json
import sys

from packages.engine_worker.runtime import EngineRuntime


def fresh(config):
    runtime = EngineRuntime()
    runtime.create(config)
    return runtime, runtime.env.environment_controller.state


def address(state, hostname):
    return next(ip for ip, name in state.ip_addresses.items() if name == hostname)


def reveal(runtime, actor, ip):
    # Explicit fixture knowledge injection, not the production evidence bridge.
    runtime.env.environment_controller.agent_interfaces[actor].update({str(ip): {"Interface": [{"IP Address": ip}]}})


def act(runtime, actor, action, target=None, session=0):
    p = {"action": action, "session": session}
    if target is not None:
        p["target"] = str(target)
    frame = runtime.step({actor: p})
    return frame, next(a for a in frame["actions"] if a["actor"] == actor)


def acquire(runtime, actor, ip):
    reveal(runtime, actor, ip)
    _, scan = act(runtime, actor, "DiscoverNetworkServices", ip)
    assert scan["valid"] and scan["outcome"] == "TRUE", scan
    for _ in range(2):
        frame, exploit = act(runtime, actor, "ExploitRemoteService", ip)
        if exploit["outcome"] == "TRUE":
            return frame
    raise AssertionError(exploit)


def check(config):
    results = []
    runtime, state = fresh(config)
    target = address(state, "User1")
    reveal(runtime, "Red_0", target)
    frame, record = act(runtime, "Red_0", "DiscoverNetworkServices", target, session=999)
    assert not record["valid"] and record["outcome"] == "UNKNOWN"
    assert frame["score"]["controlled_hosts"] == ["User0"]
    results.append("missing_session_rejected")
    frame = acquire(runtime, "Red_0", target)
    own = next(s for s in frame["views"]["Red_0"]["sessions"] if s["hostname"] == "User1")
    assert not own["privileged"]
    assert not frame["score"]["mission_success"]
    results.append("unprivileged_target_does_not_satisfy_mission")
    # Numeric IDs are actor-relative; an ID present in Red_0 cannot be used by
    # Red_1 if Red_1 has not acquired its own session with that ID.
    for actor in ["Red_0", "Red_1"]:
        _, record = act(runtime, actor, "DiscoverNetworkServices", target, session=own["id"])
        assert not record["valid"] and "actor-owned controlling" in record["rejection"]
    results.append("peer_and_reverse_shell_cannot_be_used_as_controller")
    reveal(runtime, "Red_1", target)
    _, record = act(runtime, "Red_1", "PrivilegeEscalate", "User1")
    assert not record["valid"] and "owned session" in record["rejection"]
    results.append("peer_foothold_does_not_grant_escalation")
    frame, record = act(runtime, "Red_0", "PrivilegeEscalate", "User1")
    assert record["outcome"] == "TRUE" and frame["score"]["mission_success"]
    assert frame["score"]["targets_reached"] == 1
    state.sessions["Red_0"][own["id"]].active = False
    assert not runtime.score()["mission_success"]
    _, record = act(runtime, "Red_0", "PrivilegeEscalate", "User1")
    assert not record["valid"]
    results.append("inactive_target_session_cannot_satisfy_mission_or_escalate")
    state.sessions["Red_0"][0].active = False
    _, record = act(runtime, "Red_0", "DiscoverNetworkServices", target)
    assert not record["valid"]
    results.append("inactive_controller_rejected")
    tick = runtime.tick
    try:
        runtime.step({"Blue": {"action": "Sleep"}})
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown actor binding accepted")
    assert runtime.tick == tick
    results.append("unknown_actor_cannot_advance_world")

    runtime, state = fresh(config)
    target = address(state, "User1")
    reveal(runtime, "Red_0", target)
    state.link_diagram.remove_edges_from(list(state.link_diagram.edges("User1")))
    frame, record = act(runtime, "Red_0", "DiscoverNetworkServices", target)
    assert record["valid"] and record["outcome"] == "FALSE", record
    assert str(target) not in frame["views"]["Red_0"]["scan_cache"]["0"]
    results.append("disconnected_scan_fails_without_cache_or_crash")
    # Obtain the cache before disconnecting to isolate exploit reachability.
    runtime, state = fresh(config)
    target = address(state, "User1")
    reveal(runtime, "Red_0", target)
    act(runtime, "Red_0", "DiscoverNetworkServices", target)
    state.link_diagram.remove_edges_from(list(state.link_diagram.edges("User1")))
    frame, record = act(runtime, "Red_0", "ExploitRemoteService", target)
    assert record["valid"] and record["outcome"] == "FALSE", record
    assert len(frame["views"]["Red_0"]["sessions"]) == 1
    results.append("disconnected_exploit_fails_without_session_or_crash")

    runtime, state = fresh(config)
    operational = address(state, "Op_Server0")
    for actor in runtime.actors:
        reveal(runtime, actor, operational)
    _, denied = act(runtime, "Red_0", "DiscoverNetworkServices", operational)
    assert denied["valid"] and denied["outcome"] == "FALSE", denied
    acquire(runtime, "Red_1", address(state, "Enterprise1"))
    _, still_denied = act(runtime, "Red_0", "DiscoverNetworkServices", operational)
    _, allowed = act(runtime, "Red_1", "DiscoverNetworkServices", operational)
    assert still_denied["valid"] and still_denied["outcome"] == "FALSE"
    assert allowed["valid"] and allowed["outcome"] == "TRUE", allowed
    results.append("legacy_operational_gate_requires_own_enterprise_foothold")
    return results


if __name__ == "__main__":
    config = json.loads(sys.stdin.read())
    with contextlib.redirect_stdout(sys.stderr):
        result = check(config)
    print(json.dumps({"checks": result}))
