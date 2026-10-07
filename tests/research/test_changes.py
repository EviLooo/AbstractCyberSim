import asyncio
import copy
import json

import pytest
from backend.app.bridge import EngineBridge
from tests.research.helpers import config, finish, ip, action, evidence, TARGET_A


def recovery(mode, delay=8):
    data = config(recipe="recover", credential_variant="valid", change={"mode": mode, "response_budget": 1, "response_delay": delay})
    data["scenario"]["mission"] = {"hold_ticks": 3}
    return data


@pytest.mark.engine
def test_patch_rechecks_an_admitted_access_at_native_completion(tmp_path):
    async def check():
        outcomes = []
        for mode in ("none", "patch_rfi"):
            bridge = EngineBridge(tmp_path / (mode + '.log'), 'enterprise_cc4_research')
            try:
                await bridge.start()
                cfg = recovery(mode, delay=2) if mode != 'none' else config(workers=2)
                frame = await bridge.call('create', config=cfg)
                target = ip(frame, TARGET_A)
                entry = frame['views']['Red_0']['sessions'][0]['hostname']
                await finish(bridge, {'action':'InspectArtifacts', 'target':entry})
                await finish(bridge, {'action':'DiscoverNetworkServices', 'target':target})
                frame = await bridge.call('step', proposals={'Red_0': {'action':'AttemptAccess', 'method':'web_rfi', 'target':target}})
                assert action(frame)['outcome'] == 'IN_PROGRESS'
                admitted = action(frame)['started_tick']
                for _ in range(3):
                    frame = await bridge.call('step', proposals={})
                completed = action(frame)
                assert completed['remaining_ticks'] == 0 and completed['lifecycle'] == 'completed'
                outcomes.append(completed['outcome'])
                resources = frame['views']['Red_0']['access_resources']
                assert resources['reserved'] == resources['settled'] == 1
                if mode == 'patch_rfi':
                    effects = [e for e in frame['truth']['research_truth']['response']['history'] if e['type']=='research_defender_effect']
                    assert len(effects) == 1 and admitted < effects[0]['effect_tick'] <= frame['tick']
                    assert not any(s['hostname']==TARGET_A for s in frame['views']['Red_0']['sessions'])
            finally:
                await bridge.close()
        assert outcomes == ['TRUE', 'FALSE']
    asyncio.run(check())


@pytest.mark.engine
def test_patch_and_access_same_tick_follow_recorded_native_order(tmp_path):
    """A causal tie is resolved by CC4's real joint-action order, not the adapter."""
    async def check():
        bridge = EngineBridge(tmp_path / 'completion-tie.log', 'enterprise_cc4_research')
        try:
            await bridge.start()
            # The custom Patch has native duration one; signal3 + delay6 = effect9.
            frame = await bridge.call('create', config=recovery('patch_rfi', delay=6))
            target = ip(frame, TARGET_A)
            entry = frame['views']['Red_0']['sessions'][0]['hostname']
            await finish(bridge, {'action':'InspectArtifacts', 'target':entry})
            await finish(bridge, {'action':'DiscoverNetworkServices', 'target':target})
            await finish(bridge, {'action':'Probe', 'probe':'service_behavior', 'port':80, 'target':target})
            frame = await finish(bridge, {'action':'AttemptAccess', 'method':'web_rfi', 'target':target})
            effects = [e for e in frame['truth']['research_truth']['response']['history']
                       if e['type'] == 'research_defender_effect']
            assert len(effects) == 1 and effects[0]['effect_tick'] == frame['tick'] == 9
            trace = [e for e in frame['execution_trace'] if e['phase'] == 'joint']
            patch = next(i for i, e in enumerate(trace) if e['action'] == 'PatchService ' + TARGET_A)
            access = next(i for i, e in enumerate(trace) if e['actor'] == 'Red_0')
            assert action(frame)['outcome'] == ('FALSE' if patch < access else 'TRUE')
            resources = frame['views']['Red_0']['access_resources']
            assert resources['reserved'] == resources['settled'] == 1
            (tmp_path / 'completion-tie.json').write_text(json.dumps({
                'tick': frame['tick'], 'trace': trace, 'effects': effects,
                'outcome': action(frame)['outcome'], 'resources': resources}, indent=2))
            frame = await finish(bridge, {'action':'AttemptAccess', 'method':'web_rfi', 'target':target})
            assert action(frame)['outcome'] == 'FALSE'
            assert frame['views']['Red_0']['access_resources']['settled'] == 2
            assert frame['truth']['research_truth']['response']['used'] == 1
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
def test_patch_native_condition_persists_and_old_reports_are_not_rewritten(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / "native.log", "enterprise_cc4_research")
        try:
            await bridge.start()
            frame = await bridge.call("create", config=recovery("patch_rfi"))
            target = ip(frame, TARGET_A)
            entry = frame["views"]["Red_0"]["sessions"][0]["hostname"]
            frame = await finish(bridge, {"action": "InspectArtifacts", "target": entry})
            token = next(e["token_ref"] for e in evidence(frame) if e.get("token_ref"))
            frame = await finish(bridge, {"action": "DiscoverNetworkServices", "target": target})
            frame = await finish(bridge, {"action": "Probe", "probe": "service_behavior", "port": 80, "target": target})
            old = copy.deepcopy(frame["observations"]["Red_0"])
            assert evidence(frame)[0]["response"] == "external_import_accepted"
            await bridge.call("ingest_intel", sender="Red_0", recipient="Red_1", evidence_ids=[old["evidence_id"]])
            frame = await finish(bridge, {"action": "AttemptAccess", "method": "web_rfi", "target": target})
            assert action(frame)["outcome"] == "TRUE"
            cache = copy.deepcopy(frame["views"]["Red_0"]["scan_cache"])
            owned = copy.deepcopy(frame["views"]["Red_0"]["sessions"])
            for _ in range(10):
                if frame["truth"]["research_truth"]["response"]["used"] and frame["truth"]["research_truth"]["response"]["inflight"] is None:
                    break
                frame = await bridge.call("step", proposals={})
            response = frame["truth"]["research_truth"]["response"]
            assert response["used"] == 1
            assert response["history"][-1]["type"] == "research_defender_effect"
            assert response["history"][-1]["outcome"] == "TRUE"
            assert frame["views"]["Red_0"]["scan_cache"] == cache
            assert frame["views"]["Red_0"]["sessions"] == owned
            still_old = await bridge.call("ingest_intel", sender="Red_0", recipient="Red_1", evidence_ids=[old["evidence_id"]])
            assert any(e["response"] == "external_import_accepted" for h in still_old["evidence"][0]["data"].values() for e in h.get("Research evidence", []))
            frame = await finish(bridge, {"action": "Probe", "probe": "service_behavior", "port": 80, "target": target})
            assert evidence(frame)[0]["response"] == "external_import_refused"
            for _ in range(3):
                frame = await finish(bridge, {"action": "AttemptAccess", "method": "web_rfi", "target": target})
                assert action(frame)["outcome"] == "FALSE"
            frame = await finish(bridge, {"action": "AttemptAccess", "method": "credential_login", "target": target, "token_ref": token})
            assert action(frame)["outcome"] == "TRUE"
            assert frame["truth"]["research_truth"]["response"]["used"] == 1
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
def test_native_restore_loses_pivot_cache_resets_hold_and_reacquires(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / "native.log", "enterprise_cc4_research")
        try:
            await bridge.start()
            frame = await bridge.call("create", config=recovery("restore"))
            target = ip(frame, TARGET_A)
            entry = frame["views"]["Red_0"]["sessions"][0]["hostname"]
            frame = await finish(bridge, {"action": "InspectArtifacts", "target": entry})
            frame = await finish(bridge, {"action": "DiscoverNetworkServices", "target": target})
            frame = await finish(bridge, {"action": "AttemptAccess", "method": "web_rfi", "target": target})
            frame = await finish(bridge, {"action": "PrivilegeEscalate", "target": TARGET_A})
            frame = await finish(bridge, {"action": "EstablishPivot", "target": TARGET_A})
            pivot = next(s["id"] for s in frame["views"]["Red_0"]["sessions"] if s["hostname"] == TARGET_A and s["controller"])
            subnet = frame["views"]["Red_0"]["known"]["subnet"][0]
            frame = await finish(bridge, {"action": "DiscoverRemoteSystems", "session": pivot, "target": subnet})
            for _ in range(10):
                if not any(s["hostname"] == TARGET_A for s in frame["views"]["Red_0"]["sessions"]):
                    break
                frame = await bridge.call("step", proposals={})
            assert not any(s["hostname"] == TARGET_A for s in frame["views"]["Red_0"]["sessions"])
            assert str(pivot) not in frame["views"]["Red_0"]["scan_cache"]
            assert TARGET_A not in frame["score"]["privileged_hosts"]
            assert not frame["score"]["mission_success"]
            assert frame["score"]["mission"]["reset_count"] >= 1
            frame = await finish(bridge, {"action": "AttemptAccess", "method": "web_rfi", "target": target})
            assert action(frame)["outcome"] == "TRUE"
            frame = await finish(bridge, {"action": "PrivilegeEscalate", "target": TARGET_A})
            frame = await finish(bridge, {"action": "EstablishPivot", "target": TARGET_A})
            new = next(s["id"] for s in frame["views"]["Red_0"]["sessions"] if s["hostname"] == TARGET_A and s["controller"])
            assert frame["views"]["Red_0"]["scan_cache"][str(new)] == {}
            assert frame["truth"]["research_truth"]["response"]["used"] == 1
        finally:
            await bridge.close()
    asyncio.run(check())
