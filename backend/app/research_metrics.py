"""Offline event-based research metrics, with explicit denominators/censoring."""
from statistics import mean

VERSION = 'research_metrics_v1.1'


def completed_action(action):
    return action.get('valid', True) and (action.get('lifecycle') == 'completed' or
        action.get('remaining_ticks', 0) == 0 and action.get('outcome') in ('TRUE', 'FALSE'))


def reduce_research(frames, horizon=None, termination_reason=None):
    last = frames[-1]
    admitted, completed, ages, relays = [], [], [], 0
    previous, wasted, duplicate, waits = {}, 0, 0, 0
    method_changes, source_changes, last_access = 0, 0, {}
    conflicts, refreshes, stale_uses = set(), set(), 0
    for frame in frames[1:]:
        concurrent = []
        for action in frame.get('actions', []):
            proposal, actor = action['proposal'], action['actor']
            label = proposal['action']
            if label=='Sleep':
                waits += 1
                continue
            if completed_action(action):
                completed.append(action)
            if not action.get('submitted', True) or not action.get('valid', True):
                continue
            admitted.append(action)
            signature = tuple(proposal.get(k) for k in ('action','target','source_host','method','probe','port','token_ref'))
            concurrent.append(signature)
            private = frame.get('private_views', {}).get(actor, {})
            relevant = {r['evidence_id']: r for r in private.get('research_evidence', [])
                        if r.get('kind') in ('probe','artifact')}
            cited = set(proposal.get('basis_evidence_ids', [])) & set(relevant)
            for eid in sorted(cited):
                evidence = relevant[eid]
                ages.append(max(0, frame['tick']-evidence['observed_tick']))
                stale_uses += int(bool(evidence.get('stale')))
                if evidence['origin']!=actor:
                    relays += 1
            if label=='AttemptAccess':
                last = last_access.get((actor, proposal.get('target')))
                method_changes += int(last is not None and last.get('method') != proposal.get('method'))
                source_changes += int(last is not None and last.get('source_host') != proposal.get('source_host'))
                last_access[actor, proposal.get('target')] = proposal
                identity = (actor, signature)
                epoch = private.get('belief_epoch', 0)
                prior = previous.get(identity)
                if prior and prior[0]==epoch and not cited-prior[1]:
                    wasted += 1
                previous[identity] = epoch, cited
        duplicate += len(concurrent)-len(set(concurrent))
        for actor, private in frame.get('private_views', {}).items():
            beliefs = private.get('beliefs', {})
            for record in beliefs.get('records', []):
                if record.get('conflict'):
                    conflicts.add((actor, record['host'], record['field'], record['evidence_id']))
            for record in beliefs.get('history', []):
                if record.get('contradicts'):
                    refreshes.add((actor, record['host'], record['field'], record['evidence_id']))
    last = frames[-1]
    accesses = [a for a in admitted if a['proposal']['action']=='AttemptAccess']
    finished_access = [a for a in completed if a['proposal']['action']=='AttemptAccess']
    messages = last.get('messages', [])
    recoveries, observed_losses = [], 0
    for actor, private in last.get('private_views', {}).items():
        events = private.get('beliefs', {}).get('events', [])
        losses = [e for e in events if e['type']=='access_lost']
        observed_losses += len(losses)
        for loss in losses:
            recovered = next((e for e in events if e['type']=='access_recovered'
                              and e['host']==loss['host'] and e['tick']>loss['tick']), None)
            renewed = next((f['tick'] for f in frames if f['tick']>loss['tick'] and any(
                a['actor']==actor and completed_action(a) and a.get('outcome')=='TRUE' and a['proposal']['action']!='Sleep'
                for a in f.get('actions', []))), None)
            recoveries.append({'actor': actor, 'host': loss['host'], 'observable_loss_tick': loss['tick'],
                               'renewed_progress_latency': renewed-loss['tick'] if renewed is not None else None,
                               'recovery_latency': recovered['tick']-loss['tick'] if recovered else None,
                               'censored': recovered is None})
    compatibility_recovery = []
    for actor, private in last.get('private_views', {}).items():
        previous_response = {}
        records = sorted(private.get('research_evidence', []), key=lambda r:(r['received_tick'],r['observed_tick']))
        for record in records:
            if record.get('kind')!='probe' or record.get('probe')!='service_behavior':
                continue
            context = (record['host'],record.get('source_host'),record.get('port'))
            older = previous_response.get(context)
            if older and record['observed_tick'] <= older['observed_tick']:
                continue
            previous_response[context] = record
            if not older or older['response']!='external_import_accepted' or record['response']=='external_import_accepted':
                continue
            observed = record['received_tick']
            recovered = next(((f['tick'],a['proposal']) for f in frames if f['tick']>=observed for a in f.get('actions', [])
                              if a['actor']==actor and a['proposal']['action']=='AttemptAccess'
                              and a['proposal'].get('target')==record['host'] and completed_action(a) and a.get('outcome')=='TRUE'), None)
            compatibility_recovery.append({'actor':actor,'address':record['host'],'source_host':record.get('source_host'),
                'observable_change_tick':observed,'basis_evidence_id':record['evidence_id'],
                'renewed_access_latency':recovered[0]-observed if recovered else None,
                'renewed_method':recovered[1].get('method') if recovered else None,
                'renewed_source':recovered[1].get('source_host') if recovered else None,'censored':recovered is None})
    success = next((f['tick'] for f in frames if f['score']['mission_success']), None)
    return {'research_formula_version': VERSION, 'native_ticks_observed': last['tick'],
            'declared_horizon': horizon, 'restricted_completion_ticks': success if success is not None else horizon,
            'completion_censored': success is None, 'outcome_reason': termination_reason,
            'admitted_access_attempts': len(accesses), 'completed_access_attempts': len(finished_access),
            'partial_access_attempts': len(accesses)-len(finished_access),
            'failed_access_attempts': sum(a['outcome']=='FALSE' for a in finished_access),
            'completed_probes': sum(a['proposal']['action']=='Probe' for a in completed),
            'completed_inspections': sum(a['proposal']['action']=='InspectArtifacts' for a in completed),
            'unchanged_repeated_access_attempts': wasted, 'comparable_duplicate_admissions': duplicate,
            'worker_wait_ticks': waits, 'recipient_copy_bytes_created': sum(m.get('bytes', 0) for m in messages),
            'recipient_copy_bytes_delivered': sum(m.get('bytes', 0) for m in messages if m['status']=='delivered'),
            'assignment_copies': sum(m['kind']=='assignment' for m in messages),
            'claim_copies': sum(m['kind']=='claim' for m in messages),
            'report_copies': sum(m['kind']=='report' for m in messages),
            'evidence_uses': len(ages), 'peer_evidence_uses': relays,
            'stale_evidence_uses': stale_uses, 'conflicting_evidence_records': len(conflicts),
            'contradicting_refresh_records': len(refreshes), 'access_method_changes': method_changes,
            'access_source_changes': source_changes,
            'mean_evidence_age_at_admission': mean(ages) if ages else None,
            'observed_access_losses': observed_losses, 'recovery_records': recoveries,
            'compatibility_recovery_records':compatibility_recovery,
            'no_observable_access_loss': observed_losses==0,
            'limitations': 'Conservative repeated-attempt rule; waiting includes voluntary Sleep. Reports are claims; age is not correctness. No loss is not zero recovery latency.'}
