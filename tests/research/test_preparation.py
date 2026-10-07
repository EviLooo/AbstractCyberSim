import asyncio
import httpx
from backend.app.preparation import prepare_pilot
from backend.app.api import create_app
from packages.contracts.models import ExperimentSpec
from backend.app.diagnostics import structure
from packages.contracts.models import EpisodeConfig
from tests.research.helpers import config


def test_pilot_preparation_api_and_cli_shape_start_no_engine_or_model(tmp_path,monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('Preparation must not execute')
    monkeypatch.setattr('backend.app.bridge.EngineBridge.start',forbidden)
    monkeypatch.setattr('backend.app.providers.Cognition.complete',forbidden)
    cfg=config(workers=2,architecture='hierarchy')
    cfg['cognition'].update(provider='ollama',model='mock-only',scripted_policy='legacy')
    spec=ExperimentSpec.model_validate({'base':cfg,'architectures':['hierarchy','swarm'],
        'worker_counts':[2],'world_seeds':[100],'replicates':1})
    report=prepare_pilot(spec)
    assert report['job_count']==2 and not report['executed']
    assert report['provider_request_upper_bound']==180*(5+4)
    assert report['team_token_upper_bound']==2*spec.base.cognition.max_team_tokens
    assert list(report['mechanism_checklist'])==['investigate']
    async def check():
        app=create_app(tmp_path)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
                response=await client.post('/api/experiments/prepare-pilot',json=spec.model_dump())
                assert response.status_code==200 and response.json()==report
                assert (await client.get('/api/runs')).json()==[]
    asyncio.run(check())


def test_research_structure_uses_actual_research_settings():
    cfg=config(recipe='recover',change={'mode':'restore','response_budget':1,'response_delay':6},
               evidence={'observation_delay':2,'stale_after':8})
    described=structure(EpisodeConfig.model_validate(cfg),{})
    assert described['observation_delay']==2 and described['change_mode']=='restore'
    assert described['shared_response_budget']==1 and described['response_delay']==6
    assert 'reactive_restore' not in described and 'gateway_layers' not in described
