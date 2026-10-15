"""An unverified world remains inspectable without executing any policy."""
import json

import pytest
from fastapi.testclient import TestClient
from backend.app.api import create_app
from tests.research.helpers import config


@pytest.mark.engine
def test_native_unverified_evaluation_saves_replay_and_rejects_controls(tmp_path):
    cfg = config(workers=1)
    cfg['purpose'] = 'evaluation'
    cfg['schedule']['max_ticks'] = 1
    with TestClient(create_app(tmp_path)) as client:
        created = client.post('/api/runs', json=cfg)
        assert created.status_code == 409
        run = client.get('/api/runs').json()[0]
        assert run['status'] == 'errored' and run['termination_reason'] == 'unverified_world'
        assert run['feasibility_status'] == 'unverified' and run['tick'] == 0
        replay = client.get(f"/api/runs/{run['id']}/frame?tick=0")
        assert replay.status_code == 200
        assert replay.json()['status'] == 'errored'
        assert not replay.json()['score']['mission_success']
        assert replay.json()['cognition']['calls'] == 0
        assert client.post(f"/api/runs/{run['id']}/step", json={'overrides':{}}).status_code == 409
        assert client.post(f"/api/runs/{run['id']}/control/start").status_code == 409
        directory = tmp_path / 'runs' / run['id']
        manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
        world = json.loads((directory / 'world.json').read_text(encoding='utf-8'))
        assert manifest['qualification']['status'] == 'unverified'
        assert world['world_id'] == run['world_id']
        assert len(list((directory/'frames').glob('*.json'))) == 1
        assert not (directory/'provider-transcripts.jsonl').exists()
        assert client.get(f"/api/runs/{run['id']}/export").status_code == 200
