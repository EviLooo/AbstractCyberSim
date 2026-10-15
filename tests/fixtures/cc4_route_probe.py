"""Runs only under the isolated native interpreter, as a bounded software test."""
import json
import sys
from ipaddress import IPv4Address
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / ".engine/cc4/checkout"))
from CybORG.Simulator.Actions import Restore, ExploitRemoteService
from packages.engine_worker.cc4.runtime import EngineRuntime


def main():
    runtime = EngineRuntime()
    cfg = json.load(sys.stdin)
    initial = runtime.create(cfg)
    layers = initial["truth"]["route_manifest"]["layers"]
    gates = layers[-1]
    target = cfg["scenario"]["targets"][0]
    state = runtime.controller.state
    target_ip = state.hostname_ip_map[target]

    def finish(action, session=0, host=None):
        proposal = {"action": action, "session": session, "target": host}
        frame = runtime.step({"Red_0": proposal})
        for _ in range(8):
            if not frame["views"]["Red_0"]["pending_action"]:
                return frame
            frame = runtime.step({})
        raise AssertionError("Action did not complete")

    finish("DiscoverRemoteSystems", host=initial["views"]["Red_0"]["known"]["subnet"][0])
    upstream = 0
    for layer in layers[:-1]:
        gate = layer[0]
        finish("DiscoverNetworkServices", upstream, str(state.hostname_ip_map[gate]))
        finish("ExploitRemoteService", upstream, str(state.hostname_ip_map[gate]))
        finish("PrivilegeEscalate", upstream, gate)
        finish("EstablishPivot", upstream, gate)
        upstream = next(s.ident for s in runtime.sessions("Red_0").values() if s.hostname == gate)
    pivots = []
    for gate in gates:
        finish("DiscoverNetworkServices", upstream, str(state.hostname_ip_map[gate]))
        finish("ExploitRemoteService", upstream, str(state.hostname_ip_map[gate]))
        finish("PrivilegeEscalate", upstream, gate)
        frame = finish("EstablishPivot", upstream, gate)
        assert next(a for a in frame["actions"] if a["actor"] == "Red_0")["outcome"] == "TRUE"
        pivots.append(next(s.ident for s in runtime.sessions("Red_0").values() if s.hostname == gate))
    # White-box adversarial setup: even forged old scan cache does not bypass
    # stock CC4 ExploitRemoteService's source firewall check.
    runtime.sessions("Red_0")[0].ports[target_ip] = [22]
    stock = ExploitRemoteService(session=0, agent="red_agent_0", ip_address=IPv4Address(target_ip))
    assert str(stock.execute(state).data["success"]) == "FALSE"
    assert not any(s.hostname == target for s in runtime.sessions("Red_0").values())
    # A teammate cannot use the other actor's pivot ID or deploy without access.
    for proposal in [{"action": "DiscoverNetworkServices", "session": pivots[0], "target": str(target_ip)},
                     {"action": "EstablishPivot", "session": 0, "target": gates[0]}]:
        try:
            runtime.construct("Red_1", proposal)
        except ValueError:
            pass
        else:
            raise AssertionError("Unowned pivot accepted")
    assert next(a for a in finish("DiscoverNetworkServices", pivots[0], str(target_ip))["actions"] if a["actor"] == "Red_0")["outcome"] == "TRUE"
    blue = next(name for name, sessions in state.sessions.items() if name.startswith("blue_") and any(s.hostname == gates[0] for s in sessions.values()))
    # Schedule a normal five-tick native Restore. Test injection is deliberate;
    # the existing fresh-sensor policy is qualified in test_cc4_adapter.py.
    runtime.env.parallel_step(actions={blue: Restore(session=0, agent=blue, hostname=gates[0])})
    runtime.tick += 1
    runtime.score()
    for _ in range(4):
        frame = runtime.step({})
    assert pivots[0] not in runtime.sessions("Red_0")
    assert pivots[1] in runtime.sessions("Red_0")
    assert any(e["type"] == "defender_response_completed" and e["host"] == gates[0] for e in frame["defender_events"])
    denied = finish("DiscoverNetworkServices", pivots[0], str(target_ip))
    assert not next(a for a in denied["actions"] if a["actor"] == "Red_0")["valid"]
    alternate = finish("DiscoverNetworkServices", pivots[1], str(target_ip))
    assert next(a for a in alternate["actions"] if a["actor"] == "Red_0")["outcome"] == "TRUE"
    finish("DiscoverNetworkServices", upstream, str(state.hostname_ip_map[gates[0]]))
    finish("ExploitRemoteService", upstream, str(state.hostname_ip_map[gates[0]]))
    finish("PrivilegeEscalate", upstream, gates[0])
    recovered = finish("EstablishPivot", upstream, gates[0])
    assert next(a for a in recovered["actions"] if a["actor"] == "Red_0")["outcome"] == "TRUE"
    new_id = next(s.ident for s in runtime.sessions("Red_0").values() if s.hostname == gates[0])
    assert not runtime.sessions("Red_0")[new_id].ports
    assert runtime.snapshot()["route_manifest"] == initial["truth"]["route_manifest"]
    print(json.dumps({"native_block": True, "restored_pivot_removed": True, "alternate_route": True, "recovered_pivot": True}))


if __name__ == "__main__":
    main()
