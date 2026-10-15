"""Selected, fixed software witnesses; not performance sweeps or research data.

The witness driver selects a route from researcher truth, then must satisfy all
native discovery/cache/source prerequisites. These checks establish legal paths,
not autonomous reasoning or universal solvability.
"""
import asyncio
import pytest

from backend.app.bridge import EngineBridge
from tests.test_cc4_adapter import address, finish
from tests.test_route_tradeoffs import tradeoff_config


@pytest.mark.engine
@pytest.mark.parametrize('seed,workers,depth,width,addons', [(100,1,1,2,0),(101,2,2,3,3),(103,4,3,3,5),(107,8,2,9,0)])
def test_selected_population_depth_service_witnesses(tmp_path,seed,workers,depth,width,addons):
    async def check():
        bridge = EngineBridge(tmp_path/'native.log','enterprise_cc4')
        try:
            await bridge.start()
            cfg = tradeoff_config(workers=workers,alternatives=width,privileged=width>=3,reactive_blocks=False)
            cfg.scenario.world_seed = seed
            cfg.scenario.cc4.addon_services = addons
            cfg.scenario.complexity.routes.depth = depth
            cfg.scenario.mission.deadline_tick = 300
            cfg.schedule.max_ticks = 350
            initial = await bridge.call('create',config=cfg.model_dump())
            actors = initial['actors']
            frame = await finish(bridge,{a:{'action':'DiscoverRemoteSystems','target':initial['views'][a]['known']['subnet'][0]} for a in actors})
            sources = {a:0 for a in actors}
            for layer in initial['truth']['route_manifest']['layers']:
                rules = [r for r in initial['truth']['route_manifest']['rules'] if r['target'] in layer]
                gate = next(r['target'] for r in rules if r['template']=='quiet_ftp')
                ip = address(initial,gate)
                assert all(ip in frame['views'][a]['known']['ip_address'] for a in actors)
                for action,target in [('DiscoverNetworkServices',ip),('ExploitRemoteService',ip),('PrivilegeEscalate',gate),('EstablishPivot',gate)]:
                    frame = await finish(bridge,{a:{'action':action,'target':target,'session':sources[a]} for a in actors})
                    assert all(r['outcome']=='TRUE' for r in frame['actions']), (seed,action,frame['actions'])
                sources = {a:next(s['id'] for s in frame['views'][a]['sessions'] if s['hostname']==gate and s['controller']) for a in actors}
                assert all(frame['views'][a]['scan_cache'][str(sources[a])]=={} for a in actors)
            target = cfg.scenario.targets[0]
            ip = address(initial,target)
            frame = await finish(bridge,{a:{'action':'DiscoverNetworkServices','target':ip,'session':sources[a]} for a in actors})
            assert all(r['outcome']=='TRUE' for r in frame['actions'])
            # Addon services alter CybORG's native exploit selector; repeat legal
            # attempts rather than injecting sessions or bypassing native actions.
            for attempt in range(8):
                need = [a for a in actors if not any(s['hostname']==target and s['active'] for s in frame['views'][a]['sessions'])]
                if not need:
                    break
                frame = await finish(bridge,{a:{'action':'ExploitRemoteService','target':ip,'session':sources[a]} for a in need})
            assert all(any(s['hostname']==target and s['active'] for s in frame['views'][a]['sessions']) for a in actors), (seed,'no legal native target access within witness bound')
            frame = await finish(bridge,{a:{'action':'PrivilegeEscalate','target':target,'session':sources[a]} for a in actors})
            assert all(r['outcome']=='TRUE' for r in frame['actions'])
            frame = await bridge.call('step',proposals={})
            assert frame['score']['mission_success']
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
def test_native_restore_during_quarantine_removes_pivot_and_reacquisition_has_empty_cache(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path/'native.log','enterprise_cc4')
        try:
            await bridge.start()
            cfg = tradeoff_config(fast_detection_probability=1,quiet_detection_probability=0,
                                  reaction_delay=8,block_ticks=14,response_budget=1)
            cfg.scenario.complexity.routes.depth = 2
            cfg.scenario.defender = 'reactive_restore'
            cfg.scenario.cc4.response_delay = 12
            cfg.scenario.cc4.response_budget = 1
            cfg.scenario.mission.deadline_tick = 150
            initial = await bridge.call('create',config=cfg.model_dump())
            layers = initial['truth']['route_manifest']['layers']
            rules = initial['truth']['route_manifest']['rules']
            gate1 = next(r['target'] for r in rules if r['target'] in layers[0] and r['template']=='quiet_ftp')
            gate2 = next(r['target'] for r in rules if r['target'] in layers[1] and r['template']=='fast_ssh')
            # Use a native target in the same defender zone. The fixed one-shot
            # policy spends its budget restoring the pivot, not another zone.
            cfg.scenario.targets = [gate2.rsplit('_user_host_',1)[0]+'_server_host_0']
            initial = await bridge.call('create',config=cfg.model_dump())
            frames = [initial]
            async def act(action,target=None,source=0):
                f = await bridge.call('step',proposals={'Red_0':{'action':action,'target':target,'session':source}})
                frames.append(f)
                while f['views']['Red_0'].get('pending_action'):
                    f = await bridge.call('step',proposals={}); frames.append(f)
                return f
            await act('DiscoverRemoteSystems',initial['views']['Red_0']['known']['subnet'][0])
            for action,target in [('DiscoverNetworkServices',address(initial,gate1)),('ExploitRemoteService',address(initial,gate1)),('PrivilegeEscalate',gate1),('EstablishPivot',gate1)]:
                f = await act(action,target)
                assert f['actions'][0]['outcome']=='TRUE'
            source1 = next(s['id'] for s in f['views']['Red_0']['sessions'] if s['hostname']==gate1 and s['controller'])
            for action,target in [('DiscoverNetworkServices',address(initial,gate2)),('ExploitRemoteService',address(initial,gate2)),('PrivilegeEscalate',gate2),('EstablishPivot',gate2)]:
                f = await act(action,target,source1)
                assert f['actions'][0]['outcome']=='TRUE'
            source2 = next(s['id'] for s in f['views']['Red_0']['sessions'] if s['hostname']==gate2 and s['controller'])
            target = cfg.scenario.targets[0]
            await act('DiscoverNetworkServices',address(initial,target),source2)
            restore = None
            for _ in range(40):
                f = await act('Sleep')
                if any(e['type']=='defender_response_completed' and e.get('host')==gate2 for e in f['defender_events']):
                    restore = f
                    break
            assert restore is not None, [(f['tick'],f['defender_events']) for f in frames]
            assert gate2 in restore['truth']['route_pressure']['blocked_until']
            assert not any(s['hostname']==gate2 and s['active'] for s in restore['views']['Red_0']['sessions'])
            assert str(source2) not in restore['views']['Red_0']['scan_cache']
            release = restore['truth']['route_pressure']['blocked_until'][gate2]
            while f['tick'] < release:
                f = await act('Sleep')
            for action,dest in [('DiscoverNetworkServices',address(initial,gate2)),('ExploitRemoteService',address(initial,gate2)),('PrivilegeEscalate',gate2),('EstablishPivot',gate2)]:
                f = await act(action,dest,source1)
                assert f['actions'][0]['outcome']=='TRUE'
            new_source = next(s['id'] for s in f['views']['Red_0']['sessions'] if s['hostname']==gate2 and s['controller'])
            assert f['views']['Red_0']['scan_cache'][str(new_source)] == {}
            for action,dest in [('DiscoverNetworkServices',address(initial,target)),('ExploitRemoteService',address(initial,target)),('PrivilegeEscalate',target)]:
                f = await act(action,dest,new_source)
                assert f['actions'][0]['outcome']=='TRUE'
            f = await act('Sleep')
            assert f['score']['mission_success']
        finally:
            await bridge.close()
    asyncio.run(check())
