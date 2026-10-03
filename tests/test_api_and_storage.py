import asyncio
import json
import httpx
import pytest
from backend.app.api import create_app
from backend.app.storage import Store


def test_api_startup_is_idle_and_planner_does_not_create_runs(tmp_path):
    async def check():
        app = create_app(tmp_path)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            assert (await client.get("/api/runs")).json() == []
            health = (await client.get("/api/health")).json()
            assert health["experiments_started_automatically"] is False
            preview = await client.post("/api/experiments/preview", json={})
            assert preview.status_code == 200
            assert preview.json()["job_count"] == 8
            assert (await client.get("/api/runs")).json() == []
            assert not app.state.manager.live
            blocked = await client.post("/api/runs", headers={"Origin": "https://unrelated.example"}, json={})
            assert blocked.status_code == 403
            bad = await client.post("/api/runs", json={"team": {"workers": 999}})
            assert bad.status_code == 422
    asyncio.run(check())


def test_storage_path_validation_and_restart_marks_native_state_interrupted(tmp_path):
    store = Store(tmp_path)
    with pytest.raises(KeyError):
        store.path("../config")
    run_id = "a" * 32
    store.update({"id": run_id, "status": "paused", "tick": 0})
    store.write_json(store.path(run_id) / "config.json", {"schema_version": "1.0"})
    store.recover()
    assert store.get(run_id)["status"] == "interrupted"
    assert json.loads((store.path(run_id) / "config.json").read_text())["schema_version"] == "1.0"
