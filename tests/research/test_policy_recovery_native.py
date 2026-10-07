"""Actual programmed recovery from a single observed-response mechanism."""
import asyncio
import pytest
from backend.app.runs import Run
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig
from tests.research.helpers import config


@pytest.mark.engine
@pytest.mark.parametrize('mode', ['patch_rfi', 'restore'])
def test_policy_reinvestigates_or_reacquires_after_native_response(tmp_path, mode):
    async def check():
        cfg = config(recipe='recover',workers=1,credential_variant='valid',
                     change={'mode':mode,'response_budget':1,'response_delay':4})
        cfg['scenario']['mission']={'hold_ticks':3}
        run = Run(EpisodeConfig.model_validate(cfg), Store(tmp_path))
        try:
            await run.initialize()
            for _ in range(70):
                if run.meta['status']=='completed':
                    break
                await run.advance()
            assert run.frames[-1]['score']['mission_success']
            response = run.frames[-1]['truth']['research_truth']['response']
            effects = [e for e in response['history'] if e['type']=='research_defender_effect']
            assert response['used']==1 and len(effects)==1 and effects[0]['outcome']=='TRUE'
            records = run.frames[-1]['private_views']['Red_0']['research_evidence']
            if mode=='patch_rfi':
                observed = [r for r in records if r.get('probe')=='service_behavior']
                assert any(r['response']=='external_import_accepted' for r in observed)
                assert any(r['response']=='external_import_refused' for r in observed)
                assert any(a['proposal'].get('method')=='credential_login' and a['outcome']=='TRUE'
                           for f in run.frames for a in f['actions'])
            else:
                events = run.frames[-1]['private_views']['Red_0']['beliefs']['events']
                assert any(e['type']=='access_lost' for e in events)
                assert any(e['type']=='access_recovered' for e in events)
                assert run.meta['metrics']['observed_access_losses']>=1
                assert any(not r['censored'] for r in run.meta['metrics']['recovery_records'])
        finally:
            await run.stop()
    asyncio.run(check())
