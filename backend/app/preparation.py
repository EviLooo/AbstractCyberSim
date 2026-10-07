"""Read-only preparation; never imports a simulator or constructs a provider."""
from backend.app.evaluation import expand
from packages.contracts.models import ExperimentSpec


MECHANISMS = {
    'linear_control': ['Observe short compatible workflow; do not assume difficulty'],
    'investigate': ['Compare identical initial input and distinguishing evidence',
                    'Inspect unchanged failures and useful method/source decisions'],
    'combine': ['Verify both capabilities separately insufficient',
                'Trace actually delivered reference and owned source at admission'],
    'recover': ['Separate defender signal, decision, effect and observed symptom',
                'Inspect contradiction/reacquisition, native hold and censored recovery'],
}


def prepare_pilot(spec: ExperimentSpec):
    plan = expand(spec)
    families, workers, modes = set(), set(), set()
    tick_ceiling = request_ceiling = request_seconds = 0
    for job in plan['jobs']:
        cfg = job['config']
        research = cfg['scenario'].get('research')
        if not research:
            raise ValueError('Graduation pilot preparation requires the qualified research profile')
        families.add(research['recipe'])
        workers.add(cfg['team']['workers'])
        modes.add(cfg['schedule']['mode'])
        ticks = cfg['schedule']['max_ticks']
        tick_ceiling += ticks
        if cfg['cognition']['provider'] != 'scripted':
            # Loose bound: every worker's decision plus a format repair per tick;
            # a sessionless leader can add one call. Busy ticks usually need less.
            calls = ticks * (2*cfg['team']['workers'] + int(cfg['team']['architecture']=='hierarchy'))
            request_ceiling += calls
            request_seconds += calls * cfg['cognition']['timeout_seconds']
    return {'version':'pilot_preparation_v1','status':'preparation_only','executed':False,
        'job_count':plan['job_count'],'resolved_jobs':plan['jobs'],
        'declared_joint_tick_ceiling':tick_ceiling,
        'team_token_upper_bound':plan['team_token_upper_bound'],
        'provider_request_upper_bound':request_ceiling,
        'serial_request_seconds_upper_bound':request_seconds,
        'mechanism_checklist':{name:MECHANISMS[name] for name in sorted(families)},
        'worker_counts':sorted(workers),'tool_capacity_modes':sorted(modes),
        'failure_checklist':['Native exact-world witness or unverified exclusion before policy outcomes',
            'Separate horizon/attempt/token failure, refusal, invalid decision and context limit',
            'Record technical errors, unknown usage, manual intervention and partial attempts',
            'Retry technical errors only with a bounded ceiling and new attempt IDs',
            'Inspect all selected fixtures, including programmed wins and negative results'],
        'before_scientific_execution':['Obtain separate pilot execution authorization',
            'Review worked mechanism examples with supervisor; record disagreements',
            'After authorized development pilot, estimate costs/variance and justify sample size',
            'Freeze meaningful splits, exact policies/prompts/model artifacts and predeclared analysis'],
        'limitations':['No scientific pilot, native feasibility check or provider request executed.',
            'Request/tick/token bounds are configuration ceilings, not runtime or cost forecasts.',
            'Mechanisms are software-qualified; difficulty and realism are not calibrated.',
            'Scripted controls can succeed; no LLM winner or statistical significance assumed.']}
