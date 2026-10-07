"""Scheduling checks use fake terminal outcomes; one fixture uses real CC4."""
import asyncio
import uuid
import json

import pytest

from backend.app.batches import Batch
from backend.app.runs import Run
from backend.app.storage import digest
from backend.app.evaluation import expand
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig, ExperimentSpec
from tests.research.helpers import config


def plan(seeds=(100,101)):
    cfg = config(workers=1)
    return expand(ExperimentSpec.model_validate({'base':cfg,'architectures':['independent'],
                  'worker_counts':[1],'world_seeds':list(seeds)}))


def test_saved_queue_resumes_scheduling_without_retrying_ordinary_failure(tmp_path):
    store = Store(tmp_path)
    batch = Batch.create(store, plan())
    calls = []
    class FakeRun:
        def __init__(self, cfg, store):
            self.id=uuid.uuid4().hex
            self.meta={'status':'ready','termination_reason':None}
            calls.append(self.id)
        async def initialize(self):
            pass
        async def advance(self):
            self.meta.update(status='completed', termination_reason='tick_limit', metrics={'success':False})
        async def stop(self):
            return self.meta
    first = asyncio.run(batch.execute(max_jobs=1, technical_retries=2, run_factory=FakeRun))
    assert first['status']=='paused' and len(calls)==1
    assert first['jobs'][0]['status']=='completed' and len(first['jobs'][0]['attempts'])==1
    second = asyncio.run(batch.execute(max_jobs=1, run_factory=FakeRun))
    assert second['status']=='completed' and len(calls)==2
    assert second['jobs'][0]['attempts']==first['jobs'][0]['attempts']
    assert second['jobs'][0]['attempts'][0]['id']!=second['jobs'][1]['attempts'][0]['id']
    assert Batch.create(store, plan()).id==batch.id


def test_stop_resume_creates_a_new_episode_attempt_not_a_native_checkpoint(tmp_path):
    batch = Batch.create(Store(tmp_path), plan((100,)))
    stop_once = [True]
    class FakeRun:
        def __init__(self, cfg, store):
            self.id=uuid.uuid4().hex
            self.meta={'status':'ready','termination_reason':None}
        async def initialize(self):
            pass
        async def advance(self):
            if stop_once[0]:
                stop_once[0]=False
                batch.request_stop()
            else:
                self.meta.update(status='completed',termination_reason='mission_success')
        async def stop(self):
            if self.meta['status'] in ('ready','running'):
                self.meta.update(status='stopped',termination_reason='user_stop')
    stopped = asyncio.run(batch.execute(run_factory=FakeRun))
    assert stopped['status']=='paused' and stopped['jobs'][0]['status']=='pending'
    resumed = asyncio.run(batch.execute(run_factory=FakeRun))
    attempts = resumed['jobs'][0]['attempts']
    assert resumed['status']=='completed' and len(attempts)==2
    assert attempts[0]['run_id']!=attempts[1]['run_id'] and attempts[0]['id']!=attempts[1]['id']


def test_live_queue_is_rejected_before_any_episode_is_constructed(tmp_path):
    planned = plan((100,))
    planned['jobs'][0]['config']['cognition'].update(provider='ollama',scripted_policy='legacy',model='mock-only')
    batch = Batch.create(Store(tmp_path), planned)
    def forbidden(*args):
        raise AssertionError('No engine or provider may be constructed')
    with pytest.raises(ValueError, match='authorization'):
        asyncio.run(batch.execute(run_factory=forbidden))
    assert batch.read()['status']=='ready' and not batch.read()['jobs'][0]['attempts']


@pytest.mark.parametrize('status,reason,attempts', [
    ('errored','runtime_error',3),('completed','provider_refusal',1),
    ('completed','invalid_decision',1),('completed','context_limit',1),
    ('completed','token_budget',1),('completed','tick_limit',1)])
def test_retry_ceiling_applies_only_to_technical_errors(tmp_path,status,reason,attempts):
    batch=Batch.create(Store(tmp_path),plan((100,)))
    class TerminalRun:
        def __init__(self,*args):
            self.id=uuid.uuid4().hex
            self.meta={'status':'ready','termination_reason':None}
        async def initialize(self): pass
        async def advance(self): self.meta.update(status=status,termination_reason=reason)
        async def stop(self): return self.meta
    result=asyncio.run(batch.execute(max_jobs=1,technical_retries=2,run_factory=TerminalRun))
    assert len(result['jobs'][0]['attempts'])==attempts
    assert len({a['id'] for a in result['jobs'][0]['attempts']})==attempts


@pytest.mark.engine
def test_one_saved_job_runs_through_the_native_research_pipeline(tmp_path):
    batch = Batch.create(Store(tmp_path), plan((100,)))
    result = asyncio.run(batch.execute(max_jobs=1))
    attempt = result['jobs'][0]['attempts'][0]
    assert result['status']=='completed' and attempt['metrics']['success']
    meta = batch.store.get(attempt['run_id'])
    assert meta['purpose']=='evaluation' and meta['feasibility_status']=='native_witness_validated'
    assert meta['metrics']['admitted_access_attempts'] >= 1
    assert (batch.store.path(meta['id'])/'qualification.json').is_file()


@pytest.mark.engine
def test_native_partial_error_gets_one_fresh_technical_retry(tmp_path):
    batch=Batch.create(Store(tmp_path),plan((100,)))
    failed=[False]
    class FaultOnce(Run):
        async def advance(self, *args, **kwargs):
            result=await super().advance(*args, **kwargs)
            pending=self.memory['Red_0'].view.get('pending_action')
            if not failed[0] and pending and pending['proposal']['action']=='AttemptAccess':
                failed[0]=True
                raise RuntimeError('Injected executor fault after actual native admission')
            return result
    result=asyncio.run(batch.execute(max_jobs=1,technical_retries=1,run_factory=FaultOnce))
    attempts=result['jobs'][0]['attempts']
    assert len(attempts)==2 and attempts[0]['reason']=='batch_execution_error'
    assert attempts[0]['status']=='errored' and attempts[0]['metrics']['partial_access_attempts']==1
    assert attempts[0]['metrics']['outcome_reason']=='batch_execution_error'
    assert attempts[1]['metrics']['success'] and attempts[1]['status']=='completed'
    assert attempts[0]['run_id']!=attempts[1]['run_id']
    first=batch.store.get(attempts[0]['run_id'])
    assert first['batch_id']==batch.id and first['termination_reason']=='batch_execution_error'
    partial=json.loads((batch.store.path(first['id'])/'interrupted-actions.json').read_text())
    assert partial['access_resources']['Red_0']['reserved']==1
    assert partial['access_resources']['Red_0']['settled']==0


@pytest.mark.engine
def test_native_saved_running_attempt_restarts_with_partial_evidence(tmp_path):
    async def check():
        store=Store(tmp_path)
        batch=Batch.create(store,plan((100,)))
        cfg=batch.read()['jobs'][0]['config']
        run=Run(EpisodeConfig.model_validate(cfg),store)
        await run.initialize()
        for _ in range(20):
            await run.advance()
            pending=run.memory['Red_0'].view.get('pending_action')
            if pending and pending['proposal']['action']=='AttemptAccess':
                break
        assert pending and pending['remaining_ticks']>0
        state=batch.read()
        job=state['jobs'][0]
        attempt_id=digest({'batch':batch.id,'job':job['job_id'],'index':1})[:32]
        job.update(status='running',attempts=[{'id':attempt_id,'run_id':run.id,'status':'running'}])
        state['status']='running'
        store.write_json(batch.path,state)
        # Simulate lost native process after a durable tick. No stop/rewrite of its frame.
        frame_path=run.directory/'frames'/f"{run.meta['tick']:06d}.json"
        saved=frame_path.read_bytes()
        await run.engine.close()
        result=await Batch(store,batch.id).execute(max_jobs=1)
        attempts=result['jobs'][0]['attempts']
        assert len(attempts)==2 and attempts[0]['status']=='interrupted'
        assert attempts[0]['reason']=='executor_restart'
        assert attempts[0]['metrics']['partial_access_attempts']==1
        assert attempts[1]['metrics']['success'] and attempts[1]['run_id']!=run.id
        assert store.get(run.id)['termination_reason']=='executor_restart'
        assert frame_path.read_bytes()==saved
        partial=json.loads((run.directory/'interrupted-actions.json').read_text())
        assert partial['actions']['Red_0']['proposal']['action']=='AttemptAccess'
        assert partial['access_resources']['Red_0']['reserved']==1
        assert partial['access_resources']['Red_0']['settled']==0
    asyncio.run(check())
