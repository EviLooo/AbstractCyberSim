import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from backend.app.evaluation import compare_runs, expand, metrics
from backend.app.knowledge import PrivateMemory
from backend.app.policies import Organization
from backend.app.transport import MessageBus
from packages.contracts.models import EpisodeConfig, ExperimentSpec, CommunicationConfig


def test_strict_config_and_real_matrix_without_execution():
    with pytest.raises(ValidationError):
        EpisodeConfig.model_validate({"schema_version": "1.0", "hidden_setting": True})
    with pytest.raises(ValidationError):
        EpisodeConfig.model_validate({"cognition": {"provider": "ollama"}})
    spec = ExperimentSpec(worker_counts=[2, 4], world_seeds=[101, 102], delays=[0, 1], losses=[0, .1], replicates=2)
    preview = expand(spec)
    assert preview["job_count"] == 64
    assert len({j["job_id"] for j in preview["jobs"]}) == 64
    pairs = {}
    for job in preview["jobs"]:
        pairs.setdefault(job["pair_key"], []).append(job)
        assert job["config"]["purpose"] == "evaluation"
    assert all(len(group) == 2 for group in pairs.values())


def test_delivery_delay_topology_loss_capacity_and_expiry():
    config = CommunicationConfig(extra_delay=1, loss_probability=0, envelopes_per_tick=1)
    bus = MessageBus(config, ["Red_0", "Red_1"], "hierarchy")
    with pytest.raises(ValueError):
        bus.enqueue("Red_0", ["Red_1"], "report", {}, [], 1)
    bus.enqueue("Coordinator", ["Red_0", "Red_1"], "assignment", {"target": "x"}, [], 1)
    assert not bus.deliver(2)[0]["Red_0"]
    delivered, changes = bus.deliver(3)
    assert len(delivered["Red_0"]) == 1
    assert {m["status"] for m in changes} == {"delivered", "dropped_capacity"}
    loss_bus = MessageBus(CommunicationConfig(loss_probability=1), ["Red_0", "Red_1"], "swarm")
    loss_bus.enqueue("Red_0", ["Red_1"], "claim", {}, [], 0)
    assert loss_bus.deliver(1)[1][0]["status"] == "dropped_loss"
    expired = MessageBus(CommunicationConfig(extra_delay=3, ttl=1), ["Red_0"], "hierarchy")
    expired.enqueue("Red_0", ["Coordinator"], "report", {}, [], 0)
    assert expired.deliver(2)[1][0]["status"] == "expired"


def test_private_knowledge_does_not_include_undelivered_peer_memory():
    a, b = PrivateMemory("Red_0"), PrivateMemory("Red_1")
    a.observe({"evidence_id": "e0", "tick": 0, "data": {"10.0.0.1": {"System info": {"Hostname": "secret"}}}}, {"actor": "Red_0"})
    b.observe({"evidence_id": "e1", "tick": 0, "data": {}}, {"actor": "Red_1"})
    assert "secret" not in json.dumps(b.public_view({}, {}))
    org = Organization(EpisodeConfig(), ["Red_0", "Red_1"])
    assert org.coordinator_view([], 1)["delivered_reports"] == []


def test_metrics_count_duplicates_once_and_keep_failure_censored():
    action = {"actor": "Red_0", "proposal": {"action": "DiscoverNetworkServices", "target": "10.0.0.1"}, "valid": True}
    frames = [{"score": {"mission_success": False}, "tick": 0, "messages": [], "actions": []}, {"score": {"mission_success": False}, "tick": 1, "messages": [], "actions": [action, dict(action, actor="Red_1")]}]
    result = metrics(frames, {"charged_tokens": 0})
    assert result["duplicate_actions"] == 1
    assert result["success_tick"] is None and result["time_to_success_censored"]


def test_compare_excludes_manual_and_does_not_invent_ci_for_one_world():
    def run(id, arch, manual=False):
        return {"id": id, "status": "completed", "manual_intervention": manual, "purpose": "evaluation", "world_id": "world1", "condition_hash": "same", "architecture": arch, "metrics": {"success": arch == "hierarchy", "charged_tokens": 10}}
    metadata = [run("a", "hierarchy"), run("b", "swarm"), run("c", "swarm", True)]
    result = compare_runs(metadata, ["a", "b", "c"])
    assert result["paired_worlds"] == 1
    assert result["success_difference"] == 1
    assert result["world_cluster_bootstrap_95_ci"] is None
    assert result["excluded"][0]["id"] == "c"


def test_checked_in_schemas_match_runtime():
    root = Path(__file__).resolve().parents[1]
    for model in [EpisodeConfig, ExperimentSpec]:
        stored = json.loads((root / "packages/contracts/schemas" / (model.__name__ + ".json")).read_text())
        assert stored == model.model_json_schema()
