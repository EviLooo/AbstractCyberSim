"""Phase 1/2 software fixtures. No experiment matrix or real model transport."""
import asyncio
import io
import json
import zipfile

import httpx
import pytest
from pydantic import ValidationError

from backend.app.api import create_app
from backend.app.cli import arguments, remote
from backend.app.knowledge import PrivateMemory
from backend.app.runs import RunManager
from backend.app.storage import Store
from backend.app.transport import MessageBus
from packages.contracts.models import CommunicationConfig, EpisodeConfig


def test_interruption_validation_and_sparse_directed_topology():
    with pytest.raises(ValidationError):
        EpisodeConfig.model_validate({"scenario":{"targets":["User0"]}})
    with pytest.raises(ValidationError):
        EpisodeConfig.model_validate({"scenario":{"targets":["Op_Server0","Op_Server0"]}})
    with pytest.raises(ValidationError, match="Interruption end"):
        EpisodeConfig.model_validate({"communication":{"interruptions":[{"start_tick":8,"end_tick":2}]}})
    with pytest.raises(ValidationError, match="unavailable reasoner"):
        EpisodeConfig.model_validate({"team":{"workers":1},"communication":{"interruptions":[{"start_tick":1,"end_tick":2,"sender":"Red_7"}]}})
    with pytest.raises(ValidationError, match="configured organization"):
        EpisodeConfig.model_validate({"communication":{"links":[{"sender":"Red_0","recipient":"Red_1"}]}})
    config = EpisodeConfig.model_validate({"team":{"architecture":"swarm","workers":3},"communication":{"links":[{"sender":"Red_0","recipient":"Red_1"}]}})
    bus = MessageBus(config.communication,["Red_0","Red_1","Red_2"],"swarm")
    assert bus.neighbors("Red_0") == ["Red_1"] and not bus.neighbors("Red_1")
    assert not bus.neighbors("Blue")
    with pytest.raises(ValueError,match="topology"):
        bus.enqueue("Red_0",["Red_2"],"claim",{},[],1)


def test_scheduled_link_drop_recovery_delay_and_expiry_precedence():
    config = CommunicationConfig.model_validate({"interruptions":[{"start_tick":2,"end_tick":3,"sender":"Red_0","recipient":"Red_1"}]})
    bus = MessageBus(config,["Red_0","Red_1","Red_2"],"swarm")
    bus.enqueue("Red_0",["Red_1","Red_2"],"claim",{},[],1)
    bus.enqueue("Red_1",["Red_0"],"claim",{},[],1)
    assert not any(bus.deliver(1)[0].values())
    delivered,changes = bus.deliver(2)
    assert len(delivered["Red_2"]) == 1
    assert sum(m["status"] == "dropped_link" for m in changes) == 2
    assert all(not e["active"] for e in bus.topology(3) if {e["sender"],e["recipient"]} == {"Red_0","Red_1"})
    bus.enqueue("Red_0",["Red_1"],"claim",{},[],3)
    assert len(bus.deliver(4)[0]["Red_1"]) == 1
    assert all(e["active"] for e in bus.topology(4))
    assert all(m["status"] != "pending" for m in bus.snapshot())
    expired = MessageBus(CommunicationConfig.model_validate({"extra_delay":3,"ttl":1,"interruptions":[{"start_tick":2,"end_tick":8}]}),["Red_0","Red_1"],"swarm")
    expired.enqueue("Red_0",["Red_1"],"claim",{},[],1)
    assert expired.deliver(3)[1][0]["status"] == "expired"


def test_one_way_outage_does_not_block_reverse_link():
    config = CommunicationConfig.model_validate({"interruptions":[{"start_tick":1,"end_tick":2,"sender":"Red_0","recipient":"Red_1","bidirectional":False}]})
    bus = MessageBus(config,["Red_0","Red_1"],"swarm")
    for sender,recipient in [("Red_0","Red_1"),("Red_1","Red_0")]:
        bus.enqueue(sender,[recipient],"claim",{},[],0)
    delivered,events = bus.deliver(1)
    assert len(delivered["Red_0"]) == 1 and not delivered["Red_1"]
    assert {m["status"] for m in events} == {"delivered","dropped_link"}


def test_memory_preserves_nested_facts_and_separates_verified_reports():
    memory = PrivateMemory("Red_0")
    memory.observe({"evidence_id":"Red_0:0:0","tick":0,"data":{"10.0.0.1":{"System info":{"Hostname":"User0","OSType":"WINDOWS"},"Interface":[{"IP Address":"10.0.0.1"}],"Processes":[{"PID":10}]}}},{"actor":"Red_0"})
    memory.observe({"evidence_id":"Red_0:1:1","tick":1,"data":{"10.0.0.1":{"System info":{"OSVersion":"old"},"Processes":[{"PID":20}]}}},{"actor":"Red_0"})
    memory.report({"10.0.0.2":{"System info":{"Hostname":"PeerHost"}}},["Red_1:1:2"],"Red_1",2)
    own = memory.hosts["10.0.0.1"]["fields"]
    assert own["System info"]["Hostname"] == "User0" and len(own["Processes"]) == 2
    assert "10.0.0.2" not in memory.hosts
    assert memory.reported_hosts["10.0.0.2"]["source"] == "verified_peer_report"
    view = memory.public_view({}, {})
    view["hosts"]["10.0.0.1"]["fields"]["System info"]["Hostname"] = "changed"
    assert own["System info"]["Hostname"] == "User0"


@pytest.mark.engine
@pytest.mark.parametrize("architecture",["hierarchy","swarm"])
def test_forged_reference_and_undelivered_relay_cannot_unlock_address(tmp_path,architecture):
    async def check():
        manager = RunManager(Store(tmp_path))
        config = EpisodeConfig()
        config.team.workers = 3
        config.team.architecture = architecture
        try:
            meta = await manager.create(config)
            run = manager.get(meta["id"])
            subnet = run.memory["Red_0"].view["known"]["subnet"][0]
            proposals = {actor:{"action":"Sleep"} for actor in run.actors}
            proposals["Red_0"] = {"action":"DiscoverRemoteSystems","target":subnet}
            await run.advance(proposals)
            evidence = run.memory["Red_0"].observations[-1]["evidence_id"]
            target = next(ip for ip in run.memory["Red_0"].view["known"]["ip_address"] if ip not in run.memory["Red_2"].view["known"]["ip_address"])
            forged_sender = "Coordinator" if architecture == "hierarchy" else "Red_1"
            kind = "assignment" if architecture == "hierarchy" else "claim"
            message = {"id":"fixture-forgery","sender":forged_sender,"recipient":"Red_2","kind":kind,"created_tick":1,"resolved_tick":2,"evidence_ids":[evidence],"payload":{}}
            await run.bridge_messages({"Red_2":[message]})
            assert target not in run.memory["Red_2"].view["known"]["ip_address"]
            # A leader report must really have arrived before the relay was
            # created. A same-tick or future-dated report is insufficient.
            if architecture == "hierarchy":
                report = dict(message,id="fixture-report",sender="Red_0",recipient="Coordinator",kind="report")
                await run.bridge_messages({"Coordinator":[report]})
                await run.bridge_messages({"Red_2":[message]})
                assert target not in run.memory["Red_2"].view["known"]["ip_address"]
                message["created_tick"] = 2
            else:
                message["sender"] = "Red_0"
            await run.bridge_messages({"Red_2":[message]})
            assert target in run.memory["Red_2"].view["known"]["ip_address"]
            assert target in run.memory["Red_2"].reported_hosts
            assert target not in run.memory["Red_2"].hosts
            assert not run.memory["Red_2"].view["scan_cache"]["0"]
            assert len(run.memory["Red_2"].view["sessions"]) == 1
        finally:
            await manager.close()
    asyncio.run(check())


@pytest.mark.engine
@pytest.mark.parametrize("architecture",["hierarchy","swarm","independent"])
def test_team_capacity_is_neutral_and_native_state_deltas_are_owned(tmp_path,architecture):
    async def check():
        manager = RunManager(Store(tmp_path))
        config = EpisodeConfig()
        config.team.workers = 2
        config.team.architecture = architecture
        config.schedule.mode = "team_cap_one"
        config.scenario.defender = "monitor"
        config.communication.verified_intel = False
        try:
            meta = await manager.create(config)
            run = manager.get(meta["id"])
            subnet = run.memory["Red_0"].view["known"]["subnet"][0]
            for tick in range(1,4):
                await run.advance({a:{"action":"DiscoverRemoteSystems","target":subnet} for a in run.actors})
                frame = run.frames[-1]
                selected = run.actors[(tick-1)%2]
                active = [a for a in frame["actions"] if a["proposal"]["action"] != "Sleep"]
                assert len(active) == 1 and active[0]["actor"] == selected
                assert all(active[0]["preconditions"].values())
                assert frame["native_step_count"] == tick
                assert len(frame["suppressed_proposals"]) == 1
                assert sum(e["actor"] == "Blue" for e in frame["execution_trace"]) == 1
                if tick < 3:
                    assert active[0]["state_delta"]["knowledge_added"]["ip_address"]
        finally:
            await manager.close()
    asyncio.run(check())


@pytest.mark.engine
def test_cli_api_config_roundtrip_controls_events_and_replay_are_same_run(tmp_path):
    async def check():
        app = create_app(tmp_path)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as client:
                config = EpisodeConfig.model_validate({"team":{"workers":2,"architecture":"swarm"},"communication":{"interruptions":[{"start_tick":2,"end_tick":2}]}})
                cfg_file = tmp_path/"exported.json"
                cfg_file.write_text(config.model_dump_json(),encoding="utf-8")
                created = await remote(arguments(["initialize",str(cfg_file)]),client)
                rid = created["id"]
                assert created["status"] == "ready" and created["tick"] == 0
                saved = (await client.get(f"/api/runs/{rid}/config")).json()
                assert saved == config.model_dump()
                await remote(arguments(["step",rid]),client)
                await remote(arguments(["step",rid]),client)
                frame = await remote(arguments(["frame",rid,"--tick","2"]),client)
                assert all(not edge["active"] for edge in frame["communication_topology"])
                assert any(m["status"] == "dropped_link" for m in frame["messages"])
                events = await remote(arguments(["events",rid]),client)
                next_events = await remote(arguments(["events",rid,"--after",str(events["cursor"])]),client)
                assert next_events["items"] == [] and next_events["cursor"] == events["cursor"]
                run = app.state.manager.get(rid)
                original = run.engine.call
                async def pause_at_boundary(method,**params):
                    value = await original(method,**params)
                    if method == "step":
                        run.pause_requested = True
                    return value
                run.engine.call = pause_at_boundary
                started = await remote(arguments(["control",rid,"start"]),client)
                assert started["status"] == "running"
                blocked = await client.post(f"/api/runs/{rid}/step",json={})
                assert blocked.status_code == 409
                await run.task
                paused = await remote(arguments(["control",rid,"pause"]),client)
                assert paused["status"] == "paused" and paused["tick"] == 3
                await remote(arguments(["control",rid,"continue"]),client)
                await run.task
                assert run.meta["tick"] == 4
                count = run.meta["tick"]
                for _ in range(2):
                    assert (await remote(arguments(["frame",rid,"--tick","1"]),client))["tick"] == 1
                assert run.meta["tick"] == count and run.cognition.calls == 0
                stopped = await remote(arguments(["control",rid,"stop"]),client)
                assert stopped["status"] == "stopped" and run.engine.process is None
                archive = await client.get(f"/api/runs/{rid}/export")
                with zipfile.ZipFile(io.BytesIO(archive.content)) as bundle:
                    assert json.loads(bundle.read("config.json")) == saved
                    assert json.loads(bundle.read("frames/000002.json"))["communication_topology"] == frame["communication_topology"]
                broken = await client.post(f"/api/runs/{rid}/step",json={"overrides":{"Red_0":{"action":"RunShellCommand","target":"anything"}}})
                assert broken.status_code == 422
                assert run.meta["tick"] == count
    asyncio.run(check())


@pytest.mark.engine
def test_sparse_hierarchy_missing_report_link_waits_without_crashing(tmp_path):
    async def check():
        manager = RunManager(Store(tmp_path))
        config = EpisodeConfig.model_validate({"team":{"workers":2},"communication":{"links":[{"sender":"Red_0","recipient":"Coordinator"},{"sender":"Coordinator","recipient":"Red_0"}]}})
        try:
            meta = await manager.create(config)
            run = manager.get(meta["id"])
            for _ in range(3):
                await run.advance()
            assert run.meta["status"] == "paused"
            assert set(run.organization.reports) == {"Red_0"}
            assert all(m["sender"] != "Red_1" and m["recipient"] != "Red_1" for m in run.bus.messages)
            assert next(a for a in run.frames[-1]["actions"] if a["actor"] == "Red_1")["proposal"]["action"] == "Sleep"
        finally:
            await manager.close()
    asyncio.run(check())
