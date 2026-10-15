import asyncio

import pytest
from backend.app.bridge import EngineBridge
from tests.research.helpers import config, finish, ip, action, evidence, TARGET_A, TARGET_B


@pytest.mark.engine
@pytest.mark.parametrize("provision", ["valid", "wrong_scope", "invalid"])
def test_native_login_possession_scope_and_attempt_accounting(tmp_path, provision):
    async def check():
        bridge = EngineBridge(tmp_path / "native.log", "enterprise_cc4_research")
        try:
            await bridge.start()
            frame = await bridge.call("create", config=config("ssh_hardened", credential_variant=provision))
            target = ip(frame, TARGET_A)
            entry = frame["views"]["Red_0"]["sessions"][0]["hostname"]
            frame = await finish(bridge, {"action": "InspectArtifacts", "target": entry})
            token = next(e["token_ref"] for e in evidence(frame) if e.get("token_ref"))
            frame = await finish(bridge, {"action": "DiscoverNetworkServices", "target": target})
            forged = await finish(bridge, {"action": "AttemptAccess", "method": "credential_login", "target": target, "token_ref": "fabricated"})
            assert not action(forged)["valid"]
            assert forged["views"]["Red_0"]["access_resources"]["reserved"] == 0
            for retry in range(1 if provision == "valid" else 3):
                frame = await finish(bridge, {"action": "AttemptAccess", "method": "credential_login", "target": target, "token_ref": token})
                assert action(frame)["outcome"] == ("TRUE" if provision == "valid" else "FALSE")
                assert frame["views"]["Red_0"]["access_resources"]["reserved"] == retry + 1
                assert frame["views"]["Red_0"]["access_resources"]["settled"] == retry + 1
            owned = frame["views"]["Red_0"]["sessions"]
            assert any(s["hostname"] == TARGET_A for s in owned) == (provision == "valid")
            assert len(frame["views"]["Red_1"]["sessions"]) == 1
            assert not frame["views"]["Red_1"]["scan_cache"]["0"]
            if provision == "valid":
                native = next(h for h in frame["truth"]["hosts"] if h["id"] == TARGET_A)
                assert any(s["agent"] == "Red_0" and s["username"] == "user" for s in native["sessions"])
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
def test_complementary_branches_verified_delivery_and_complete_two_targets(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / "native.log", "enterprise_cc4_research")
        try:
            await bridge.start()
            frame = await bridge.call("create", config=config(recipe="combine"))
            roles = frame["truth"]["research_truth"]["roles"]
            addresses = {role: ip(frame, host) for role, host in roles.items()}
            entry = roles["entry"]
            for actor in ("Red_0", "Red_1"):
                frame = await finish(bridge, {"action": "InspectArtifacts", "target": entry}, actor)
            # A bridge grants a usable source, never the independent token.
            frame = await finish(bridge, {"action": "DiscoverNetworkServices", "target": addresses["bridge"]})
            frame = await finish(bridge, {"action": "AttemptAccess", "method": "web_rfi", "target": addresses["bridge"]})
            assert action(frame)["outcome"] == "TRUE"
            frame = await finish(bridge, {"action": "PrivilegeEscalate", "target": roles["bridge"]})
            frame = await finish(bridge, {"action": "EstablishPivot", "target": roles["bridge"]})
            pivot = next(s["id"] for s in frame["views"]["Red_0"]["sessions"] if s["hostname"] == roles["bridge"] and s["controller"])
            frame = await finish(bridge, {"action": "InspectArtifacts", "session": pivot, "target": roles["bridge"]})
            frame = await finish(bridge, {"action": "DiscoverNetworkServices", "session": pivot, "target": addresses["archive_target"]})
            for method in ("web_rfi", "ssh_weak_auth"):
                frame = await finish(bridge, {"action": "AttemptAccess", "session": pivot, "target": addresses["archive_target"], "method": method})
                assert action(frame)["outcome"] == "FALSE"
            assert not frame["views"]["Red_0"]["possessed_tokens"]
            # B finds a token locally, but its entry source cannot reach A.
            frame = await finish(bridge, {"action": "DiscoverNetworkServices", "target": addresses["archive"]}, "Red_1")
            frame = await finish(bridge, {"action": "AttemptAccess", "target": addresses["archive"], "method": "ssh_weak_auth"}, "Red_1")
            assert action(frame, "Red_1")["outcome"] == "TRUE"
            shell = next(s["id"] for s in frame["views"]["Red_1"]["sessions"] if s["hostname"] == roles["archive"])
            frame = await finish(bridge, {"action": "InspectArtifacts", "session": shell, "target": roles["archive"]}, "Red_1")
            eid = frame["observations"]["Red_1"]["evidence_id"]
            token = next(e["token_ref"] for e in evidence(frame, "Red_1") if e.get("token_ref"))
            frame = await finish(bridge, {"action": "Probe", "probe": "connectivity", "port": 22, "target": addresses["archive_target"]}, "Red_1")
            assert evidence(frame, "Red_1")[0]["response"] == "timeout"
            forged = await bridge.call("ingest_intel", sender="Red_0", recipient="Red_0", evidence_ids=[eid])
            assert not forged["accepted_evidence"] and not forged["view"]["possessed_tokens"]
            before = frame["views"]["Red_0"]
            delivered = await bridge.call("ingest_intel", sender="Red_1", recipient="Red_0", evidence_ids=[eid])
            assert delivered["view"]["possessed_tokens"] == [token]
            assert delivered["view"]["sessions"] == before["sessions"]
            assert delivered["view"]["scan_cache"] == before["scan_cache"]
            assert all("Sessions" not in fields and "Processes" not in fields for fields in delivered["address_fragment"].values())
            frame = await finish(bridge, {"action": "AttemptAccess", "session": pivot, "target": addresses["archive_target"], "method": "credential_login", "token_ref": token})
            assert action(frame)["outcome"] == "TRUE"
            frame = await finish(bridge, {"action": "PrivilegeEscalate", "session": pivot, "target": TARGET_A})
            assert TARGET_A in frame["score"]["privileged_hosts"]
            # B's separate application branch supports parallel objective B.
            frame = await finish(bridge, {"action": "DiscoverNetworkServices", "target": addresses["app"]}, "Red_1")
            frame = await finish(bridge, {"action": "AttemptAccess", "target": addresses["app"], "method": "web_rfi"}, "Red_1")
            assert action(frame, "Red_1")["outcome"] == "TRUE"
            frame = await finish(bridge, {"action": "PrivilegeEscalate", "target": roles["app"]}, "Red_1")
            frame = await finish(bridge, {"action": "EstablishPivot", "target": roles["app"]}, "Red_1")
            pivot_b = next(s["id"] for s in frame["views"]["Red_1"]["sessions"] if s["hostname"] == roles["app"] and s["controller"])
            frame = await finish(bridge, {"action": "InspectArtifacts", "session": pivot_b, "target": roles["app"]}, "Red_1")
            token_b = next(e["token_ref"] for e in evidence(frame, "Red_1") if e.get("token_ref"))
            frame = await finish(bridge, {"action": "DiscoverNetworkServices", "session": pivot_b, "target": addresses["parallel_target"]}, "Red_1")
            frame = await finish(bridge, {"action": "AttemptAccess", "session": pivot_b, "target": addresses["parallel_target"], "method": "credential_login", "token_ref": token_b}, "Red_1")
            assert action(frame, "Red_1")["outcome"] == "TRUE"
            frame = await finish(bridge, {"action": "PrivilegeEscalate", "session": pivot_b, "target": TARGET_B}, "Red_1")
            assert frame["score"]["mission_success"]
            assert frame["tick"] == frame["native_step_count"]
        finally:
            await bridge.close()
    asyncio.run(check())
