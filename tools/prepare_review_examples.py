"""Four bounded native software review fixtures, explicitly executed and archived.

No provider calls or scientific estimates. Default invocation is a config preview.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.runs import Run
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig


def configurations():
    a='restricted_zone_a_subnet_server_host_0'
    b='operational_zone_a_subnet_server_host_0'
    result={}
    for mechanism,recipe,change,workers,architecture in (
        ('investigation','investigate','none',1,'independent'),
        ('dependency_merge','combine','none',2,'hierarchy'),
        ('patch_adaptation','recover','patch_rfi',1,'independent'),
        ('restore_recovery','recover','restore',1,'independent')):
        result[mechanism]=EpisodeConfig.model_validate({
            'schema_version':'2.0','purpose':'evaluation','name':'Software review · '+mechanism,
            'scenario':{'profile':'enterprise_cc4_research','world_seed':100,'targets':[a,b] if recipe=='combine' else [a],
                'cc4':{'addon_services':0},'mission':{'hold_ticks':3 if recipe=='recover' else 1},
                'research':{'recipe':recipe,'condition_variant':'import_disabled' if mechanism=='investigation' else 'import_enabled',
                    'credential_variant':'valid','initial_access':'matched_split_entry' if recipe=='combine' else 'common_entry',
                    'capability_coupling':'bridge_and_token' if recipe=='combine' else 'separate',
                    'change':{'mode':change,'response_budget':int(change!='none'),'response_delay':4}}},
            'team':{'architecture':architecture,'workers':workers},
            'cognition':{'scripted_policy':'evidence_controller'},'schedule':{'max_ticks':180}})
    return result


def archive(run,mechanism,output):
    frames=run.frames
    events=[]
    for frame in frames:
        for action in frame['actions']:
            if action['proposal']['action']!='Sleep' and (action.get('submitted') or action.get('lifecycle')=='completed'):
                actor=action['actor']
                events.append({'tick':frame['tick'],'actor':actor,'proposal':action['proposal'],
                    'valid':action['valid'],'outcome':action['outcome'],'lifecycle':action.get('lifecycle'),
                    'preconditions':action.get('preconditions'),'state_delta':action.get('state_delta'),
                    'private_evidence':[r for r in frame['private_views'][actor]['research_evidence']
                        if r.get('evidence_id') in action['proposal'].get('basis_evidence_ids', [])
                        or r.get('host')==action['proposal'].get('target')],
                    'decision':frame.get('decisions',{}).get(actor)})
    last=frames[-1]
    summary={'purpose':'software_qualification','mechanism':mechanism,'run_id':run.id,
        'code_fingerprint':run.meta['code_fingerprint'],'config_hash':run.meta['config_hash'],
        'world_id':run.meta['world_id'],'feasibility_status':run.meta['feasibility_status'],
        'catalog_version':last['private_views']['Red_0']['native']['catalog']['version'],
        'config':run.config.model_dump(),'metrics':run.meta['metrics'],'trajectory':events,
        'delivered_messages':[{key:m.get(key) for key in ('id','kind','sender','recipient',
            'created_tick','due_tick','resolved_tick','bytes','status','evidence_ids')}
            for m in last['messages'] if m['status']=='delivered'],
        'defender_history':last['truth']['research_truth']['response']['history'],
        'observed_access_events':{a:v.get('beliefs',{}).get('events',[]) for a,v in last['private_views'].items()},
        'limitations':['Deliberately selected bounded software fixture, not a scientific performance sample.',
            'Review is pending; a software-qualified trajectory does not establish external realism.',
            'Compact JSON selects cited/target evidence and message metadata; ZIP preserves full frames/payloads.']}
    output.mkdir(parents=True,exist_ok=True)
    (output/(mechanism+'.json')).write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    entries={p.relative_to(run.directory).as_posix():p.read_bytes() for p in run.directory.rglob('*') if p.is_file() and p.suffix!='.tmp'}
    entries['checksums.json']=json.dumps({n:hashlib.sha256(d).hexdigest() for n,d in entries.items()},indent=2).encode()
    with zipfile.ZipFile(output/(mechanism+'.zip'),'w',zipfile.ZIP_DEFLATED) as bundle:
        for name,data in sorted(entries.items()):bundle.writestr(name,data)
    return {key:summary[key] for key in ('mechanism','run_id','code_fingerprint','config_hash','world_id','metrics')}


async def execute(args):
    store=Store(args.data_root.resolve())
    result=[]
    for mechanism,cfg in configurations().items():
        run=Run(cfg,store)
        try:
            await run.initialize()
            for _ in range(cfg.schedule.max_ticks):
                if run.meta['status']=='completed':break
                await run.advance()
            assert run.meta['metrics']['success'],mechanism
            assert run.cognition.calls==0
            await run.stop()
            result.append(archive(run,mechanism,args.output))
            print(json.dumps({'mechanism':mechanism,'run_id':run.id,'success_tick':run.meta['tick']}),flush=True)
        finally:await run.stop()
    store.write_json(args.output/'index.json',{'purpose':'software_qualification','examples':result})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--data-root',type=Path,default=Path('.local/graduation-review'))
    parser.add_argument('--output',type=Path,default=Path('docs/research/examples/worked'))
    args=parser.parse_args()
    if args.execute:asyncio.run(execute(args))
    else:print(json.dumps({k:v.model_dump() for k,v in configurations().items()},indent=2))


if __name__=='__main__':main()
