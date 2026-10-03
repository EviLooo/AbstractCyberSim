"""Software lifecycle checks in temporary storage, not experimental studies."""
import asyncio
import json
import pytest
from backend.app.runs import RunManager
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig


@pytest.mark.engine
def test_hierarchy_waits_for_delivery_pause_replay_and_world_pairing(tmp_path):
    async def check():
        store = Store(tmp_path)
        manager = RunManager(store)
        config = EpisodeConfig()
        config.team.workers = 2
        try:
            meta = await manager.create(config)
            run = manager.get(meta["id"])
            assert meta["tick"] == 0 and meta["status"] == "ready"
            assert not run.task
            initial_hash = meta["world_id"]
            await run.advance()
            first = store.frame(run.id)
            assert all(a["proposal"]["action"] == "Sleep" for a in first["actions"])
            assert not first["coordinator"]["delivered_reports"]
            await run.advance()
            second = store.frame(run.id)
            assert second["coordinator"]["delivered_reports"]
            assert all(a["proposal"]["action"] == "Sleep" for a in second["actions"])
            await run.advance()
            third = store.frame(run.id)
            assert sum(a["proposal"]["action"] == "DiscoverRemoteSystems" for a in third["actions"]) == 1
            assert third["score"]["mission_success"] is False
            await run.stop()
            assert run.engine.process is None
            assert store.frame(run.id, 1)["tick"] == 1
            config.team.architecture = "swarm"
            second_meta = await manager.create(config)
            assert second_meta["world_id"] == initial_hash
            swarm = manager.get(second_meta["id"])
            await swarm.advance()
            swarm_frame = store.frame(swarm.id)
            assert swarm_frame["coordinator"] is None
            assert all(m["recipient"] != "Coordinator" for m in swarm_frame["messages"])
            assert any(a["proposal"]["action"] != "Sleep" for a in swarm_frame["actions"])
        finally:
            await manager.close()
        assert not (tmp_path / "provider-transcripts.jsonl").exists()
    asyncio.run(check())


@pytest.mark.engine
def test_evaluation_forbids_manual_action_and_run_config_is_frozen(tmp_path):
    async def check():
        store = Store(tmp_path)
        manager = RunManager(store)
        config = EpisodeConfig(purpose="evaluation")
        config.team.workers = 1
        try:
            meta = await manager.create(config)
            run = manager.get(meta["id"])
            with pytest.raises(ValueError, match="Manual actions"):
                await run.advance({"Red_0": {"action": "Sleep"}})
            assert run.meta["tick"] == 0
            frozen = json.loads((store.path(run.id) / "config.json").read_text())
            assert frozen["team"]["workers"] == 1
            config.team.workers = 2
            assert run.config.team.workers == 1
        finally:
            await manager.close()
    asyncio.run(check())
