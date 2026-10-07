"""Physical mission clock qualification; bounded fixtures, no research sweep."""
import asyncio
import copy
import json
import subprocess
from pathlib import Path
import pytest
from backend.app.bridge import EngineBridge
from backend.app.runs import RunManager
from backend.app.storage import Store
from backend.app.settings import engine_python
from backend.app.evaluation import metrics
from packages.contracts.models import EpisodeConfig
from packages.contracts.missions import MissionSettings
from packages.contracts.module_registry import compile_modules
from packages.engine_worker.missions import MissionTracker
from tests.test_cc4_adapter import config, address, finish


def test_simultaneous_hold_resets_and_same_tick_is_idempotent():
    m=MissionTracker(['A','B'],{'hold_ticks':3})
    assert not m.update(0,['A','B'])['success']
    assert m.update(1,['A'])['hold_ticks']==0
    assert m.update(2,['A','B'])['hold_ticks']==1
    assert m.update(2,['A','B'])['hold_ticks']==1
    assert m.update(3,['A','B'])['hold_ticks']==2
    lost=m.update(4,['B'])
    assert lost['hold_ticks']==0 and lost['reset_count']==1
    assert lost['events'][0]['type']=='objective_hold_reset'
    for tick in (5,6):assert not m.update(tick,['A','B'])['success']
    assert m.update(7,['A','B'])['success']
    with pytest.raises(ValueError):m.update(9,['A','B'])


def test_physical_prerequisites_are_live_and_completion_is_revocable():
    m=MissionTracker(['A','B'],{'objectives':[
        {'id':'first','targets':['A'],'hold_ticks':1},
        {'id':'second','targets':['B'],'requires_privileged_hosts':['A'],'hold_ticks':2}]})
    m.update(0,[])
    assert m.update(1,['B'])['objectives'][1]['status']=='blocked'
    assert not m.update(2,['A','B'])['success']
    assert m.update(3,['A','B'])['success']
    lost=m.update(4,['B'])
    assert not lost['success'] and all(o['hold_ticks']==0 for o in lost['objectives'])
    assert lost['objectives'][1]['missing_prerequisites']==['A']


@pytest.mark.parametrize('kind',['mission','objective'])
def test_inclusive_deadline_last_tick_succeeds_and_failure_is_sticky(kind):
    settings={'hold_ticks':2,'deadline_tick':3} if kind=='mission' else {'objectives':[{'id':'access','targets':['A'],'hold_ticks':2,'deadline_tick':3}]}
    good=MissionTracker(['A'],settings)
    good.update(0,[]);good.update(1,[]);good.update(2,['A'])
    assert good.update(3,['A'])['success']
    bad=MissionTracker(['A'],settings)
    for tick in (0,1,2):bad.update(tick,[])
    failure=bad.update(3,['A'])
    assert failure['failure']['reason']==kind+'_deadline' and not failure['success']
    assert not bad.update(4,['A'])['success']


def test_configuration_rejects_invalid_missions_and_compiles_without_architecture():
    cfg=config()
    cfg.scenario.mission=MissionSettings(hold_ticks=5,deadline_tick=100)
    raw=cfg.model_dump()
    assert EpisodeConfig.model_validate(raw).scenario.mission.hold_ticks==5
    other=copy.deepcopy(cfg);other.team.architecture='hierarchy'
    assert compile_modules(cfg)==compile_modules(other)
    for mission in [{'hold_ticks':0},{'hold_ticks':1001},{'hold_ticks':5,'deadline_tick':4},
        {'deadline_tick':181},{'hold_ticks':181},{'imaginary_goal':True},
        {'objectives':[{'id':'a','targets':['unknown']}]},
        {'objectives':[{'id':'a','targets':cfg.scenario.targets,'requires_privileged_hosts':['fake']}]},
        {'objectives':[{'id':'a','targets':cfg.scenario.targets,'requires_privileged_hosts':cfg.scenario.targets}]},
        {'objectives':[{'id':'a','targets':cfg.scenario.targets,'hold_ticks':99,'deadline_tick':98}]},
        {'objectives':[{'id':'a','targets':cfg.scenario.targets},{'id':'a','targets':cfg.scenario.targets}]}]:
        data=copy.deepcopy(raw);data['scenario']['mission']=mission
        with pytest.raises(ValueError):EpisodeConfig.model_validate(data)
    with pytest.raises(ValueError):EpisodeConfig.model_validate({'scenario':{'mission':{}}})


@pytest.mark.engine
def test_native_multiple_target_hold_and_read_only_score(tmp_path):
    async def check():
        cfg=config(1)
        cfg.scenario.targets=['contractor_network_subnet_server_host_0','restricted_zone_a_subnet_server_host_0']
        cfg.scenario.mission=MissionSettings(hold_ticks=3,deadline_tick=90)
        b=EngineBridge(tmp_path/'engine.log','enterprise_cc4')
        try:
            await b.start()
            frame=await b.call('create',config=cfg.model_dump())
            assert frame['score']['mission']['hold_ticks']==0
            await finish(b,{'Red_0':{'action':'DiscoverRemoteSystems','target':frame['views']['Red_0']['known']['subnet'][0]}})
            for target in cfg.scenario.targets:
                ip=address(frame,target)
                await finish(b,{'Red_0':{'action':'DiscoverNetworkServices','target':ip}})
                await finish(b,{'Red_0':{'action':'ExploitRemoteService','target':ip}})
                frame=await finish(b,{'Red_0':{'action':'PrivilegeEscalate','target':target}})
            assert frame['score']['targets_reached']==2
            assert frame['score']['mission']['hold_ticks']==1 and not frame['score']['mission_success']
            frame=await b.call('step',proposals={})
            assert not frame['score']['mission_success']
            frame=await b.call('step',proposals={})
            assert frame['score']['mission_success'] and frame['score']['mission']['hold_ticks']==3
        finally:await b.close()
    asyncio.run(check())


@pytest.mark.engine
def test_deadline_terminates_persists_failure_and_public_prompts_hide_progress(tmp_path):
    async def check():
        manager=RunManager(Store(tmp_path))
        try:
            cfg=config(1);cfg.scenario.mission=MissionSettings(deadline_tick=2)
            run=manager.get((await manager.create(cfg))['id'])
            assert run.mission()['requirements']['deadline_tick']==2
            assert 'hold_ticks' not in run.mission() and 'progress' not in run.mission()
            # A forged report or historical observation cannot grant native root.
            run.memory['Red_0'].reported_hosts['target']={'fields':{'privileged':True}}
            await run.advance({'Red_0':{'action':'Sleep'}})
            await run.advance({'Red_0':{'action':'Sleep'}})
            assert run.meta['termination_reason']=='mission_deadline' and run.meta['status']=='completed'
            assert run.engine.process is None and run.cognition.calls==0
            saved=manager.store.frame(run.id)
            assert saved['score']['mission']['status']=='failed'
            assert saved['score']['mission']['failure']['tick']==2
            assert not run.meta['metrics']['success'] and run.meta['metrics']['time_to_success_censored']
            assert run.meta['metrics']['mission_failure']['reason']=='mission_deadline'
            assert 'remaining_ticks' not in saved['private_views']['Red_0']['mission']
        finally:await manager.close()
    asyncio.run(check())


@pytest.mark.engine
def test_observed_defender_restore_during_hold_then_legal_recovery(tmp_path):
    async def check():
        cfg=config(1,defender='reactive_restore')
        cfg.scenario.cc4.response_delay=8
        cfg.scenario.cc4.response_budget=1
        cfg.scenario.mission=MissionSettings(hold_ticks=20,deadline_tick=100)
        b=EngineBridge(tmp_path/'engine.log','enterprise_cc4')
        frames=[]
        try:
            await b.start()
            initial=await b.call('create',config=cfg.model_dump())
            actor='Red_0';target=cfg.scenario.targets[0]
            await finish(b,{actor:{'action':'DiscoverRemoteSystems','target':initial['views'][actor]['known']['subnet'][0]}})
            async def acquire(host):
                ip=address(initial,host)
                for label in ['DiscoverNetworkServices','ExploitRemoteService','PrivilegeEscalate']:
                    frame=await finish(b,{actor:{'action':label,'target':host if label=='PrivilegeEscalate' else ip}})
                    frames.append(frame)
                return frame
            await acquire('contractor_network_subnet_server_host_0')
            frame=await acquire(target)
            assert frame['score']['mission']['hold_ticks']>0 and not frame['score']['mission_success']
            for _ in range(12):
                frame=await b.call('step',proposals={});frames.append(frame)
                if frame['score']['mission']['reset_count']:break
            assert frame['score']['mission']['hold_ticks']==0 and frame['score']['mission']['reset_count']==1
            assert target not in frame['score']['privileged_hosts']
            assert any(e['type']=='defender_response_completed' and e['host']==target for f in frames for e in f['defender_events'])
            frame=await acquire(target)
            assert frame['score']['mission']['hold_ticks']==1 and frame['score']['mission']['reset_count']==1
            for _ in range(19):frame=await b.call('step',proposals={})
            assert frame['score']['mission_success']
        finally:await b.close()
    asyncio.run(check())


@pytest.mark.engine
def test_persisted_native_objective_prerequisite_and_hold_replay(tmp_path):
    async def check():
        manager = RunManager(Store(tmp_path))
        try:
            cfg = config(1)
            target = cfg.scenario.targets[0]
            prerequisite = 'contractor_network_subnet_server_host_0'
            cfg.scenario.mission = MissionSettings.model_validate({
                'hold_ticks': 3, 'deadline_tick': 90, 'objectives': [{
                    'id': 'sustained_target', 'targets': [target],
                    'requires_privileged_hosts': [prerequisite], 'hold_ticks': 2}]})
            run = manager.get((await manager.create(cfg))['id'])
            initial = run.frames[-1]
            async def act(proposal):
                await run.advance({'Red_0': proposal})
                for _ in range(8):
                    if not run.frames[-1]['views']['Red_0']['pending_action']:
                        return run.frames[-1]
                    await run.advance()
                raise AssertionError('Native action did not complete')
            await act({'action': 'DiscoverRemoteSystems', 'target': initial['views']['Red_0']['known']['subnet'][0]})
            for host in [prerequisite, target]:
                ip = address(initial, host)
                for label in ['DiscoverNetworkServices', 'ExploitRemoteService', 'PrivilegeEscalate']:
                    frame = await act({'action': label, 'target': host if label == 'PrivilegeEscalate' else ip})
            assert frame['score']['mission']['objectives'][0]['hold_ticks'] == 1
            assert frame['score']['mission']['hold_ticks'] == 0
            for expected in [1, 2, 3]:
                frame = await act({'action': 'Sleep'})
                assert frame['score']['mission']['hold_ticks'] == expected
            assert run.meta['termination_reason'] == 'mission_success'
            assert run.meta['manual_intervention'] and run.cognition.calls == 0
            assert manager.store.frame(run.id)['score']['mission']['success']
            assert run.meta['metrics']['mission_hold_ticks'] == 3
            import csv, io
            row = next(csv.DictReader(io.StringIO(manager.store.csv())))
            assert row['mission_hold_ticks'] == '3' and row['mission_deadline_tick'] == '90'
        finally:
            await manager.close()
    asyncio.run(check())
