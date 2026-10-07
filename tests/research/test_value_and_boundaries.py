import asyncio

import pytest
from backend.app.bridge import EngineBridge
from tests.research.helpers import config, finish, ip, action, evidence, TARGET_A


@pytest.mark.engine
def test_hand_count_information_value_and_negative_ssh_under_equal_limits(tmp_path):
    async def trajectory(bridge, informed):
        cfg = config("import_disabled", credential_variant="valid")
        cfg["resources"]["team_access_attempts"] = 3
        frame = await bridge.call("create", config=cfg)
        target = ip(frame, TARGET_A)
        entry = frame["views"]["Red_0"]["sessions"][0]["hostname"]
        frame = await finish(bridge, {"action": "InspectArtifacts", "target": entry})
        frame = await finish(bridge, {"action": "DiscoverNetworkServices", "target": target})
        if informed is True:
            frame = await finish(bridge, {"action": "Probe", "probe": "service_behavior", "port": 80, "target": target})
            assert evidence(frame)[0]["response"] == "external_import_refused"
            frame = await finish(bridge, {"action": "Probe", "probe": "auth_policy", "port": 22, "target": target})
            assert evidence(frame)[0]["response"] == "password_and_account_token_supported"
            # The provisioning note, not auth_policy's handshake, supplies the
            # weak-account hypothesis. This test witness uses disclosed evidence.
            frame = await finish(bridge, {"action": "AttemptAccess", "method": "ssh_weak_auth", "target": target})
            assert action(frame)["outcome"] == "TRUE"
            frame = await finish(bridge, {"action": "PrivilegeEscalate", "target": TARGET_A})
        elif informed == "fixed":
            for _ in range(2):
                frame = await finish(bridge, {"action": "AttemptAccess", "method": "web_rfi", "target": target})
                assert action(frame)["outcome"] == "FALSE"
            frame = await finish(bridge, {"action": "AttemptAccess", "method": "ssh_weak_auth", "target": target})
            assert action(frame)["outcome"] == "TRUE"
            frame = await finish(bridge, {"action": "PrivilegeEscalate", "target": TARGET_A})
        else:
            for _ in range(3):
                frame = await finish(bridge, {"action": "AttemptAccess", "method": "web_rfi", "target": target})
                assert action(frame)["outcome"] == "FALSE"
        return frame

    async def check():
        bridge = EngineBridge(tmp_path / "native.log", "enterprise_cc4_research")
        try:
            await bridge.start()
            informed = await trajectory(bridge, True)
            blind = await trajectory(bridge, False)
            fixed = await trajectory(bridge, "fixed")
            assert informed["score"]["mission_success"] and not blind["score"]["mission_success"]
            assert informed["views"]["Red_0"]["access_resources"]["reserved"] == 1
            assert blind["views"]["Red_0"]["access_resources"]["reserved"] == 3
            assert fixed["score"]["mission_success"]
            assert fixed["views"]["Red_0"]["access_resources"]["reserved"] == 3
            assert fixed["tick"] > informed["tick"]
            # Same public budget/horizon; no shortened deadline creates the gap.
            assert informed["views"]["Red_0"]["access_resources"]["limit"] == blind["views"]["Red_0"]["access_resources"]["limit"] == 3
            frame = await bridge.call("create", config=config("ssh_hardened"))
            target = ip(frame, TARGET_A)
            entry = frame["views"]["Red_0"]["sessions"][0]["hostname"]
            frame = await finish(bridge, {"action": "InspectArtifacts", "target": entry})
            frame = await finish(bridge, {"action": "DiscoverNetworkServices", "target": target})
            for _ in range(3):
                frame = await finish(bridge, {"action": "AttemptAccess", "method": "ssh_weak_auth", "target": target})
                assert action(frame)["outcome"] == "FALSE"
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
def test_budget_busy_reset_and_background_cannot_bypass(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / "native.log", "enterprise_cc4_research")
        try:
            await bridge.start()
            cfg = config(workers=2)
            cfg["resources"]["team_access_attempts"] = 1
            initial = await bridge.call("create", config=cfg)
            target = ip(initial, TARGET_A)
            for actor in initial["actors"]:
                entry = initial["views"][actor]["sessions"][0]["hostname"]
                await finish(bridge, {"action": "InspectArtifacts", "target": entry}, actor)
                await finish(bridge, {"action": "DiscoverNetworkServices", "target": target}, actor)
            admitted = await bridge.call("step", proposals={actor: {"action": "AttemptAccess", "target": target, "method": "web_rfi"} for actor in initial["actors"]})
            assert sum(r["valid"] for r in admitted["actions"]) == 1
            owner = next(r["actor"] for r in admitted["actions"] if r["valid"])
            assert admitted["views"][owner]["access_resources"]["reserved"] == 1
            for remaining in (2, 1, 0):
                frame = await bridge.call("step", proposals={owner: {"action": "AttemptAccess", "target": target, "method": "web_rfi"}})
                assert action(frame, owner)["remaining_ticks"] == remaining
                assert frame["views"][owner]["access_resources"]["reserved"] == 1
            reset = await bridge.call("create", config=cfg)
            assert reset["views"] == initial["views"] and reset["observations"] == initial["observations"]
            generic = await finish(bridge, {"action": "ExploitRemoteService", "target": target})
            assert not action(generic)["valid"]
            subnet = reset["views"]["Red_0"]["known"]["subnet"][0]
            frame = await finish(bridge, {"action": "DiscoverRemoteSystems", "target": subnet})
            background = ip(frame, "contractor_network_subnet_server_host_0")
            frame = await finish(bridge, {"action": "DiscoverNetworkServices", "target": background})
            assert not frame["views"]["Red_0"]["scan_cache"]["0"].get(background)
            forbidden = await finish(bridge, {"action": "AttemptAccess", "method": "web_rfi", "target": background})
            assert not action(forbidden)["valid"]
            assert len(forbidden["views"]["Red_0"]["sessions"]) == 1
        finally:
            await bridge.close()
    asyncio.run(check())
