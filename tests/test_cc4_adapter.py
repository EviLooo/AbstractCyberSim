"""Bounded native CC4 software fixtures; no training, providers or research sweep."""
import asyncio
import json

import pytest

from backend.app.bridge import EngineBridge
from backend.app.runs import RunManager
from backend.app.storage import Store
from packages.contracts.capabilities import profiles
from packages.contracts.models import EpisodeConfig
from packages.contracts.models import CC4_COMMIT


def config(workers=2, architecture="independent", defender="passive"):
    data = profiles()[1]["default_config"]
    data["team"].update(workers=workers, architecture=architecture)
    data["scenario"]["defender"] = defender
    # A service-controlled fixture isolates ownership from stochastic selection.
    data["scenario"]["cc4"]["addon_services"] = 0
    data["schedule"]["max_ticks"] = 180
    return EpisodeConfig.model_validate(data)


async def finish(bridge, proposals):
    result = await bridge.call("step", proposals=proposals)
    for _ in range(8):
        if not any(result["views"][actor]["pending_action"] for actor in proposals):
            return result
        result = await bridge.call("step", proposals={})
    raise AssertionError("Exceeded bounded action continuation")


def address(frame, hostname):
    host = next(host for host in frame["truth"]["hosts"] if host["id"] == hostname)
    return next(i["IP Address"] for i in host["interfaces"] if i["IP Address"] != "127.0.0.1")


@pytest.mark.engine
@pytest.mark.parametrize("workers", [1, 2, 4, 8])
def test_cc4_joint_workers_private_cache_and_duration(tmp_path, workers):
    async def check():
        bridge = EngineBridge(tmp_path / "native.log", "enterprise_cc4")
        try:
            hello = await bridge.start()
            assert hello["python"].startswith("3.12.") and not hello["upstream_dirty"]
            initial = await bridge.call("create", config=config(workers).model_dump())
            actors = initial["actors"]
            assert actors == [f"Red_{i}" for i in range(workers)]
            assert all(len(view["sessions"]) == 1 for view in initial["views"].values())
            target = address(initial, "contractor_network_subnet_server_host_0")
            assert target not in initial["views"][actors[0]]["known"]["ip_address"]
            subnet = initial["views"][actors[0]]["known"]["subnet"][0]
            discovered = await finish(bridge, {a: {"action": "DiscoverRemoteSystems", "target": subnet} for a in actors})
            assert discovered["tick"] == 1 and discovered["native_step_count"] == 1
            assert all(target in view["known"]["ip_address"] for view in discovered["views"].values())
            scanned = await finish(bridge, {actors[0]: {"action": "DiscoverNetworkServices", "target": target}})
            assert scanned["views"][actors[0]]["scan_cache"]["0"][target]
            if workers > 1:
                assert target not in scanned["views"][actors[1]]["scan_cache"]["0"]
                rejected = await bridge.call("step", proposals={actors[1]: {"action": "ExploitRemoteService", "target": target}})
                assert not next(a for a in rejected["actions"] if a["actor"] == actors[1])["valid"]
            await finish(bridge, {a: {"action": "DiscoverNetworkServices", "target": target} for a in actors[1:]})
            starting = await bridge.call("step", proposals={a: {"action": "ExploitRemoteService", "target": target} for a in actors})
            assert all(a["outcome"] == "IN_PROGRESS" and a["remaining_ticks"] == 3 for a in starting["actions"])
            assert all(a["submitted"] for a in starting["actions"])
            end = starting
            for remaining in (2, 1, 0):
                end = await bridge.call("step", proposals={})
                assert all(a["remaining_ticks"] == remaining for a in end["actions"])
                assert all(not a["submitted"] for a in end["actions"])
            assert end["tick"] == starting["tick"] + 3
            assert all(a["outcome"] == "TRUE" for a in end["actions"])
            assert all(any(s["hostname"] == "contractor_network_subnet_server_host_0" for s in v["sessions"]) for v in end["views"].values())
            assert len(end["score"]["controlled_hosts"]) == 2
            assert {s["agent"] for h in end["truth"]["hosts"] if h["id"] == "contractor_network_subnet_server_host_0" for s in h["sessions"] if s["agent"].startswith("Red_")} == set(actors)
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
def test_cc4_initial_world_stable_and_intel_is_delivered_only(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / "native.log", "enterprise_cc4")
        try:
            await bridge.start()
            cfg = config().model_dump()
            initial = await bridge.call("create", config=cfg)
            repeat = await bridge.call("create", config=cfg)
            assert repeat["world"] == initial["world"]
            cfg["team"]["architecture"] = "hierarchy"
            hierarchy = await bridge.call("create", config=cfg)
            assert hierarchy["world"]["world_id"] == initial["world"]["world_id"]
            subnet = initial["views"]["Red_0"]["known"]["subnet"][0]
            target = address(initial, "contractor_network_subnet_server_host_0")
            discovered = await finish(bridge, {"Red_0": {"action": "DiscoverRemoteSystems", "target": subnet}})
            eid = discovered["observations"]["Red_0"]["evidence_id"]
            assert target not in discovered["views"]["Red_1"]["known"]["ip_address"]
            forged = await bridge.call("ingest_intel", sender="Red_1", recipient="Red_1", evidence_ids=[eid])
            assert not forged["accepted_evidence"]
            update = await bridge.call("ingest_intel", sender="Red_0", recipient="Red_1", evidence_ids=[eid])
            assert target in update["view"]["known"]["ip_address"]
            assert not update["view"]["scan_cache"]["0"] and len(update["view"]["sessions"]) == 1
            assert all("Sessions" not in fields and "Processes" not in fields for fields in update["address_fragment"].values())
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
@pytest.mark.parametrize("architecture", ["hierarchy", "swarm", "independent"])
def test_cc4_complete_mission_and_offline_replay(tmp_path, architecture):
    async def check():
        store = Store(tmp_path)
        manager = RunManager(store)
        try:
            meta = await manager.create(config(2, architecture, "monitor"))
            run = manager.get(meta["id"])
            while run.meta["status"] not in {"completed", "errored"}:
                await run.advance()
            assert run.meta["termination_reason"] == "mission_success", [(f["tick"], [(a["actor"], a["proposal"], a["outcome"]) for a in f["actions"]]) for f in run.frames]
            assert run.cognition.summary()["calls"] == 0
            assert run.engine.process is None
            saved = store.frame(run.id)
            assert saved["score"]["targets_reached"] == 1
            assert saved["engine_profile"] == "enterprise_cc4"
            assert json.loads((run.directory / "manifest.json").read_text())["versions"]["engine_commit"] == CC4_COMMIT
        finally:
            await manager.close()
    asyncio.run(check())


def test_cc4_configuration_rejects_unsupported_combinations():
    for scenario in [
        {"profile": "enterprise_cc4", "targets": ["Op_Server0"]},
        {"defender": "reactive_restore"},
        {"cc4": {}},
        {"profile": "enterprise_cc4", "targets": ["restricted_zone_a_subnet_server_host_0"], "cc4": {"user_hosts": 2}},
    ]:
        with pytest.raises(ValueError):
            EpisodeConfig.model_validate({"scenario": scenario})


def test_reactive_policy_delay_budget_cooldown_and_observation_boundary():
    from packages.engine_worker.cc4.defender import RestorePolicy
    settings = {"response_delay": 2, "response_budget": 2, "response_cooldown": 10}
    policy = RestorePolicy(settings)
    assert not policy.observe({"host": {"System info": {"Hostname": "host"}}}, 0)
    events = policy.observe({"host": {"Processes": [{"Connections": []}]}}, 1)
    assert events[0]["signal_tick"] == 1
    assert policy.choose(2, {"host"}) is None
    assert policy.choose(3, set()) is None
    assert policy.choose(3, {"host"})["host"] == "host"
    assert not policy.observe({"host": {"Processes": [{}]}}, 4)
    policy.observe({"host": {"Processes": [{}]}}, 13)
    assert policy.choose(15, {"host"})["remaining_responses"] == 0
    policy.observe({"host": {"Processes": [{}]}}, 25)
    assert policy.choose(30, {"host"}) is None


@pytest.mark.engine
def test_cc4_reactive_restore_has_native_effect_and_event_provenance(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / "native.log", "enterprise_cc4")
        frames = []
        try:
            await bridge.start()
            cfg = config(1, defender="reactive_restore")
            cfg.scenario.cc4.response_delay = 1
            cfg.scenario.cc4.response_budget = 1
            initial = await bridge.call("create", config=cfg.model_dump())
            actor = "Red_0"
            contractor = "contractor_network_subnet_server_host_0"
            target = "restricted_zone_a_subnet_server_host_0"
            contractor_ip, target_ip = address(initial, contractor), address(initial, target)
            await finish(bridge, {actor: {"action": "DiscoverRemoteSystems", "target": initial["views"][actor]["known"]["subnet"][0]}})
            await finish(bridge, {actor: {"action": "DiscoverNetworkServices", "target": contractor_ip}})
            await finish(bridge, {actor: {"action": "ExploitRemoteService", "target": contractor_ip}})
            escalated = await finish(bridge, {actor: {"action": "PrivilegeEscalate", "target": contractor}})
            assert target_ip in escalated["views"][actor]["known"]["ip_address"]
            frames.append(await finish(bridge, {actor: {"action": "DiscoverNetworkServices", "target": target_ip}}))
            frames.append(await bridge.call("step", proposals={actor: {"action": "ExploitRemoteService", "target": target_ip}}))
            for _ in range(10):
                frames.append(await bridge.call("step", proposals={}))
            events = [event for frame in frames for event in frame["defender_events"] if event.get("host") == target]
            (tmp_path / "reactive-debug.json").write_text(json.dumps(frames, indent=2))
            assert events, tmp_path / "reactive-debug.json"
            started = next(event for event in events if event["type"] == "defender_response_started")
            completed = next(event for event in events if event["type"] == "defender_response_completed")
            assert started["decision_tick"] >= started["signal_tick"] + 1
            assert completed["outcome"] == "TRUE"
            assert any(any(session["hostname"] == target for session in frame["views"][actor]["sessions"]) for frame in frames)
            assert not any(session["hostname"] == target for session in frames[-1]["views"][actor]["sessions"])
            assert any(any(session["hostname"] == target for session in frame["actions"][0]["state_delta"]["sessions_lost"]) for frame in frames)
            assert all("blue_agent" not in json.dumps(frame["views"][actor]) for frame in frames)
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
def test_cc4_busy_worker_no_extra_cognition_calls_and_single_team_capacity(tmp_path):
    async def check():
        store = Store(tmp_path)
        manager = RunManager(store)
        try:
            cfg = config(2)
            cfg.schedule.mode = "team_cap_one"
            meta = await manager.create(cfg)
            run = manager.get(meta["id"])
            # Count scheduling without using any live provider.
            calls = []
            original = run.cognition.worker
            async def counted(actor, view, preferred):
                calls.append((actor, run.meta["tick"] + 1))
                return await original(actor, view, preferred)
            run.cognition.worker = counted
            for _ in range(35):
                if run.meta["status"] == "completed":
                    break
                previous_pending = {actor for actor, memory in run.memory.items() if memory.view.get("pending_action")}
                tick = run.meta["tick"] + 1
                await run.advance()
                assert not any((actor, tick) in calls for actor in previous_pending)
                assert sum(bool(view["pending_action"]) for view in run.frames[-1]["views"].values()) <= 1
            continuations = [record for frame in run.frames for record in frame["actions"] if record.get("submitted") is False and record["proposal"]["action"] != "Sleep"]
            assert continuations
            admissions = sum(record.get("submitted", True) and record["proposal"]["action"] != "Sleep" for frame in run.frames for record in frame["actions"])
            assert run.meta["metrics"]["attempted_actions"] == admissions
        finally:
            await manager.close()
    asyncio.run(check())


@pytest.mark.engine
def test_cc4_api_profile_roundtrip_export_and_busy_override(tmp_path):
    import io
    import zipfile
    import httpx
    from backend.app.api import create_app

    async def check():
        app = create_app(tmp_path)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                capabilities = (await client.get("/api/capabilities")).json()
                assert {profile["id"] for profile in capabilities["profiles"]} == {"enterprise_cc4", "enterprise_legacy", "enterprise_cc4_research"}
                cfg = config(1)
                resolved = await client.post("/api/configs/validate", json=cfg.model_dump())
                assert resolved.status_code == 200 and resolved.json() == cfg.model_dump()
                created = await client.post("/api/runs", json=cfg.model_dump())
                assert created.status_code == 201
                run_id = created.json()["id"]
                assert created.json()["tick"] == 0 and created.json()["status"] == "ready"
                run = app.state.manager.get(run_id)
                initial = run.frames[0]
                target = address(initial, "contractor_network_subnet_server_host_0")
                for proposal in [
                    {"action": "DiscoverRemoteSystems", "target": initial["views"]["Red_0"]["known"]["subnet"][0]},
                    {"action": "DiscoverNetworkServices", "target": target},
                    {"action": "ExploitRemoteService", "target": target},
                ]:
                    stepped = await client.post(f"/api/runs/{run_id}/step", json={"overrides": {"Red_0": proposal}})
                    assert stepped.status_code == 200
                assert run.memory["Red_0"].view["pending_action"]
                before_tick = run.meta["tick"]
                rejected = await client.post(f"/api/runs/{run_id}/step", json={"overrides": {"Red_0": {"action": "Sleep"}}})
                assert rejected.status_code == 409 and run.meta["tick"] == before_tick
                assert run.meta["status"] == "paused"
                assert (await client.post(f"/api/runs/{run_id}/step", json={})).status_code == 200
                await client.post(f"/api/runs/{run_id}/control/stop")
                exported = await client.get(f"/api/runs/{run_id}/export")
                assert exported.status_code == 200
                with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
                    assert json.loads(archive.read("config.json"))["scenario"]["profile"] == "enterprise_cc4"
                    assert any(name.startswith("frames/") for name in archive.namelist())
                assert run.engine.process is None
        finally:
            await app.state.manager.close()
    asyncio.run(check())


@pytest.mark.engine
def test_cc4_population_controls_and_addon_cap_materialize(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / "native.log", "enterprise_cc4")
        try:
            await bridge.start()
            cfg = config(1)
            small = await bridge.call("create", config=cfg.model_dump())
            cfg.scenario.cc4.user_hosts = 10
            cfg.scenario.cc4.server_hosts = 6
            large = await bridge.call("create", config=cfg.model_dump())
            assert len(large["truth"]["hosts"]) - len(small["truth"]["hosts"]) == 8 * (7 + 5)
            assert large["world"]["world_id"] != small["world"]["world_id"]
            assert large["score"]["targets_reached"] == 0
            assert not large["actions"]
        finally:
            await bridge.close()
    asyncio.run(check())
