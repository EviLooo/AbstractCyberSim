"""Bounded software qualification of real native ACLs and the pivot extension."""
import asyncio
import json
import pytest
import subprocess
from pathlib import Path
from backend.app.settings import engine_python

from backend.app.bridge import EngineBridge
from backend.app.knowledge import PrivateMemory
from backend.app.policies import candidates, key, Organization
from backend.app.runs import RunManager
from backend.app.storage import Store
from packages.contracts.complexity import ComplexitySettings, RouteSettings
from packages.contracts.models import EpisodeConfig
from packages.contracts.module_registry import compile_modules
from tests.test_cc4_adapter import config, address, finish


def routed(workers=1, depth=1, alternatives=2, dead=True):
    cfg = config(workers)
    cfg.scenario.complexity = ComplexitySettings(routes=RouteSettings(enabled=True,
        depth=depth, alternatives=alternatives, hardened_dead_end=dead))
    return cfg


def test_route_configuration_and_architecture_independent_compilation():
    cfg = routed()
    assert compile_modules(cfg)["modules"]["segmented_routes"]["enabled"]
    other = EpisodeConfig.model_validate(cfg.model_dump())
    other.team.architecture = "hierarchy"
    assert compile_modules(other) == compile_modules(cfg)
    for patch in [{"depth": 0}, {"depth": 4}, {"alternatives": 3}, {"arbitrary_gate": True}]:
        data = cfg.model_dump()
        data["scenario"]["complexity"]["routes"].update(patch)
        with pytest.raises(ValueError):
            EpisodeConfig.model_validate(data)
    data = cfg.model_dump()
    data["scenario"]["targets"] = ["contractor_network_subnet_server_host_0"]
    with pytest.raises(ValueError):
        EpisodeConfig.model_validate(data)


@pytest.mark.engine
@pytest.mark.parametrize("workers,depth,alternatives", [(1, 1, 1), (2, 2, 2), (4, 3, 2), (8, 1, 2)])
def test_native_segmented_paths_and_hardened_service(tmp_path, workers, depth, alternatives):
    async def check():
        bridge = EngineBridge(tmp_path / "engine.log", "enterprise_cc4")
        try:
            await bridge.start()
            initial = await bridge.call("create", config=routed(workers, depth, alternatives).model_dump())
            manifest = initial["truth"]["route_manifest"]
            actors = initial["actors"]
            assert len(manifest["layers"]) == depth
            assert all(len(layer) == alternatives for layer in manifest["layers"])
            assert all("route_manifest" not in v and v["pivot_enabled"] for v in initial["views"].values())
            frame = await finish(bridge, {a: {"action": "DiscoverRemoteSystems", "target": initial["views"][a]["known"]["subnet"][0]} for a in actors})
            sources = {a: 0 for a in actors}
            for level, layer in enumerate(manifest["layers"]):
                host = layer[0]
                ip = address(initial, host)
                dead_ip = address(initial, manifest["dead_ends"][level])
                for a in actors:
                    assert ip in frame["views"][a]["known"]["ip_address"]
                # Same SSH port, different account vulnerability. Failure comes
                # from native SSHBruteForce, not a magic scenario gate.
                await finish(bridge, {a: {"action": "DiscoverNetworkServices", "session": sources[a], "target": dead_ip} for a in actors})
                frame = await finish(bridge, {a: {"action": "ExploitRemoteService", "session": sources[a], "target": dead_ip} for a in actors})
                assert all(r["outcome"] == "FALSE" for r in frame["actions"])
                await finish(bridge, {a: {"action": "DiscoverNetworkServices", "session": sources[a], "target": ip} for a in actors})
                frame = await finish(bridge, {a: {"action": "ExploitRemoteService", "session": sources[a], "target": ip} for a in actors})
                assert all(r["outcome"] == "TRUE" for r in frame["actions"])
                rejected = await finish(bridge, {a: {"action": "EstablishPivot", "session": sources[a], "target": host} for a in actors})
                assert all(not r["valid"] for r in rejected["actions"])
                frame = await finish(bridge, {a: {"action": "PrivilegeEscalate", "session": sources[a], "target": host} for a in actors})
                assert all(r["outcome"] == "TRUE" for r in frame["actions"])
                next_host = manifest["layers"][level + 1][0] if level + 1 < depth else routed().scenario.targets[0]
                next_ip = address(initial, next_host)
                assert all(next_ip in frame["views"][a]["known"]["ip_address"] for a in actors)
                blocked = await finish(bridge, {a: {"action": "DiscoverNetworkServices", "session": sources[a], "target": next_ip} for a in actors})
                assert all(r["valid"] and r["outcome"] == "FALSE" for r in blocked["actions"])
                assert all(next_ip not in blocked["views"][a]["scan_cache"][str(sources[a])] for a in actors)
                frame = await finish(bridge, {a: {"action": "EstablishPivot", "session": sources[a], "target": host} for a in actors})
                assert all(r["outcome"] == "TRUE" and r["duration"] == 2 for r in frame["actions"])
                for a in actors:
                    pivot = next(s for s in frame["views"][a]["sessions"] if s["hostname"] == host)
                    assert pivot["privileged"] and pivot["controller"]
                    sources[a] = pivot["id"]
                    assert frame["views"][a]["scan_cache"][str(pivot["id"])] == {}
            target = routed().scenario.targets[0]
            ip = address(initial, target)
            await finish(bridge, {a: {"action": "DiscoverNetworkServices", "session": sources[a], "target": ip} for a in actors})
            frame = await finish(bridge, {a: {"action": "ExploitRemoteService", "session": sources[a], "target": ip} for a in actors})
            frame = await finish(bridge, {a: {"action": "PrivilegeEscalate", "session": sources[a], "target": target} for a in actors})
            assert frame["score"]["mission_success"]
            assert frame["tick"] < 100
            (tmp_path / "acceptance.json").write_text(json.dumps(frame, indent=2))
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
def test_route_materialization_reset_seed_and_no_op(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / "engine.log", "enterprise_cc4")
        try:
            await bridge.start()
            native = await bridge.call("create", config=config().model_dump())
            disabled = config()
            disabled.scenario.complexity = ComplexitySettings()
            same = await bridge.call("create", config=disabled.model_dump())
            assert native["world"] == same["world"]
            cfg = routed(2, 3)
            first = await bridge.call("create", config=cfg.model_dump())
            assert first["world"] == (await bridge.call("create", config=cfg.model_dump()))["world"]
            cfg.team.architecture = "hierarchy"
            assert first["world"] == (await bridge.call("create", config=cfg.model_dump()))["world"]
            cfg.scenario.world_seed += 1
            other = await bridge.call("create", config=cfg.model_dump())
            assert first["truth"]["route_manifest"]["rules"] != other["truth"]["route_manifest"]["rules"]
            assert first["truth"]["blocks"] != other["truth"]["blocks"]
        finally:
            await bridge.close()
    asyncio.run(check())


def test_source_candidates_and_coordinator_preserve_owned_pivot():
    mem = PrivateMemory("Red_0")
    mem.view = {"pivot_enabled": True, "sessions": [
        {"id": sid, "hostname": f"h{sid}", "active": True, "controller": True, "privileged": True} for sid in (0, 2)],
        "scan_cache": {"0": {}, "2": {"10.0.0.4": [22]}},
        "known": {"ip_address": ["10.0.0.4"], "hostname": [], "subnet": []}}
    opts = candidates(mem)
    exploit = next(p for p in opts if p["action"] == "ExploitRemoteService")
    assert exploit["session"] == 2
    assert key(exploit) != key(dict(exploit, session=0))
    mem.history.append({"proposal": dict(exploit, session=0), "valid": True, "outcome": "FALSE"})
    assert exploit in candidates(mem)
    org = Organization(routed(1), ["Red_0"])
    org.coordinator_view([{"sender": "Red_0", "kind": "report", "evidence_ids": [], "payload": {"sessions": mem.view["sessions"], "candidates": [exploit]}}], 1)
    assert org.scripted_assignments()["Red_0"]["proposal"]["session"] == 2


@pytest.mark.engine
def test_native_restore_invalidates_source_alternative_and_recovery():
    result = subprocess.run([engine_python("enterprise_cc4"), str(Path(__file__).parent / "fixtures/cc4_route_probe.py")],
        input=routed(2, 2, 2).model_dump_json(), text=True, capture_output=True, timeout=45)
    assert result.returncode == 0, result.stderr
    assert all(json.loads(result.stdout.splitlines()[-1]).values())


@pytest.mark.engine
@pytest.mark.parametrize("architecture", ["hierarchy", "swarm", "independent"])
def test_route_organization_pipeline_without_truth_or_models(tmp_path, architecture):
    async def check():
        manager = RunManager(Store(tmp_path))
        try:
            cfg = routed(2, 1, 2, False)
            cfg.team.architecture = architecture
            cfg.scenario.complexity.beliefs.enabled = True
            cfg.scenario.complexity.beliefs.stale_after = 1000
            run = manager.get((await manager.create(cfg))["id"])
            for _ in range(180):
                if run.meta["status"] in {"completed", "errored"}:
                    break
                await run.advance()
            assert run.meta["termination_reason"] == "mission_success", run.meta
            assert not run.meta["manual_intervention"] and run.cognition.calls == 0
            assert any(a["proposal"]["action"] == "EstablishPivot" and a["outcome"] == "TRUE" for f in run.frames for a in f["actions"])
            target_ip = address(run.frames[0], cfg.scenario.targets[0])
            assert any(a["proposal"]["action"] == "ExploitRemoteService" and a["proposal"]["target"] == target_ip and a["proposal"]["session"] > 0 and a["outcome"] == "TRUE" for f in run.frames for a in f["actions"])
            assert manager.store.frame(run.id)["truth"]["route_manifest"]["enabled"]
            assert run.engine.process is None
        finally:
            await manager.close()
    asyncio.run(check())


def test_route_access_loss_retries_and_scan_age_are_source_local():
    from packages.contracts.complexity import BeliefSettings
    mem = PrivateMemory("Red_0", BeliefSettings(enabled=True, stale_after=5))
    source = {"actor": "Red_0", "pivot_enabled": True, "sessions": [
        {"id": sid, "hostname": f"h{sid}", "active": True, "controller": True, "privileged": True} for sid in (0, 2)],
        "scan_cache": {"0": {"10.0.0.4": [22]}, "2": {"10.0.0.4": [22]}},
        "known": {"ip_address": ["10.0.0.4"], "hostname": [], "subnet": []}}
    mem.observe({"actor": "Red_0", "tick": 10, "evidence_id": "self", "data": {}}, source)
    mem.scan_ticks = {"10.0.0.4": 1, "2:10.0.0.4": 10}
    assert any(p["action"] == "DiscoverNetworkServices" and p["session"] == 0 for p in candidates(mem))
    assert not any(p["action"] == "DiscoverNetworkServices" and p["session"] == 2 for p in candidates(mem))
    raw = PrivateMemory("Red_0")
    raw.observe({"tick": 0, "evidence_id": "initial", "data": {}}, source)
    p = {"action": "ExploitRemoteService", "target": "10.0.0.4", "session": 0}
    raw.history = [{"proposal": p, "outcome": "TRUE", "valid": True, "belief_epoch": 0}]
    assert not any(key(p) == key(c) for c in candidates(raw))
    source["sessions"] = source["sessions"][:1]
    source["scan_cache"].pop("2")
    raw.observe({"tick": 1, "evidence_id": "loss", "data": {}}, source)
    assert raw.epoch == 1 and any(key(p) == key(c) for c in candidates(raw))
