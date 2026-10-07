"""Hand-counted busy actions, unchanged attempts, recipient copies and loss."""
from backend.app.research_metrics import reduce_research
from backend.app.evaluation import compare_runs
import asyncio
import json
import hashlib
import pytest


def test_hand_count_completion_admission_cost_and_censoring():
    proposal = {'action':'AttemptAccess','target':'target','source_host':'owned',
                'method':'web_rfi','basis_evidence_ids':['peer:0']}
    evidence = {'evidence_id':'peer:0','kind':'probe','origin':'peer','observed_tick':0,'received_tick':1}
    frames = []
    for tick in range(7):
        actions = []
        if tick in (1,4,5,6):
            actions = [{'actor':'Red_0','proposal':proposal,'valid':True,'submitted':tick in (1,5),
                        'remaining_ticks':3 if tick==1 else 1 if tick==5 else 0,
                        'lifecycle':'completed' if tick in (4,6) else 'submitted',
                        'outcome':'IN_PROGRESS' if tick in (1,5) else 'FALSE' if tick==4 else 'TRUE'}]
        frames.append({'tick':tick,'actions':actions,'score':{'mission_success':tick==6},
                       'private_views':{'Red_0':{'research_evidence':[evidence],'belief_epoch':0}},
                       'messages':[]})
    frames[-1]['messages'] = [{'kind':'claim','status':'delivered','bytes':32},
                              {'kind':'claim','status':'dropped_loss','bytes':32}]
    frames[-1]['private_views']['Red_0']['beliefs'] = {'events':[
        {'type':'access_lost','tick':2,'host':'target'},
        {'type':'access_recovered','tick':6,'host':'target'}]}
    measured = reduce_research(frames, 10, 'mission_success')
    assert measured['admitted_access_attempts']==measured['completed_access_attempts']==2
    assert measured['partial_access_attempts']==0 and measured['failed_access_attempts']==1
    assert measured['unchanged_repeated_access_attempts']==1
    assert measured['recipient_copy_bytes_created']==64 and measured['recipient_copy_bytes_delivered']==32
    assert measured['claim_copies']==2 and measured['peer_evidence_uses']==2
    assert measured['mean_evidence_age_at_admission']==3
    assert measured['restricted_completion_ticks']==6 and not measured['completion_censored']
    assert measured['recovery_records'][0]['recovery_latency']==4
    unfinished = reduce_research(frames[:2], 10, 'stopped')
    assert unfinished['partial_access_attempts']==1 and unfinished['completion_censored']
    assert unfinished['restricted_completion_ticks']==10
    assert unfinished['no_observable_access_loss'] and unfinished['recovery_records']==[]
    frames[-1]['private_views']['Red_0']['research_evidence'] = [
        {'evidence_id':'a','kind':'probe','origin':'Red_0','observed_tick':0,'received_tick':0,
         'host':'target','source_host':'owned','probe':'service_behavior','port':80,'response':'external_import_accepted'},
        {'evidence_id':'b','kind':'probe','origin':'Red_0','observed_tick':2,'received_tick':3,
         'host':'target','source_host':'owned','probe':'service_behavior','port':80,'response':'external_import_refused'},
        {'evidence_id':'a-relay','kind':'probe','origin':'peer','observed_tick':0,'received_tick':5,
         'host':'target','source_host':'owned','probe':'service_behavior','port':80,'response':'external_import_accepted'}]
    changed = reduce_research(frames, 10, 'mission_success')['compatibility_recovery_records']
    assert len(changed)==1 and changed[0]['observable_change_tick']==3
    assert changed[0]['renewed_access_latency']==3 and not changed[0]['censored']


def test_unfrozen_native_software_checks_cannot_enter_a_research_estimate():
    checks = [{'id':identity,'profile':'enterprise_cc4_research','purpose':'evaluation','status':'completed',
               'manual_intervention':False,'feasibility_status':'native_witness_validated',
               'metrics':{'success':True,'charged_tokens':0}} for identity in ('a','b')]
    result = compare_runs(checks, ['a','b'])
    assert result['paired_worlds']==0 and result['success_difference'] is None
    assert len(result['excluded'])==2 and all('frozen' in r['reason'] for r in result['excluded'])


def test_hand_count_conflicts_refresh_changes_and_valid_renewed_progress():
    proposal={'action':'AttemptAccess','target':'target','source_host':'source1',
              'method':'web_rfi','basis_evidence_ids':['old']}
    record={'evidence_id':'old','kind':'probe','origin':'Red_1','observed_tick':0,
            'received_tick':1,'stale':True}
    frames=[{'tick':0,'actions':[],'score':{'mission_success':False}}]
    for tick in range(1,6):
        p=dict(proposal)
        if tick>=4:
            p.update(method='credential_login',source_host='source2',token_ref='opaque')
        frames.append({'tick':tick,'score':{'mission_success':False},'messages':[],
            'actions':[{'actor':'Red_0','proposal':p,'valid':tick!=2,'submitted':True,
                        'outcome':'TRUE','remaining_ticks':1 if tick==3 else 0}],
            'private_views':{'Red_0':{'research_evidence':[record],'beliefs':{
                'events':[{'type':'access_lost','tick':1,'host':'target'}],
                'records':[{'host':'target','field':'service','evidence_id':'new','conflict':True}],
                'history':[{'host':'target','field':'service','evidence_id':'new','contradicts':'old'}]}}}})
    result=reduce_research(frames,10,'tick_limit')
    assert result['recovery_records'][0]['renewed_progress_latency']==3
    assert result['recovery_records'][0]['censored']
    assert result['stale_evidence_uses']==result['peer_evidence_uses']==4
    assert result['conflicting_evidence_records']==result['contradicting_refresh_records']==1
    assert result['access_method_changes']==result['access_source_changes']==1
    assert result['partial_access_attempts']==1 and result['completed_access_attempts']==3


def test_hand_count_recipient_copies_comparable_duplicates_and_waits():
    proposal={'action':'Probe','target':'observed','source_host':'common','probe':'connectivity','port':80}
    frame={'tick':1,'score':{'mission_success':False},'private_views':{},'messages':[
        {'kind':'assignment','status':'delivered','bytes':17},
        {'kind':'report','status':'pending','bytes':23},
        {'kind':'claim','status':'expired','bytes':29}], 'actions':[
        {'actor':a,'proposal':proposal,'valid':True,'submitted':True,'outcome':'TRUE'}
        for a in ('Red_0','Red_1')] + [{'actor':'Red_2','proposal':{'action':'Sleep'}}]}
    measured=reduce_research([{'tick':0,'score':{'mission_success':False}},frame],5,'tick_limit')
    assert measured['completed_probes']==2 and measured['comparable_duplicate_admissions']==1
    assert measured['worker_wait_ticks']==1
    assert measured['recipient_copy_bytes_created']==69 and measured['recipient_copy_bytes_delivered']==17
    assert measured['assignment_copies']==measured['report_copies']==measured['claim_copies']==1


@pytest.mark.engine
def test_native_recovery_offline_metrics_preserve_evidence(tmp_path,monkeypatch):
    from backend.app.runs import Run
    from backend.app.storage import Store
    from backend.app.evaluation import metrics
    from packages.contracts.models import EpisodeConfig
    from tests.research.helpers import config
    async def check():
        cfg=config(recipe='recover',workers=1,credential_variant='valid',
                   change={'mode':'restore','response_delay':4,'response_budget':1})
        cfg['scenario']['mission']={'hold_ticks':3}
        store=Store(tmp_path)
        run=Run(EpisodeConfig.model_validate(cfg),store)
        try:
            await run.initialize()
            for _ in range(50):
                if run.meta['status']=='completed': break
                await run.advance()
            assert run.meta['status']=='completed' and run.meta['metrics']['success']
            measured=run.meta['metrics']
            # Fixed native mechanism trajectory: initial access9, loss11, regain18.
            assert measured['success_tick']==22 and measured['admitted_access_attempts']==2
            assert measured['completed_access_attempts']==2 and measured['partial_access_attempts']==0
            assert measured['observed_access_losses']==1
            assert measured['recovery_records'][0]['observable_loss_tick']==11
            assert measured['recovery_records'][0]['recovery_latency']==7
            assert measured['access_method_changes']==1 and measured['calls']==0
            assert measured['completed_probes']==2 and measured['completed_inspections']==3
            await run.stop()
            saved={str(p.relative_to(run.directory)):hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in run.directory.rglob('*') if p.is_file()}
            def forbidden(*args,**kwargs): raise AssertionError('Offline reduction must start no engine/provider')
            monkeypatch.setattr('backend.app.bridge.EngineBridge.start',forbidden)
            monkeypatch.setattr('httpx.AsyncClient',forbidden)
            frames=[store.frame(run.id,tick) for tick in range(run.meta['tick']+1)]
            recomputed=metrics(frames,run.cognition.summary(),cfg['schedule']['max_ticks'],run.meta['termination_reason'])
            assert recomputed==measured
            assert saved=={str(p.relative_to(run.directory)):hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in run.directory.rglob('*') if p.is_file()}
            store.write_json(tmp_path/'offline-metric-proof.json',recomputed)
        finally:
            await run.stop()
    asyncio.run(check())
