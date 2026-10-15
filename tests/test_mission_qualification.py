"""Fixed-world software acceptance fixtures, never a research experiment matrix."""
import asyncio

import pytest

from backend.app.runs import RunManager
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig


@pytest.mark.engine
@pytest.mark.parametrize("architecture", ["hierarchy", "swarm", "independent"])
@pytest.mark.parametrize("workers", [1, 2, 8])
def test_scripted_team_completes_native_operational_mission(tmp_path, architecture, workers):
    async def check():
        store = Store(tmp_path)
        manager = RunManager(store)
        config = EpisodeConfig()
        config.team.architecture = architecture
        config.team.workers = workers
        config.scenario.defender = "monitor"
        config.scenario.targets = ["Enterprise2", "Op_Server0"]
        config.schedule.max_ticks = 100
        try:
            meta = await manager.create(config)
            run = manager.get(meta["id"])
            while run.meta["status"] not in {"completed", "errored"}:
                await run.advance()
            trace = [(f["tick"], [(a["actor"], a["proposal"]["action"], a["proposal"].get("target"), a["outcome"]) for a in f["actions"]]) for f in run.frames]
            assert run.meta["termination_reason"] == "mission_success", trace
            final = store.frame(run.id)
            assert set(config.scenario.targets) <= set(final["score"]["privileged_hosts"])
            assert final["score"]["targets_reached"] == 2
            assert final["score"]["mission_success"]
            assert not run.meta["manual_intervention"]
            assert run.cognition.summary()["calls"] == 0
            assert run.engine.process is None
            # Native filters Sleep from execution. Every non-Sleep action is
            # executed once and Monitor is an end-turn action once per joint tick.
            for frame in run.frames[1:]:
                joint = [e["actor"] for e in frame["execution_trace"] if e["phase"] == "joint"]
                expected = {a["actor"] for a in frame["actions"] if a["valid"] and a["native_action"] != "Sleep"}
                assert set(joint) == expected and len(joint) == len(expected)
                assert sum(e["actor"] == "Blue" and e["phase"] == "end_turn" and e["action"] == "Monitor" for e in frame["execution_trace"]) == 1
                assert frame["native_step_count"] == frame["tick"]
                reached = set(config.scenario.targets) & set(frame["score"]["privileged_hosts"])
                assert frame["score"]["targets_reached"] == len(reached)
                assert frame["score"]["mission_success"] == (len(reached) == 2)
        finally:
            await manager.close()
    asyncio.run(check())
