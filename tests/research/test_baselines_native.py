"""Bounded native qualification; these fixtures are not scientific findings."""
import asyncio
import pytest
from backend.app.runs import Run
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig
from tests.research.helpers import config


@pytest.mark.engine
@pytest.mark.parametrize('policy', ['fixed_workflow', 'observed_planner'])
def test_public_catalog_control_completes_diagnostic_fixture(tmp_path, policy):
    async def check():
        cfg = config('import_disabled', workers=1, credential_variant='valid')
        cfg['cognition']['scripted_policy'] = policy
        run = Run(EpisodeConfig.model_validate(cfg), Store(tmp_path))
        try:
            await run.initialize()
            for _ in range(60):
                if run.meta['status']=='completed':
                    break
                await run.advance()
            assert run.frames[-1]['score']['mission_success']
            assert run.cognition.calls == 0
            assert run.frames[-1]['views']['Red_0']['access_resources']['reserved'] <= cfg['resources']['team_access_attempts']
            traces = [f['decisions']['Red_0'] for f in run.frames if 'Red_0' in f.get('decisions', {})]
            assert traces and all(t['policy']==policy and t['version']=='1.0' for t in traces)
            if policy=='observed_planner':
                assert any(t['plans'] for t in traces)
                assert all(p['expansions']<=128 and 'optimistic' in p['estimate'] for t in traces for p in t['plans'])
        finally:
            await run.stop()
    asyncio.run(check())
