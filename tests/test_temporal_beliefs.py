"""Bounded software acceptance, not research experiments or model comparisons."""
import asyncio
import copy
import json
import pytest
from pydantic import ValidationError
from backend.app.beliefs import BeliefLedger, perceived_action
from backend.app.knowledge import PrivateMemory
from backend.app.policies import Organization, candidates, key
from backend.app.runs import RunManager
from backend.app.storage import Store
from packages.contracts.complexity import BeliefSettings, ComplexitySettings
from packages.contracts.models import EpisodeConfig
from packages.contracts.module_registry import compile_modules
from tests.test_cc4_adapter import config, address
from backend.app.bridge import EngineBridge


def view():
    return {"actor": "Red_0", "known": {"hostname": ["entry"], "ip_address": ["10.0.0.1"], "subnet": ["10.0.0.0/24"]},
        "scan_cache": {"0": {}}, "pending_action": None,
        "sessions": [{"id": 0, "hostname": "entry", "active": True, "controller": True, "privileged": True, "username": "root"}]}


def delta(tick, data=None):
    return {"actor": "Red_0", "tick": tick, "evidence_id": f"Red_0:{tick}:{tick}", "data": data or {}}


def enabled(delay=0, age=8):
    return ComplexitySettings(beliefs=BeliefSettings(enabled=True, observation_delay=delay, stale_after=age))


def test_module_contract_compiler_and_unsupported_combinations():
    cfg = config()
    cfg.scenario.complexity = enabled(2)
    compiled = compile_modules(cfg)
    restored = EpisodeConfig.model_validate_json(cfg.model_dump_json())
    assert compile_modules(restored) == compiled
    restored.team.architecture = "hierarchy"
    assert compile_modules(restored) == compiled
    assert compiled["modules"]["temporal_beliefs"]["observation_delay"] == 2
    assert compiled["seed_namespaces"]["world"] == cfg.scenario.world_seed
    for bad in [
        {"version": "2.0"}, {"patching": {"enabled": True}},
        {"beliefs": {"observation_delay": 21}}, {"beliefs": {"stale_after": 0}},
    ]:
        with pytest.raises(ValidationError):
            EpisodeConfig.model_validate({**cfg.model_dump(), "scenario": {**cfg.scenario.model_dump(), "complexity": bad}})
    with pytest.raises(ValidationError):
        EpisodeConfig.model_validate({"scenario": {"complexity": enabled().model_dump()}})


def test_evidence_age_conflicts_out_of_order_history_and_report_time():
    ledger = BeliefLedger(4)
    ledger.add("known", {"Services": [80]}, "self:2", "Red_0", 2, 2, "self_observed")
    ledger.add("known", {"Services": [443]}, "self:5", "Red_0", 5, 7, "self_observed")
    ledger.add("known", {"Services": [80]}, "old:1", "Red_0", 1, 8, "self_observed")
    ledger.add("known", {"Services": [22]}, "peer:3", "Red_1", 3, 8, "verified_peer_report")
    current = ledger.snapshot(9)
    own, peer = current["records"]
    assert own["value"] == [443] and own["contradicts"] == "self:2"
    assert own["age"] == 4 and own["stale"] and own["conflict"]
    assert peer["observed_tick"] == 3 and peer["received_tick"] == 8
    assert peer["confirmation"] == "unconfirmed_report" and peer["age"] == 6
    assert len(current["history"]) == 4
    current["records"][0]["value"].append(123)
    assert ledger.snapshot(9)["records"][0]["value"] == [443]


def test_observation_delay_hides_knowledge_caches_and_intel_view_backdoor():
    memory = PrivateMemory("Red_0", enabled(2).beliefs)
    initial = view()
    memory.observe(delta(0, {"10.0.0.1": {"Interface": [{"IP Address": "10.0.0.1"}]}}), initial)
    future = copy.deepcopy(initial)
    future["known"]["ip_address"].append("10.0.0.2")
    future["scan_cache"]["0"]["10.0.0.2"] = [22]
    memory.observe(delta(1, {"10.0.0.2": {"Processes": [{"local_port": 22}]}}), future)
    assert "10.0.0.2" not in json.dumps(memory.public_view({}, {}))
    memory.accept_intel_view({"view": future, "address_fragment": {"10.0.0.3": {"Interface": [{"IP Address": "10.0.0.3"}]}}})
    assert "10.0.0.3" in memory.view["known"]["ip_address"]
    assert "10.0.0.2" not in memory.view["known"]["ip_address"]
    memory.observe(delta(2), future)
    assert "10.0.0.2" not in memory.view["known"]["ip_address"]
    memory.observe(delta(3), future)
    assert "10.0.0.2" in memory.view["known"]["ip_address"]
    assert memory.view["scan_cache"]["0"]["10.0.0.2"] == [22]
    record = next(r for r in memory.public_view({}, {})["beliefs"]["records"] if r["host"] == "10.0.0.2")
    assert record["observed_tick"] == 1 and record["received_tick"] == 3


def test_disabled_module_preserves_native_memory_semantics():
    plain = PrivateMemory("Red_0")
    disabled = PrivateMemory("Red_0", BeliefSettings(enabled=False, observation_delay=20, stale_after=1))
    for tick in range(3):
        for memory in [plain, disabled]:
            memory.observe(delta(tick, {"10.0.0.1": {"Interface": [{"IP Address": str(tick)}]}}), view())
    assert plain.public_view({}, {}) == disabled.public_view({}, {})
    assert "beliefs" not in disabled.public_view({}, {})


def test_access_loss_replanning_and_delayed_reports_never_grant_access():
    memory = PrivateMemory("Red_0", enabled(age=4).beliefs)
    initial = view()
    initial["known"]["ip_address"].append("10.0.0.2")
    initial["scan_cache"]["0"]["10.0.0.2"] = [22]
    initial["sessions"].append({"id": 1, "hostname": "remote", "active": True, "controller": False, "privileged": False, "username": "user"})
    memory.observe(delta(0, {"10.0.0.2": {"System info": {"Hostname": "remote"}, "Services": [22]}}), initial)
    action = {"proposal": {"action": "ExploitRemoteService", "target": "10.0.0.2"}, "outcome": "TRUE", "valid": True, "belief_epoch": 0}
    memory.history.append(action)
    memory.scan_ticks["10.0.0.2"] = 0
    changed = copy.deepcopy(initial)
    changed["sessions"] = changed["sessions"][:1]
    memory.observe(delta(1), changed)
    assert memory.epoch == 1 and memory.ledger.events[-1]["type"] == "access_lost"
    assert any(p["action"] == "ExploitRemoteService" for p in candidates(memory))
    memory.report({"10.0.0.2": {"System info": {"Hostname": "remote"}}}, ["Red_1:0:5"], "Red_1", 4,
        [{"evidence_id": "Red_1:0:5", "tick": 0, "data": {"10.0.0.2": {"System info": {"Hostname": "remote"}}}}])
    assert len(memory.view["sessions"]) == 1
    memory.advance_clock(5)
    assert any(p["action"] == "DiscoverNetworkServices" and p["target"] == "10.0.0.2" for p in candidates(memory))
    assert any(p["action"] == "ExploitRemoteService" for p in candidates(memory))
    organization = Organization(config(1, "hierarchy"), ["Red_0"])
    refresh = next(p for p in candidates(memory) if p["action"] == "DiscoverNetworkServices")
    organization.finished.add("Red_0:" + key(refresh))
    organization.reports = {"Red_0": {"sender": "Red_0", "evidence_ids": [], "payload": {"candidates": [refresh], "sessions": changed["sessions"], "belief_epoch": 1}}}
    assert organization.scripted_assignments()["Red_0"]["proposal"]["action"] == "DiscoverNetworkServices"
    # Aged scans remain a legal choice for both LLM organizations. The
    # hierarchy gateway must not silently remove a tool available to swarm.
    risky = next(p for p in candidates(memory) if p["action"] == "ExploitRemoteService")
    memory.inbox.append({"kind": "assignment", "created_tick": 5, "payload": {"proposal": risky}})
    assert organization.preferred(memory, 5)["action"] == "ExploitRemoteService"
    assert memory.hosts["10.0.0.2"]["fields"]["Services"] == [22]
    memory.observe(delta(6), initial)
    assert memory.ledger.events[-1]["type"] == "access_recovered"
    assert "defender" not in json.dumps(memory.public_view({}, {}))


def test_action_status_cannot_leak_delayed_addresses_or_ports():
    record = {"outcome": "TRUE", "state_delta": {"knowledge_added": {"ip_address": ["hidden"]}, "scan_cache_updates": {"0": {"hidden": [443]}}, "sessions_lost": []}}
    assert perceived_action(record) == {"outcome": "TRUE", "state_delta": {"sessions_lost": []}}
    assert "hidden" in json.dumps(record)


@pytest.mark.engine
def test_module_initialization_is_noop_for_physical_world_and_resets_memory(tmp_path):
    async def check():
        manager = RunManager(Store(tmp_path))
        try:
            cfg = config(2)
            baseline = manager.get((await manager.create(cfg))["id"])
            cfg.scenario.complexity = ComplexitySettings(beliefs=BeliefSettings(enabled=False, observation_delay=20, stale_after=1))
            disabled = manager.get((await manager.create(cfg))["id"])
            assert disabled.frames[0]["truth"] == baseline.frames[0]["truth"]
            assert disabled.meta["world_id"] == baseline.meta["world_id"]
            assert disabled.frames[0]["private_views"] == baseline.frames[0]["private_views"]
            cfg.scenario.complexity = enabled(2)
            cfg.team.architecture = "swarm"
            temporal = manager.get((await manager.create(cfg))["id"])
            assert temporal.meta["world_id"] == baseline.meta["world_id"]
            assert temporal.frames[0]["truth"] == baseline.frames[0]["truth"]
            assert temporal.memory["Red_0"].channel.pending == []
            assert temporal.memory["Red_0"].ledger.events == []
            assert temporal.meta["tick"] == 0 and temporal.cognition.calls == 0
        finally:
            await manager.close()
    asyncio.run(check())


def test_api_module_presets_round_trip_and_unsupported_rejection(tmp_path):
    import httpx
    from backend.app.api import create_app
    async def check():
        app = create_app(tmp_path)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                capabilities = (await client.get("/api/capabilities")).json()
                cc4 = next(p for p in capabilities["profiles"] if p["id"] == "enterprise_cc4")
                assert any(m["id"] == "temporal_beliefs" for m in cc4["complexity_modules"])
                recipe = copy.deepcopy(cc4["default_config"])
                preset = next(p for p in cc4["complexity_presets"] if p["id"] == "observed_recovery")
                recipe["scenario"].update(complexity=copy.deepcopy(preset["complexity"]), defender=preset["defender"])
                valid = await client.post("/api/configs/validate", json=recipe)
                assert valid.status_code == 200 and valid.json() == recipe
                recipe["scenario"]["complexity"]["patching"] = {"enabled": True}
                assert (await client.post("/api/runs", json=recipe)).status_code == 422
                assert not app.state.manager.live
                assert (await client.get("/api/capabilities")).json()["profiles"] == capabilities["profiles"]
        finally:
            await app.state.manager.close()
    asyncio.run(check())


@pytest.mark.engine
@pytest.mark.parametrize("workers", [1, 2, 4, 8])
def test_native_delay_privacy_refresh_and_replay_manifest(tmp_path, workers):
    async def check():
        cfg = config(workers)
        cfg.scenario.complexity = enabled(2, 4)
        manager = RunManager(Store(tmp_path))
        try:
            meta = await manager.create(cfg)
            run = manager.get(meta["id"])
            target = address(run.frames[0], "contractor_network_subnet_server_host_0")
            subnet = run.memory["Red_0"].view["known"]["subnet"][0]
            async def step(proposal=None):
                overrides = {a: {"action": "Sleep"} for a in run.actors if not run.memory[a].view.get("pending_action")}
                if proposal:
                    overrides["Red_0"] = proposal
                await run.advance(overrides)
            await step({"action": "DiscoverRemoteSystems", "target": subnet})
            assert target in run.frames[-1]["views"]["Red_0"]["known"]["ip_address"]
            assert target not in run.memory["Red_0"].view["known"]["ip_address"]
            assert not any(eid.startswith("Red_0:1:") for eid in run.memory["Red_0"].evidence_ids())
            await step({"action": "DiscoverNetworkServices", "target": target})
            assert not next(r for r in run.frames[-1]["actions"] if r["actor"] == "Red_0")["valid"]
            await step()
            assert target in run.memory["Red_0"].view["known"]["ip_address"]
            await step({"action": "DiscoverNetworkServices", "target": target})
            assert target not in run.memory["Red_0"].view["scan_cache"]["0"]
            await step({"action": "ExploitRemoteService", "target": target})
            assert not next(r for r in run.frames[-1]["actions"] if r["actor"] == "Red_0")["valid"]
            await step()
            assert target in run.memory["Red_0"].view["scan_cache"]["0"]
            assert target not in json.dumps(run.memory.get("Red_1").public_view({}, {})) if workers > 1 else True
            for _ in range(3):
                await step()
            assert any(p["action"] == "DiscoverNetworkServices" and p["target"] == target for p in candidates(run.memory["Red_0"]))
            stored = manager.store.frame(run.id, 1)
            assert stored["complexity"]["manifest_hash"] == run.modules["manifest_hash"]
            assert target not in stored["private_views"]["Red_0"]["native"]["known"]["ip_address"]
            assert manager.store.frame(run.id, 6)["private_views"]["Red_0"]["beliefs"]["history"]
            assert run.cognition.calls == 0
        finally:
            await manager.close()
    asyncio.run(check())


@pytest.mark.engine
def test_native_restoration_is_disclosed_as_access_status_not_cause(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / "native.log", "enterprise_cc4")
        memory = PrivateMemory("Red_0", enabled(age=20).beliefs)
        try:
            await bridge.start()
            cfg = config(1, defender="reactive_restore")
            cfg.scenario.cc4.response_delay = 1
            cfg.scenario.cc4.response_budget = 1
            initial = await bridge.call("create", config=cfg.model_dump())
            memory.observe(initial["observations"]["Red_0"], initial["views"]["Red_0"])
            contractor = "contractor_network_subnet_server_host_0"
            target = "restricted_zone_a_subnet_server_host_0"
            contractor_ip, target_ip = address(initial, contractor), address(initial, target)
            async def drive(proposal=None):
                frame = await bridge.call("step", proposals={"Red_0": proposal or {"action": "Sleep"}})
                memory.observe(frame["observations"]["Red_0"], frame["views"]["Red_0"], frame["actions"][0])
                return frame
            for proposal in [
                {"action": "DiscoverRemoteSystems", "target": initial["views"]["Red_0"]["known"]["subnet"][0]},
                {"action": "DiscoverNetworkServices", "target": contractor_ip},
                {"action": "ExploitRemoteService", "target": contractor_ip},
                {"action": "PrivilegeEscalate", "target": contractor},
                {"action": "DiscoverNetworkServices", "target": target_ip},
                {"action": "ExploitRemoteService", "target": target_ip},
            ]:
                frame = await drive(proposal)
                while frame["views"]["Red_0"]["pending_action"]:
                    frame = await drive()
            for _ in range(10):
                frame = await drive()
            assert any(e["host"] == target and e["type"] == "access_lost" for e in memory.ledger.events)
            private = memory.public_view({}, {})
            assert "Restore" not in json.dumps(private) and "blue_agent" not in json.dumps(private)
            assert any(r["value"].get("Hostname") == target for r in private["beliefs"]["records"] if isinstance(r["value"], dict))
            assert not any(s["hostname"] == target for s in private["native"]["sessions"])
            frame = await drive({"action": "DiscoverNetworkServices", "target": target_ip})
            while frame["views"]["Red_0"]["pending_action"]:
                frame = await drive()
            frame = await drive({"action": "ExploitRemoteService", "target": target_ip})
            while frame["views"]["Red_0"]["pending_action"]:
                frame = await drive()
            assert frame["actions"][0]["outcome"] == "TRUE"
            assert any(e["host"] == target and e["type"] == "access_recovered" for e in memory.ledger.events)
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
@pytest.mark.parametrize("architecture", ["hierarchy", "swarm", "independent"])
def test_temporal_control_missions_finish_without_provider_calls(tmp_path, architecture):
    async def check():
        manager = RunManager(Store(tmp_path))
        try:
            cfg = config(2, architecture)
            cfg.scenario.complexity = enabled(2, 20)
            meta = await manager.create(cfg)
            run = manager.get(meta["id"])
            for _ in range(180):
                if run.meta["status"] == "completed":
                    break
                await run.advance()
            assert run.meta["termination_reason"] == "mission_success", run.meta
            assert run.cognition.calls == 0 and not run.meta["manual_intervention"]
            assert run.frames[-1]["private_views"]["Red_0"]["beliefs"]["history"]
        finally:
            await manager.close()
    asyncio.run(check())


@pytest.mark.engine
def test_run_restoration_recovery_preserves_offline_belief_evidence(tmp_path):
    async def check():
        manager = RunManager(Store(tmp_path))
        try:
            cfg = config(1, defender="reactive_restore")
            cfg.scenario.cc4.response_delay = 1
            cfg.scenario.cc4.response_budget = 1
            cfg.scenario.complexity = enabled(0, 20)
            run = manager.get((await manager.create(cfg))["id"])
            initial = run.frames[0]
            contractor = "contractor_network_subnet_server_host_0"
            target = "restricted_zone_a_subnet_server_host_0"
            contractor_ip, target_ip = address(initial, contractor), address(initial, target)
            async def drive(proposal=None):
                await run.advance({} if run.memory["Red_0"].view.get("pending_action") else {"Red_0": proposal or {"action": "Sleep"}})
                return run.frames[-1]
            for proposal in [
                {"action": "DiscoverRemoteSystems", "target": initial["views"]["Red_0"]["known"]["subnet"][0]},
                {"action": "DiscoverNetworkServices", "target": contractor_ip},
                {"action": "ExploitRemoteService", "target": contractor_ip},
                {"action": "PrivilegeEscalate", "target": contractor},
                {"action": "DiscoverNetworkServices", "target": target_ip},
                {"action": "ExploitRemoteService", "target": target_ip},
            ]:
                frame = await drive(proposal)
                while frame["views"]["Red_0"]["pending_action"]:
                    frame = await drive()
            for _ in range(10):
                frame = await drive()
            signals = frame["private_views"]["Red_0"]["beliefs"]["events"]
            assert any(e["type"] == "access_lost" and e["host"] == target for e in signals)
            for proposal in [{"action": "DiscoverNetworkServices", "target": target_ip}, {"action": "ExploitRemoteService", "target": target_ip}]:
                frame = await drive(proposal)
                while frame["views"]["Red_0"]["pending_action"]:
                    frame = await drive()
            await run.stop()
            replay = manager.store.frame(run.id)
            assert any(e["type"] == "access_recovered" and e["host"] == target for e in replay["private_views"]["Red_0"]["beliefs"]["events"])
            assert "Restore" not in json.dumps(replay["private_views"]["Red_0"])
            assert any(e["type"] == "defender_response_completed" for frame in run.frames for e in frame["defender_events"])
            assert replay["private_views"]["Red_0"]["beliefs"]["history"]
            assert run.cognition.calls == 0 and run.meta["manual_intervention"]
        finally:
            await manager.close()
    asyncio.run(check())
