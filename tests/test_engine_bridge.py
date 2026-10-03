"""Bounded integration checks of actions/ownership. No research trials or LLM calls."""
import asyncio
import json
import pytest
from backend.app.bridge import EngineBridge
from packages.contracts.models import EpisodeConfig


@pytest.mark.engine
@pytest.mark.parametrize("count", [1, 2, 4, 8])
def test_real_engine_discovery_scan_exploit_and_ownership(tmp_path, count):
    async def check():
        bridge = EngineBridge(tmp_path / "native.log")
        try:
            hello = await bridge.start()
            assert hello["python"].startswith("3.8.")
            config = EpisodeConfig()
            config.team.workers = count
            initial = await bridge.call("create", config=config.model_dump())
            actors = initial["actors"]
            assert len(actors) == count
            assert len(initial["truth"]["hosts"]) == 16
            assert sum(host["router"] for host in initial["truth"]["hosts"]) == 3
            # Unknown addresses exist in native truth but never in a view.
            view = initial["views"][actors[0]]
            hidden = next(str(i["IP Address"]) for host in initial["truth"]["hosts"] for i in host["interfaces"] if "IP Address" in i and str(i["IP Address"]) not in view["known"]["ip_address"])
            bad = await bridge.call("step", proposals={actors[0]: {"action": "DiscoverNetworkServices", "session": 0, "target": hidden}})
            assert not next(a for a in bad["actions"] if a["actor"] == actors[0])["valid"]
            subnet = view["known"]["subnet"][0]
            discovered = await bridge.call("step", proposals={a: {"action": "DiscoverRemoteSystems", "session": 0, "target": subnet} for a in actors})
            assert all(o["data"]["success"] == "TRUE" for o in discovered["observations"].values())
            own_ips = initial["views"][actors[0]]["known"]["ip_address"]
            target = next(ip for ip in discovered["views"][actors[0]]["known"]["ip_address"] if ip not in own_ips)
            scanned = await bridge.call("step", proposals={a: {"action": "DiscoverNetworkServices", "session": 0, "target": target} for a in actors})
            assert all(o["data"]["success"] == "TRUE" for o in scanned["observations"].values())
            exploited = await bridge.call("step", proposals={a: {"action": "ExploitRemoteService", "session": 0, "target": target} for a in actors})
            assert all(o["data"]["success"] == "TRUE" for o in exploited["observations"].values())
            assert all(len(v["sessions"]) == 2 for v in exploited["views"].values())
            assert len(exploited["score"]["controlled_hosts"]) == 2
            assert set(exploited["submission_order"]) == set(actors)
        finally:
            await bridge.close()
        assert bridge.process is None
    asyncio.run(check())


@pytest.mark.engine
def test_verified_intel_cannot_grant_scan_cache_or_sessions(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / "native.log")
        try:
            await bridge.start()
            config = EpisodeConfig()
            config.team.workers = 2
            initial = await bridge.call("create", config=config.model_dump())
            subnet = initial["views"]["Red_0"]["known"]["subnet"][0]
            discovered = await bridge.call("step", proposals={"Red_0": {"action": "DiscoverRemoteSystems", "session": 0, "target": subnet}})
            target = next(ip for ip in discovered["views"]["Red_0"]["known"]["ip_address"] if ip not in discovered["views"]["Red_1"]["known"]["ip_address"])
            eid = discovered["observations"]["Red_0"]["evidence_id"]
            forged = await bridge.call("ingest_intel", sender="Red_1", recipient="Red_1", evidence_ids=[eid, "fake"])
            assert target not in forged["view"]["known"]["ip_address"]
            delivered = await bridge.call("ingest_intel", sender="Red_0", recipient="Red_1", evidence_ids=[eid])
            assert target in delivered["view"]["known"]["ip_address"]
            assert not delivered["view"]["scan_cache"]["0"]
            assert len(delivered["view"]["sessions"]) == 1
            scanned = await bridge.call("step", proposals={"Red_0": {"action": "DiscoverNetworkServices", "target": target}})
            assert scanned["views"]["Red_0"]["scan_cache"]["0"][target]
            shared_scan = await bridge.call("ingest_intel", sender="Red_0", recipient="Red_1", evidence_ids=[scanned["observations"]["Red_0"]["evidence_id"]])
            assert not shared_scan["view"]["scan_cache"]["0"]
            assert all("Processes" not in fields and "Sessions" not in fields for fields in shared_scan["address_fragment"].values())
            rejected = await bridge.call("step", proposals={"Red_1": {"action": "ExploitRemoteService", "session": 0, "target": target}})
            assert not next(a for a in rejected["actions"] if a["actor"] == "Red_1")["valid"]
        finally:
            await bridge.close()
    asyncio.run(check())
