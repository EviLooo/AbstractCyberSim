"""A1 native paired inputs reach worker/leader HTTP serialization unchanged."""
import asyncio
import json

import httpx
import pytest

from backend.app.runs import Run
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig
from tests.research.helpers import config


@pytest.mark.engine
def test_identical_worker_and_coordinator_requests_before_distinguishing_evidence(tmp_path,monkeypatch):
    captured=[]
    class Response:
        def __init__(self,value): self.value=value
        def raise_for_status(self): pass
        def json(self):
            return {'message':{'content':json.dumps(self.value)},'prompt_eval_count':10,'eval_count':4}
    class Client:
        def __init__(self,**kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def post(self,url,json):
            captured.append(json)
            view=__import__('json').loads(json['messages'][1]['content'])
            return Response({actor:None for actor in view['workers']} if view.get('role')=='coordinator'
                            else {'action':'Sleep'})
    monkeypatch.setattr(httpx,'AsyncClient',Client)
    async def check():
        requests=[]
        for variant in ('import_enabled','import_disabled'):
            captured.clear()
            cfg=config(variant,workers=2,architecture='hierarchy',credential_variant='valid')
            cfg['cognition'].update(provider='ollama',model='mock-only',scripted_policy='legacy',max_team_tokens=2000000)
            run=Run(EpisodeConfig.model_validate(cfg),Store(tmp_path/variant))
            try:
                await run.initialize()
                await run.advance()
                await run.advance()
                data=json.dumps(captured,sort_keys=True,separators=(',',':'))
                assert all(word not in data for word in ('condition_variant','credential_variant','research_truth','witness','allowed_sources'))
                assert any('"role":"coordinator"' in item['messages'][1]['content'] for item in captured)
                assert 'Coordinator' not in run.frames[-1]['private_views']
                assert all(a['proposal']['action']=='Sleep' for f in run.frames for a in f['actions'])
                requests.append(data.encode('utf-8'))
            finally:
                await run.stop()
        assert requests[0]==requests[1]
    asyncio.run(check())
