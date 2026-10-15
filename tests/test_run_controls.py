"""Software lifecycle checks in temporary storage, not experimental studies."""
import asyncio
import json
import pytest
from backend.app.runs import RunManager
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig


@pytest.mark.engine
@pytest.mark.parametrize("architecture", ["hierarchy", "swarm"])
def test_background_pause_continue_matches_single_steps(tmp_path, architecture):
    async def check():
        manager = RunManager(Store(tmp_path))
        config = EpisodeConfig()
        config.team.architecture = architecture
        config.team.workers = 2
        try:
            direct_meta = await manager.create(config)
            direct = manager.get(direct_meta["id"])
            for _ in range(5):
                await direct.advance()
            background_meta = await manager.create(config)
            background = manager.get(background_meta["id"])
            assert background.meta["world_id"] == direct.meta["world_id"]
            original_call = background.engine.call

            async def boundary_call(method, **params):
                result = await original_call(method, **params)
                if method == "step" and result["tick"] == 4:
                    background.pause_requested = True
                return result

            background.engine.call = boundary_call
            background.start()
            await asyncio.wait_for(background.task, timeout=15)
            await background.pause()
            assert background.meta["status"] == "paused" and background.meta["tick"] == 4
            await background.advance()
            fields = ["tick", "native_step_count", "score", "truth", "observations", "views", "actions", "submission_order", "execution_trace", "messages", "coordinator"]
            for a, b in zip(direct.frames[1:], background.frames[1:]):
                assert {k: a[k] for k in fields} == {k: b[k] for k in fields}
        finally:
            await manager.close()
    asyncio.run(check())


@pytest.mark.engine
def test_tick_limit_is_censored_and_closes_native_process(tmp_path):
    async def check():
        manager = RunManager(Store(tmp_path))
        config = EpisodeConfig()
        config.schedule.max_ticks = 2
        try:
            meta = await manager.create(config)
            run = manager.get(meta["id"])
            await run.advance()
            await run.advance()
            assert run.meta["status"] == "completed"
            assert run.meta["termination_reason"] == "tick_limit"
            assert run.meta["metrics"]["time_to_success_censored"]
            assert run.meta["metrics"]["success_tick"] is None
            assert run.engine.process is None
            with pytest.raises(ValueError, match="closed"):
                await run.advance()
        finally:
            await manager.close()
    asyncio.run(check())


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
