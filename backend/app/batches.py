"""Saved sequential scheduling; construction/preview never executes episodes."""
import json
import re
from contextlib import contextmanager

from backend.app.runs import Run
from backend.app.storage import digest, now
from packages.contracts.models import EpisodeConfig


@contextmanager
def exclusive(path):
    """OS-managed lock releases on process exit, including an interrupted queue."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        if handle.tell()==0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        try:
            import msvcrt
        except ImportError:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)
        else:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


class Batch:
    def __init__(self, store, batch_id):
        if not re.fullmatch(r'[a-f0-9]{32}', batch_id):
            raise ValueError('Invalid batch ID')
        self.store, self.id = store, batch_id
        self.directory = store.root/'batches'/batch_id
        self.path = self.directory/'queue.json'
        self.control = self.directory/'control.json'

    @classmethod
    def create(cls, store, plan, freeze_id=None, split=None):
        if (freeze_id is None)!=(split is None) or split not in (None,'development','validation','test'):
            raise ValueError('A frozen queue requires both freeze ID and a valid split')
        if freeze_id:
            from backend.app.studies import Study
            study = Study(store,freeze_id)
        jobs, seen = [], set()
        for job in plan['jobs']:
            cfg = EpisodeConfig.model_validate(job['config']).model_dump()
            if cfg['purpose']!='evaluation' or job['job_id'] in seen:
                raise ValueError('Queue needs unique validated evaluation jobs')
            seen.add(job['job_id'])
            if freeze_id:
                study.bind(cfg,split)
            jobs.append(dict(job, config=cfg, status='pending', attempts=[]))
        identity_payload = {'version':'batch_v1','jobs':plan['jobs']}
        if freeze_id:
            identity_payload.update(freeze_id=freeze_id,split=split)
        identity = digest(identity_payload)[:32]
        batch = cls(store, identity)
        if not batch.path.exists():
            store.write_json(batch.path, {'version':'batch_v1','id':identity,'plan_hash':digest(plan),
                                         'name':plan['name'],'created_at':now(),'status':'ready','jobs':jobs,
                                         'freeze_id':freeze_id,'split':split})
            store.write_json(batch.control, {'stop':False})
        return batch

    def read(self):
        return json.loads(self.path.read_text(encoding='utf-8'))

    def request_stop(self):
        self.store.write_json(self.control, {'stop':True})

    def stopping(self):
        return json.loads(self.control.read_text(encoding='utf-8')).get('stop', False)

    async def execute(self, *, max_jobs=1, technical_retries=0, allow_live=False, run_factory=Run):
        if not 1<=max_jobs<=10000 or not 0<=technical_retries<=2:
            raise ValueError('Execution bounds out of range')
        with exclusive(self.directory/'executor.lock'):
            state = self.read()
            study = None
            if state.get('freeze_id'):
                from backend.app.studies import Study
                study = Study(self.store,state['freeze_id'])
                study.check_sources()
            if not allow_live and any(j['config']['cognition']['provider']!='scripted' for j in state['jobs'] if j['status']!='completed'):
                raise ValueError('Live-provider execution requires separate explicit authorization')
            if study:
                models={j['config']['cognition']['model'] for j in state['jobs']
                        if j['status'] not in ('completed','excluded') and j['config']['cognition']['provider']=='ollama'}
                if models:
                    await study.check_model_server(models)
            self.store.write_json(self.control, {'stop':False})
            state.update(status='running', technical_retries=technical_retries, updated_at=now())
            self.store.write_json(self.path, state)
            completed = 0
            for job in state['jobs']:
                if job['status'] in ('completed','excluded'):
                    continue
                if completed>=max_jobs or self.stopping():
                    break
                # Native state cannot resume after an executor interruption.
                for attempt in job['attempts']:
                    if attempt['status']=='running':
                        attempt.update(status='interrupted', reason='executor_restart')
                        metadata = self.store.interrupt(attempt['run_id'], 'executor_restart')
                        attempt.update(ended_at=now(), metrics=metadata.get('metrics', {}))
                failures = 0
                while True:
                    cfg = EpisodeConfig.model_validate(job['config'])
                    frozen_world = study.bind(cfg.model_dump(),state['split']) if study else None
                    run = run_factory(cfg, self.store)
                    attempt = {'id':digest({'batch':self.id,'job':job['job_id'],'index':len(job['attempts'])+1})[:32],
                               'run_id':run.id,'status':'running','created_at':now()}
                    job['attempts'].append(attempt)
                    job['status']='running'
                    self.store.write_json(self.path, state)
                    try:
                        await run.initialize()
                        if frozen_world:
                            native_world = json.loads((run.directory/'world.json').read_text(encoding='utf-8'))
                            if digest(native_world)!=frozen_world['technical_world_hash']:
                                raise ValueError('Actual materialized native world differs from freeze')
                            run.meta.update(freeze_id=study.id,split=state['split'],
                                freeze_purpose=study.read()['payload']['purpose'],causal_world_hash=frozen_world['causal_world_hash'])
                            self.store.write_json(run.directory/'freeze-binding.json', {'freeze_id':study.id,
                                'split':state['split'],'technical_world_hash':digest(native_world),
                                'causal_world_hash':frozen_world['causal_world_hash']})
                        run.meta.update(batch_id=self.id, job_id=job['job_id'], attempt_id=attempt['id'],
                                        pair_key=job['pair_key'],replicate=job.get('replicate',0),status='running')
                        if isinstance(run, Run):
                            self.store.update(run.meta)
                        while run.meta['status'] not in ('completed','errored','stopped','interrupted'):
                            if self.stopping():
                                await run.stop()
                                break
                            await run.advance()
                    except Exception as exc:
                        attempt['error']=str(exc)
                        if run.meta['status'] not in ('completed','errored','stopped','interrupted'):
                            run.meta.update(status='errored',termination_reason='batch_execution_error',error=str(exc))
                            if isinstance(run, Run):
                                from backend.app.evaluation import metrics
                                if run.frames:
                                    run.meta['metrics'] = metrics(run.frames, run.cognition.summary(),
                                        run.config.schedule.max_ticks, 'batch_execution_error')
                                self.store.update(run.meta)
                    finally:
                        await run.stop()
                    reason = run.meta.get('termination_reason')
                    excluded = run.meta.get('feasibility_status')=='unverified'
                    stopped = self.stopping() or run.meta['status'] in ('stopped','interrupted')
                    technical = run.meta['status']=='errored' and not excluded
                    attempt.update(status=run.meta['status'], reason=reason, ended_at=now(),
                                   metrics=run.meta.get('metrics', {}))
                    job['status']='excluded' if excluded else 'pending' if stopped else 'completed'
                    self.store.write_json(self.path, state)
                    if stopped or excluded or not technical or failures>=technical_retries:
                        break
                    failures += 1
                    job['status']='pending'
                if self.stopping():
                    break
                completed += 1
            state.update(status='completed' if all(j['status'] in ('completed','excluded') for j in state['jobs']) else 'paused', updated_at=now())
            self.store.write_json(self.path, state)
            return state
