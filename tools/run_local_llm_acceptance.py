"""Explicit one-episode local-model acceptance with a wall-time ceiling.

This is an integration check, not a scientific comparison. Results are saved
without monitoring. No model is called unless both execution flags are present.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlparse

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from backend.app.batches import Batch
from backend.app.evaluation import expand
from backend.app.storage import Store, now
from packages.contracts.models import EpisodeConfig, ExperimentSpec


async def acceptance(args):
    endpoint = urlparse(os.environ.get('OLLAMA_URL','http://127.0.0.1:11434'))
    if endpoint.hostname not in ('localhost','127.0.0.1','::1') or endpoint.scheme!='http':
        raise ValueError('This acceptance launcher only permits the local HTTP model server')
    config = EpisodeConfig.model_validate_json(args.config.read_text(encoding='utf-8-sig')).model_dump()
    if config['scenario']['profile']!='enterprise_cc4_research' or config['team']['workers']!=1 or config['team']['architecture']!='independent':
        raise ValueError('This bounded integration fixture requires one independent research worker')
    if config['cognition']['provider']!='ollama':
        raise ValueError('Select the installed local model explicitly')
    store = Store(args.data_root.resolve())
    spec = ExperimentSpec.model_validate({'name':'Local Qwen software integration', 'base':config,
        'architectures':['independent'],'worker_counts':[1],
        'world_seeds':[config['scenario']['world_seed']], 'replicates':1})
    batch = Batch.create(store,expand(spec))
    record = {'purpose':'software_qualification','batch_id':batch.id,'started_at':now(),
              'wall_time_limit_seconds':args.max_seconds,'model_requested':config['cognition']['model'],
              'authorization':'User authorized one bounded installed-local-Qwen integration check on 5 October 2026.',
              'limitations':'No organization comparison or scientific advantage is tested; this run is unfrozen and excluded from study estimates.'}
    status_file = store.root/'acceptance-status.json'
    store.write_json(status_file,dict(record,status='starting'))
    print(json.dumps(dict(record,status='starting')),flush=True)
    if not (args.execute and args.allow_local_model):
        store.write_json(status_file,dict(record,status='preview_only'))
        return
    try:
        result = await asyncio.wait_for(batch.execute(max_jobs=1,technical_retries=0,allow_live=True),timeout=args.max_seconds)
        attempts = result['jobs'][0]['attempts']
        latest = attempts[-1] if attempts else None
        record.update(status=result['status'],attempt=latest)
    except asyncio.TimeoutError:
        state = batch.read()
        for job in state['jobs']:
            for attempt in job['attempts']:
                if attempt['status']=='running':
                    attempt.update(status='interrupted',reason='acceptance_wall_time_limit',ended_at=now())
                    metadata = store.get(attempt['run_id'])
                    metadata.update(status='interrupted',termination_reason='acceptance_wall_time_limit')
                    store.update(metadata)
                    attempt['metrics']=metadata.get('metrics',{})
                    job['status']='pending'
        state.update(status='paused',updated_at=now())
        store.write_json(batch.path,state)
        record.update(status='wall_time_limit',attempts=state['jobs'][0]['attempts'])
    except Exception as exc:
        record.update(status='launcher_error',error=str(exc))
    record['ended_at']=now()
    store.write_json(status_file,record)
    print(json.dumps(record),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config',type=Path)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--max-seconds',type=int,default=900,choices=range(60,1801),metavar='60..1800')
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--allow-local-model',action='store_true')
    asyncio.run(acceptance(parser.parse_args()))


if __name__=='__main__':
    main()
