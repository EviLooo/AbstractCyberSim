"""Terminal policy failures through a native Run, with mocked HTTP only."""
import asyncio

import httpx
import pytest

from backend.app.runs import Run
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig
from tests.research.helpers import config


@pytest.mark.engine
@pytest.mark.parametrize('kind,reason,calls', [('refusal','provider_refusal',1),
                         ('invalid','invalid_decision',2),('context','context_limit',0),
                         ('budget','token_budget',0),('transport','runtime_error',1)])
def test_provider_outcome_is_not_a_retryable_engine_error(tmp_path,monkeypatch,kind,reason,calls):
    requests=[]
    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {'message':{'refusal':'mock refusal'} if kind=='refusal' else {'content':'not valid JSON'},
                    'prompt_eval_count':10,'eval_count':4}
    class Client:
        def __init__(self,**kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def post(self,*args,**kwargs):
            requests.append(1)
            if kind=='transport':
                raise httpx.ConnectError('Mocked local transport unavailable')
            return Response()
    monkeypatch.setattr(httpx,'AsyncClient',Client)
    async def check():
        cfg=config(workers=1)
        cfg['cognition'].update(provider='ollama',model='mock-only',scripted_policy='legacy',
            max_context_bytes=4000 if kind=='context' else 128000,
            max_team_tokens=1000 if kind=='budget' else 2000000)
        run=Run(EpisodeConfig.model_validate(cfg),Store(tmp_path))
        try:
            await run.initialize()
            if kind=='transport':
                with pytest.raises(httpx.ConnectError):
                    await run.advance()
            else:
                await run.advance()
            assert run.meta['status']==('errored' if kind=='transport' else 'completed') and run.meta['termination_reason']==reason
            assert run.meta['tick']==0 and not run.meta['metrics']['success']
            assert len(requests)==calls
            if kind=='transport':
                assert run.meta['metrics']['unknown_usage_calls']==1 and run.meta['metrics']['charged_tokens']>0
            else:
                assert run.meta['metrics']['charged_tokens']==calls*14
        finally:
            await run.stop()
    asyncio.run(check())
