"""Explicit bounded developmental calibration; never a final held-out study.

Preparation saves a preselected plan and source snapshot without engine/model
construction. Execution accepts scripted providers only and never tunes policies,
retries failures, selects a winning seed, or computes significance from this pilot.
"""
import argparse
import asyncio
import copy
import csv
import io
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.batches import Batch
from backend.app.storage import Store, digest, now
from backend.app.studies import ROOT, source_manifest
from packages.contracts.models import EpisodeConfig
from tools.prepare_review_examples import configurations


def pilot_plan(focus='initial'):
    jobs = []
    bases = configurations()

    def add(case, base, architecture, workers, policy='evidence_controller', **overrides):
        cfg = base.model_dump()
        cfg['name'] = 'Development pilot · '+case+' · '+architecture+' · '+policy
        cfg['team'].update(architecture=architecture, workers=workers)
        cfg['cognition']['scripted_policy'] = policy
        research = cfg['scenario']['research']
        cfg['scenario']['world_seed'] = overrides.pop('world_seed', 1031)
        research['seed_namespaces']['recipe'] = overrides.pop('recipe_seed', 7919)
        research['evidence']['observation_delay'] = overrides.pop('observation_delay', 0)
        cfg['communication']['extra_delay'] = overrides.pop('transport_delay', 0)
        if 'response_delay' in overrides:
            research['change']['response_delay'] = overrides.pop('response_delay')
        if 'recipe' in overrides:
            research['recipe'] = overrides.pop('recipe')
        if 'variant' in overrides:
            research['condition_variant'] = overrides.pop('variant')
        if 'credential_variant' in overrides:
            research['credential_variant'] = overrides.pop('credential_variant')
        if overrides:
            raise ValueError('Unknown pilot override')
        cfg = EpisodeConfig.model_validate(cfg).model_dump()
        paired = copy.deepcopy(cfg)
        for key in ('name', 'cognition'):
            paired.pop(key)
        paired['team'].pop('architecture')
        jobs.append({'case_id':case, 'job_id':digest(cfg)[:24], 'pair_key':digest(paired),
                     'replicate':0, 'config':cfg})

    if focus=='artifact_reliability':
        for policy in ('fixed_workflow', 'evidence_controller', 'observed_planner'):
            for case,variant,credential in (
                ('disabled-invalid-key','import_disabled','invalid'),
                ('enabled-wrong-scope-key','import_enabled','wrong_scope'),
                ('denied-source-invalid-key','source_denied','invalid')):
                add(case,bases['investigation'],'independent',1,policy,
                    variant=variant,credential_variant=credential)
        for architecture in ('hierarchy','swarm'):
            add('restore-response8',bases['restore_recovery'],architecture,2,
                world_seed=1034,recipe_seed=7937,observation_delay=2,response_delay=8)
        return {'name':'R6 second development iteration · artifact reliability / Restore timing',
            'job_count':len(jobs),'jobs':jobs,'team_token_upper_bound':0,
            'warning':'Preselected developmental follow-up to valid cached-key shortcut and early Restore; no policy edits or final-study claims.'}
    for policy in ('fixed_workflow', 'evidence_controller', 'observed_planner'):
        add('linear-control', bases['investigation'], 'independent', 1, policy,
            recipe='linear_control', variant='import_enabled')
        for variant in ('import_enabled', 'import_disabled'):
            add('investigation-'+variant, bases['investigation'], 'independent', 1,
                policy, variant=variant)
    for delay in (0, 2):
        for architecture in ('independent', 'hierarchy', 'swarm'):
            add('dependency-delay'+str(delay), bases['dependency_merge'], architecture, 2,
                world_seed=1032, recipe_seed=7927, observation_delay=2, transport_delay=delay)
    for architecture in ('hierarchy', 'swarm'):
        add('dependency-four-workers', bases['dependency_merge'], architecture, 4,
            world_seed=1032, recipe_seed=7927, observation_delay=2)
        for delay in (2, 8):
            add('patch-response'+str(delay), bases['patch_adaptation'], architecture, 2,
                world_seed=1033, recipe_seed=7933, observation_delay=2, response_delay=delay)
        add('restore-response4', bases['restore_recovery'], architecture, 2,
            world_seed=1034, recipe_seed=7937, observation_delay=2)
    return {'name':'Authorized R6 development pilot · 6 October 2026',
        'job_count':len(jobs), 'jobs':jobs, 'team_token_upper_bound':0,
        'warning':'Development only; one episode per selected cell, not significance, realism or final generalization proof.'}


def prepare(root,focus='initial'):
    store = Store(root)
    plan = pilot_plan(focus)
    sources = source_manifest()
    payload = {'version':'development_pilot_v1', 'plan':plan, 'sources':sources,
        'source_hash':digest(sources), 'authorization':'User: ok go following the plan, after the bounded pilot/held-out workflow explanation.',
        'bounds':{'episodes':len(plan['jobs']),'ticks_per_episode':180,'access_attempts_per_episode':12,
                  'provider_calls':0,'technical_retries':0,'wall_seconds':1200},
        'rules':['Preselect cells before outcomes; freeze current policies.',
                 'No policy/engine/prompt edits during this pilot; no post-failure seed selection.',
                 'Exclude unverified witnesses; separate technical errors from mission failures.',
                 'Descriptive development observations only; final held-out protocol requires later freeze.',
                 'Expert realism feedback and live LLM comparison remain outstanding.']}
    freeze = {'id':digest(payload), 'created_at':now(), 'payload':payload}
    target = root/'pilot-freeze.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf-8'))['id']!=freeze['id']:
            raise ValueError('Existing pilot differs; preserve it and use a new data directory')
        return
    for name in sources:
        p=root/'source'/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes((ROOT/name).read_bytes())
    store.write_json(target,freeze)


async def execute(root):
    store=Store(root)
    freeze=json.loads((root/'pilot-freeze.json').read_text(encoding='utf-8'))
    if digest(freeze['payload'])!=freeze['id'] or source_manifest()!=freeze['payload']['sources']:
        raise ValueError('Pilot freeze/source changed; execution rejected')
    plan=freeze['payload']['plan']
    if any(j['config']['cognition']['provider']!='scripted' for j in plan['jobs']):
        raise ValueError('This bounded pilot does not authorize model generation')
    batch=Batch.create(store,plan)
    status=root/'pilot-status.json'
    store.write_json(status,{'status':'running','batch_id':batch.id,'started_at':now(),
                             'pilot_id':freeze['id'],'episodes':len(plan['jobs'])})
    try:
        state=await asyncio.wait_for(batch.execute(max_jobs=len(plan['jobs']),technical_retries=0),1200)
    except asyncio.TimeoutError:
        state=batch.read()
        store.write_json(status,{'status':'wall_time_limit','batch_id':batch.id,'ended_at':now()})
        raise
    if source_manifest()!=freeze['payload']['sources']:
        raise ValueError('Source changed during pilot; preserve runs and reject interpretation')
    rows=[]
    for job in state['jobs']:
        attempt=job['attempts'][-1] if job['attempts'] else {}
        metrics=attempt.get('metrics',{})
        rows.append({'case':job['case_id'],'policy':job['config']['cognition']['scripted_policy'],
            'architecture':job['config']['team']['architecture'],'workers':job['config']['team']['workers'],
            'run_id':attempt.get('run_id'),'status':attempt.get('status'),'reason':attempt.get('reason'),
            'success':metrics.get('success'),'ticks':metrics.get('native_ticks_observed'),
            'attempts':metrics.get('admitted_access_attempts'),'failed_attempts':metrics.get('failed_access_attempts'),
            'probes':metrics.get('completed_probes'),'inspections':metrics.get('completed_inspections'),
            'copies':metrics.get('message_delivered'),'recovery':metrics.get('recovery_records'),
            'calls':metrics.get('calls'),'exclusion':job['status']=='excluded'})
    store.write_json(root/'pilot-results.json',{'purpose':'development_pilot','pilot_id':freeze['id'],
        'source_hash':freeze['payload']['source_hash'],'rows':rows,
        'limits':'One selected episode per cell; no confidence interval, LLM comparison or external realism conclusion.'})
    output=io.StringIO()
    writer=csv.DictWriter(output,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
    (root/'pilot-results.csv').write_text(output.getvalue(),encoding='utf-8')
    store.write_json(status,{'status':state['status'],'batch_id':batch.id,'ended_at':now(),
        'pilot_id':freeze['id'],'completed_jobs':sum(j['status']=='completed' for j in state['jobs']),
        'excluded_jobs':sum(j['status']=='excluded' for j in state['jobs'])})
    print(json.dumps({'status':state['status'],'rows':rows}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,default=Path('.local/development-pilot-20261006'))
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--focus',choices=('initial','artifact_reliability'),default='initial')
    args=parser.parse_args()
    root=args.data_root.resolve()
    if args.prepare:prepare(root,args.focus)
    if args.execute:asyncio.run(execute(root))
    if not(args.prepare or args.execute):
        plan=pilot_plan(args.focus)
        print(json.dumps({'episodes':plan['job_count'],'max_ticks':180,'attempts':12,'model_calls':0,
            'cases':[{'case':j['case_id'],'architecture':j['config']['team']['architecture'],
                      'policy':j['config']['cognition']['scripted_policy']} for j in plan['jobs']]},indent=2))


if __name__=='__main__':main()
