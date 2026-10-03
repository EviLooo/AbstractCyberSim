"""Observable organization invariants on hand-built private-knowledge fixtures."""
import asyncio
import copy
import json

import pytest

from backend.app.knowledge import PrivateMemory
from backend.app.policies import Organization, candidates, key
from backend.app.runs import RunManager
from backend.app.storage import Store
from backend.app.transport import MessageBus
from packages.contracts.models import CommunicationConfig, EpisodeConfig


def memory(actor, addresses=("10.0.0.2", "10.0.0.3"), controller=0):
    m = PrivateMemory(actor)
    m.view = {"actor": actor, "known": {"ip_address": list(addresses), "subnet": [], "hostname": ["User0"]}, "sessions": [{"id": controller, "hostname": "User0", "active": True, "controller": True, "privileged": True}], "scan_cache": {str(controller): {}}}
    return m


def report(m, tick=1):
    return {"sender": m.actor, "kind": "report", "created_tick": tick, "evidence_ids": [f"{m.actor}:0:0"], "payload": {"candidates": candidates(m), "sessions": copy.deepcopy(m.view["sessions"]), "recent_actions": copy.deepcopy(m.history)}}


def test_privileged_remote_foothold_still_requires_native_host_inspection():
    m = memory("Red_0", addresses=())
    remote = {"id": 1, "hostname": "Enterprise2", "active": True, "controller": False, "privileged": True}
    m.view["sessions"].extend([remote, dict(remote, id=2)])
    m.view["known"]["hostname"].append("Enterprise2")
    options = candidates(m)
    assert len(options) == 1
    assert options[0]["action"] == "PrivilegeEscalate" and options[0]["target"] == "Enterprise2"
    m.history.append({"proposal": options[0], "valid": True, "outcome": "TRUE"})
    assert candidates(m) == []


def test_hierarchy_assigns_distinct_branch_tasks_from_delivered_reports():
    config = EpisodeConfig()
    workers = ["Red_0", "Red_1"]
    org = Organization(config, workers)
    a, b = memory(workers[0]), memory(workers[1], controller=7)
    assert org.scripted_assignments() == {}
    org.coordinator_view([report(a), report(b)], 2)
    assigned = org.scripted_assignments()
    assert set(assigned) == set(workers)
    assert len({key(t["proposal"]) for t in assigned.values()}) == 2
    assert assigned["Red_1"]["proposal"]["session"] == 7
    # Reports received by the leader do not directly assign a worker a task.
    assert org.preferred(a, 2)["action"] == "Sleep"
    a.receive([{"kind": "assignment", "created_tick": 2, "payload": assigned[a.actor]}])
    assert key(org.preferred(a, 3)) == key(assigned[a.actor]["proposal"])


def test_scan_completion_does_not_complete_another_actors_native_cache():
    org = Organization(EpisodeConfig(), ["Red_0", "Red_1"])
    a, b = memory("Red_0", ("10.0.0.2",)), memory("Red_1", ("10.0.0.2",))
    done = candidates(a)[0]
    a.history.append({"proposal": done, "valid": True, "outcome": "TRUE"})
    org.coordinator_view([report(a), report(b)], 2)
    assigned = org.scripted_assignments()
    assert set(assigned) == {"Red_1"}
    assert assigned["Red_1"]["proposal"]["action"] == "DiscoverNetworkServices"


def test_swarm_ties_use_delivered_claims_and_expire_without_a_shared_allocator():
    config = EpisodeConfig()
    config.team.architecture = "swarm"
    org = Organization(config, ["Red_0", "Red_1"])
    worker = memory("Red_1", ("10.0.0.2",))
    proposal = org.preferred(worker, 1)
    bus = MessageBus(config.communication, org.actors, "swarm")
    bus.enqueue("Red_0", ["Red_1"], "claim", {"action_key": key(proposal)}, [], 1)
    worker.receive(bus.deliver(1)[0][worker.actor])
    assert org.preferred(worker, 1)["action"] == "DiscoverNetworkServices"
    worker.receive(bus.deliver(2)[0][worker.actor])
    assert org.preferred(worker, 2)["action"] == "Sleep"
    assert org.preferred(worker, 1 + config.team.claim_ttl + 1)["action"] == "DiscoverNetworkServices"


def test_seeded_loss_copy_charges_and_message_status_reconcile():
    def trace():
        bus = MessageBus(CommunicationConfig(loss_probability=.5, seed=19), ["Red_0", "Red_1", "Red_2"], "swarm")
        for tick in range(1, 9):
            copies = bus.enqueue("Red_0", bus.neighbors("Red_0"), "claim", {"action_key": "scan:x"}, [], tick)
            assert len(copies) == 2 and sum(m["bytes"] for m in copies) > copies[0]["bytes"]
            bus.deliver(tick)
        bus.deliver(9)
        messages = bus.snapshot()
        assert len(messages) == 16
        assert {m["status"] for m in messages} == {"delivered", "dropped_loss"}
        assert all(m["resolved_tick"] > m["created_tick"] for m in messages)
        return messages
    assert trace() == trace()


@pytest.mark.engine
def test_total_message_loss_keeps_leader_blind_but_swarm_can_act_locally(tmp_path):
    async def check():
        manager = RunManager(Store(tmp_path))
        try:
            for architecture in ["hierarchy", "swarm", "independent"]:
                config = EpisodeConfig()
                config.team.workers = 2
                config.team.architecture = architecture
                config.communication.loss_probability = 1
                meta = await manager.create(config)
                run = manager.get(meta["id"])
                for _ in range(3):
                    await run.advance()
                assert not run.organization.reports
                assert all(not m.inbox for m in run.memory.values())
                proposals = [a["proposal"]["action"] for f in run.frames[1:] for a in f["actions"]]
                if architecture == "hierarchy":
                    assert set(proposals) == {"Sleep"}
                else:
                    assert "DiscoverRemoteSystems" in proposals
                if architecture == "independent":
                    assert run.bus.messages == []
                else:
                    assert run.meta["metrics"]["message_dropped"] > 0
                await run.stop()
        finally:
            await manager.close()
    asyncio.run(check())


@pytest.mark.engine
def test_unassigned_decision_is_rejected_and_private_inputs_exclude_undelivered_intel(tmp_path):
    async def check():
        manager = RunManager(Store(tmp_path))
        config = EpisodeConfig()
        config.team.workers = 2
        config.communication.loss_probability = 1
        try:
            meta = await manager.create(config)
            run = manager.get(meta["id"])
            subnet = run.memory["Red_0"].view["known"]["subnet"][0]
            await run.advance({"Red_0": {"action": "DiscoverRemoteSystems", "target": subnet}})
            secret = next(ip for ip in run.memory["Red_0"].view["known"]["ip_address"] if ip not in run.memory["Red_1"].view["known"]["ip_address"])
            inputs = {}

            async def bad_worker(actor, view, preferred):
                inputs[actor] = copy.deepcopy(view)
                return {"action": "DiscoverNetworkServices", "session": 0, "target": secret}

            run.cognition.worker = bad_worker
            await run.advance()
            assert secret not in json.dumps(inputs["Red_1"])
            assert "truth" not in inputs["Red_0"] and "truth" not in inputs["Red_1"]
            assert not run.organization.reports
            for action in run.frames[-1]["actions"]:
                assert not action["valid"]
                assert action["native_action"] == "Sleep" and action["outcome"] == "UNKNOWN"
                assert "delivered assignment" in action["rejection"]
            assert run.meta["metrics"]["invalid_actions"] == 2
            tick = run.meta["tick"]
            with pytest.raises(ValueError, match="unknown actors"):
                await run.advance({"Blue": {"action": "Sleep"}})
            assert run.meta["tick"] == tick
        finally:
            await manager.close()
    asyncio.run(check())
