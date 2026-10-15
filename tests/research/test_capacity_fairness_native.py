"""Bounded scheduling/accounting sensitivity, no model performance estimates."""
import asyncio
import json

import httpx
import pytest

from backend.app.runs import Run
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig
from tests.research.helpers import config


@pytest.mark.engine
@pytest.mark.parametrize('architecture', ['hierarchy','swarm'])
@pytest.mark.parametrize('mode', ['per_worker','team_cap_one'])
def test_native_capacity_busy_calls_and_all_reasoner_costs(tmp_path,monkeypatch,architecture,mode):
    requests=[]
    class Response:
        def __init__(self, decision): self.decision=decision
        def raise_for_status(self): pass
        def json(self):
            return {'message':{'content':json.dumps(self.decision)},'prompt_eval_count':10,'eval_count':4}
    class Client:
        def __init__(self,**kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def post(self,url,json):
            view=__import__('json').loads(json['messages'][1]['content'])
            requests.append(view)
            if view.get('role')=='coordinator':
                # Repeated legal local inspection is deliberate accounting input.
                return Response({r['sender']:next((p for p in r['payload']['candidates']
                    if p['action']=='InspectArtifacts'),None) for r in view['delivered_reports']})
            return Response(next(p for p in view['eligible_candidates'] if p['action']=='InspectArtifacts')
                            if architecture=='swarm' else view['suggested_action'])
    monkeypatch.setattr(httpx,'AsyncClient',Client)
    async def check():
        cfg=config(workers=2,architecture=architecture,credential_variant='valid')
        cfg['schedule']['mode']=mode
        cfg['cognition'].update(provider='ollama',model='mock-only',scripted_policy='legacy',
                                max_context_bytes=128000,max_team_tokens=2000000)
        run=Run(EpisodeConfig.model_validate(cfg),Store(tmp_path))
        try:
            await run.initialize()
            maximum=0
            for _ in range(12):
                before={a for a,m in run.memory.items() if m.view.get('pending_action')}
                start=len(requests)
                await run.advance()
                assert not any(v.get('actor') in before for v in requests[start:])
                frame=run.frames[-1]
                assert frame['tick']==frame['native_step_count']
                maximum=max(maximum,sum(bool(v['pending_action']) for v in frame['views'].values()))
                if mode=='team_cap_one':
                    assert maximum<=1
                assert run.cognition.used==len(requests)*14
            assert maximum== (1 if mode=='team_cap_one' else 2)
            usage=run.cognition.summary()['per_actor_usage']
            assert sum(v['charged_tokens'] for v in usage.values())==run.cognition.used
            assert ('Coordinator' in usage)==(architecture=='hierarchy')
            if architecture=='hierarchy':
                assert usage['Coordinator']['role']=='coordinator' and usage['Coordinator']['calls']>0
            assert any(not a['submitted'] and a['proposal']['action']!='Sleep'
                       for f in run.frames for a in f['actions'])
            assert not run.meta['metrics']['success']  # No claim about cognition or a winner.
        finally:
            await run.stop()
    asyncio.run(check())
