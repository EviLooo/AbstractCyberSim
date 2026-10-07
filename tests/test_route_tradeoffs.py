"""Acceptance fixtures for service/time/sensor tradeoffs, not research results."""
import asyncio
import copy
from types import SimpleNamespace

import httpx
import pytest

from backend.app.api import create_app
from backend.app.bridge import EngineBridge
from backend.app.knowledge import PrivateMemory
from backend.app.runs import RunManager
from backend.app.storage import Store
from packages.contracts.complexity import RouteTradeoffs, RouteSettings, ComplexitySettings, BeliefSettings
from packages.contracts.models import EpisodeConfig
from packages.contracts.missions import MissionSettings
from packages.contracts.module_registry import compile_modules
from packages.engine_worker.cc4.route_pressure import RoutePressure
from tests.test_cc4_adapter import config, address, finish


def tradeoff_config(workers=1, alternatives=2, privileged=False, **options):
    cfg = config(workers)
    cfg.scenario.cc4.user_hosts = max(3, alternatives + 1)
    cfg.scenario.complexity = ComplexitySettings(routes=RouteSettings(enabled=True, depth=1,
        alternatives=alternatives, hardened_dead_end=True,
        tradeoffs=RouteTradeoffs(enabled=True, privileged_route=privileged, **options)))
    cfg.scenario.mission = MissionSettings(hold_ticks=2, deadline_tick=150)
    return cfg


def test_tradeoff_contract_population_constraints_and_manifest():
    cfg = tradeoff_config()
    manifest = compile_modules(cfg)
    assert manifest['modules']['route_tradeoffs']['enabled']
    other = cfg.model_copy(deep=True)
    other.team.architecture = 'hierarchy'
    assert compile_modules(other) == manifest
    for patch in [dict(quiet_exploit_ticks=2), dict(quiet_detection_probability=0.95),
                  dict(response_budget=0), dict(fast_detection_probability=1.1)]:
        data = cfg.model_dump()
        data['scenario']['complexity']['routes']['tradeoffs'].update(patch)
        with pytest.raises(ValueError):
            EpisodeConfig.model_validate(data)
    for patch in [dict(enabled=False), dict(alternatives=1), dict(alternatives=3)]:
        data = cfg.model_dump()
        data['scenario']['complexity']['routes'].update(patch)
        with pytest.raises(ValueError):
            EpisodeConfig.model_validate(data)
    with pytest.raises(ValueError):
        tradeoff_config(privileged=True)
    assert tradeoff_config(alternatives=9).scenario.cc4.user_hosts == 10


def test_traffic_sensor_budget_timing_reset_and_acl_preservation():
    options = RouteTradeoffs(enabled=True, reaction_delay=2, block_ticks=3, response_budget=1).model_dump()
    recipe = {'enabled': True, 'tradeoffs': {'settings': options},
              'rules': [{'target': 'fast', 'tradeoff': {'detection_probability': 1}},
                        {'target': 'quiet', 'tradeoff': {'detection_probability': 0}}]}
    sensor = RoutePressure(recipe, 100)
    traffic = [{'target': h, 'action': 'scan', 'source': 'entry'} for h in ('fast', 'quiet')]
    events = sensor.observe(traffic, 4)
    assert [e['host'] for e in events if e['type'] == 'route_sensor_alert'] == ['fast']
    assert events == RoutePressure(recipe, 100).observe(traffic, 4)
    assert not sensor.transition(5)
    assert sensor.transition(6)[0]['release_tick'] == 9
    state = SimpleNamespace(hosts={'fast': {}, 'quiet': {}, 'entry': {}},
                            blocks={'fast': ['unrelated'], 'quiet': ['other-policy']})
    original = copy.deepcopy(state.blocks)
    sensor.apply_blocks(state)
    assert 'entry' in state.blocks['fast'] and 'fast' in state.blocks['quiet']
    assert 'other-policy' in state.blocks['quiet']
    sensor.apply_blocks(state)
    assert state.blocks['fast'].count('entry') == 1
    assert not sensor.transition(8)
    assert sensor.transition(9)[0]['type'] == 'route_block_released'
    sensor.apply_blocks(state)
    assert state.blocks == original
    sensor.observe(traffic, 10)
    assert not sensor.transition(20) and sensor.used == 1


def test_route_clues_obey_delayed_private_evidence_and_replanner_costs():
    from backend.app.baselines import BaselinePolicy
    memory = PrivateMemory('Red_0', BeliefSettings(enabled=True, observation_delay=2))
    view = {'actor': 'Red_0', 'pivot_enabled': True, 'sessions': [{'id': 0, 'hostname': 'entry',
        'active': True, 'controller': True, 'privileged': False}],
        'scan_cache': {'0': {'10.0.0.2': [21]}}, 'known': {'ip_address': ['10.0.0.2'], 'hostname': [], 'subnet': []}}
    assessment = {'estimated_exploit_ticks': 8, 'route_sensor_exposure': 'low'}
    action = {'proposal': {'action': 'DiscoverNetworkServices', 'target': '10.0.0.2'}, 'valid': True, 'outcome': 'TRUE'}
    memory.observe({'tick': 1, 'actor': 'Red_0', 'evidence_id': 'scan',
                    'data': {'10.0.0.2': {'Route clue': assessment}}}, view, action)
    assert not memory.hosts
    memory.observe({'tick': 3, 'actor': 'Red_0', 'evidence_id': 'empty', 'data': {}}, view)
    public = memory.public_view({'target_names': ['goal']}, {})
    assert public['hosts']['10.0.0.2']['fields']['Route clue'] == assessment
    assert memory.evidence_ids() == ['scan']
    _, trace = BaselinePolicy('local_replan').rank(public, [{'action': 'ExploitRemoteService', 'target': '10.0.0.2'}], 3)
    assert trace['alternatives'][0]['estimated_action_ticks'] == 8
    assert trace['alternatives'][0]['observed_route_clue'] == assessment


def test_tradeoff_api_roundtrip_and_invalid_population_rejected(tmp_path):
    async def check():
        app = create_app(tmp_path)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                cfg = tradeoff_config().model_dump()
                assert (await client.post('/api/configs/validate', json=cfg)).json() == cfg
                cfg['scenario']['complexity']['routes']['alternatives'] = 9
                result = await client.post('/api/runs', json=cfg)
                assert result.status_code == 422 and not app.state.manager.live
        finally:
            await app.state.manager.close()
    asyncio.run(check())


@pytest.mark.engine
@pytest.mark.parametrize('alternatives,privileged', [(2, False), (3, True), (9, True)])
def test_native_generated_services_durations_privileges_pairing_and_clues(tmp_path, alternatives, privileged):
    async def check():
        bridge = EngineBridge(tmp_path / 'native.log', 'enterprise_cc4')
        try:
            await bridge.start()
            cfg = tradeoff_config(workers=2, alternatives=alternatives, privileged=privileged, reactive_blocks=False)
            initial = await bridge.call('create', config=cfg.model_dump())
            assert initial['world'] == (await bridge.call('create', config=cfg.model_dump()))['world']
            cfg.team.architecture = 'hierarchy'
            assert initial['world'] == (await bridge.call('create', config=cfg.model_dump()))['world']
            cfg.team.architecture = 'independent'
            manifest = initial['truth']['route_manifest']
            assert len(manifest['layers'][0]) == alternatives
            rules = [r for r in manifest['rules'] if r.get('tradeoff')]
            assert {'fast_ssh', 'quiet_ftp'} <= {r['template'] for r in rules}
            if privileged:
                assert 'privileged_ftp' in {r['template'] for r in rules}
            assert all('Route clue' not in str(obs) for obs in initial['observations'].values())
            # One legal acquisition for each distinct template in the world.
            discovered = await finish(bridge, {'Red_0': {'action': 'DiscoverRemoteSystems', 'target': initial['views']['Red_0']['known']['subnet'][0]}})
            for kind in sorted({r['template'] for r in rules}):
                rule = next(r for r in rules if r['template'] == kind)
                ip = address(initial, rule['target'])
                scanned = await finish(bridge, {'Red_0': {'action': 'DiscoverNetworkServices', 'target': ip}})
                assert scanned['views']['Red_0']['scan_cache']['0'][ip] == [rule['tradeoff']['port']]
                eid = scanned['observations']['Red_0']['evidence_id']
                clue = scanned['observations']['Red_0']['data'][ip]['Route clue']
                assert clue['estimated_exploit_ticks'] == rule['tradeoff']['exploit_ticks']
                assert 'detection_probability' not in clue and 'allowed_sources' not in clue
                assert 'Route clue' not in str(scanned['observations']['Red_1'])
                intel = await bridge.call('ingest_intel', sender='Red_0', recipient='Red_1', evidence_ids=[eid])
                assert intel['address_fragment'][ip]['Route clue'] == clue
                assert ip not in intel['view']['scan_cache']['0']
                started = await bridge.call('step', proposals={'Red_0': {'action': 'ExploitRemoteService', 'target': ip}})
                row = next(a for a in started['actions'] if a['actor'] == 'Red_0')
                assert row['duration'] == rule['tradeoff']['exploit_ticks']
                busy = await bridge.call('step', proposals={'Red_0': {'action': 'DiscoverNetworkServices', 'target': ip}})
                assert not next(a for a in busy['actions'] if a['actor'] == 'Red_0')['submitted']
                frame = busy
                while frame['views']['Red_0']['pending_action']:
                    frame = await bridge.call('step', proposals={})
                row = next(a for a in frame['actions'] if a['actor'] == 'Red_0')
                assert row['outcome'] == 'TRUE'
                assert row['concrete_action'].startswith('SSHBruteForce' if kind == 'fast_ssh' else 'FTPDirectoryTraversal')
                shell = next(s for s in frame['views']['Red_0']['sessions'] if s['hostname'] == rule['target'])
                assert shell['privileged'] == (kind == 'privileged_ftp')
                # Native inspection is needed even after direct root acquisition.
                frame = await finish(bridge, {'Red_0': {'action': 'PrivilegeEscalate', 'target': rule['target']}})
                assert address(initial, cfg.scenario.targets[0]) in frame['views']['Red_0']['known']['ip_address']
            # Adjacent seeds can legitimately produce the same permutation in
            # a small template space. Verify variation without demanding that
            # every seed change produce a unique recipe.
            for seed in (101, 102, 103):
                cfg.scenario.world_seed = seed
                changed = await bridge.call('create', config=cfg.model_dump())
                if initial['truth']['route_manifest']['rules'] != changed['truth']['route_manifest']['rules']:
                    break
            assert initial['truth']['route_manifest']['rules'] != changed['truth']['route_manifest']['rules']
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
def test_native_sensor_blocks_actual_exploit_then_releases_and_alternate_works(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / 'native.log', 'enterprise_cc4')
        try:
            await bridge.start()
            cfg = tradeoff_config(fast_detection_probability=1, quiet_detection_probability=0,
                                  reaction_delay=1, block_ticks=5, response_budget=1)
            initial = await bridge.call('create', config=cfg.model_dump())
            rules = initial['truth']['route_manifest']['rules']
            fast = next(r['target'] for r in rules if r['template'] == 'fast_ssh')
            quiet = next(r['target'] for r in rules if r['template'] == 'quiet_ftp')
            fast_ip, quiet_ip = address(initial, fast), address(initial, quiet)
            await finish(bridge, {'Red_0': {'action': 'DiscoverRemoteSystems', 'target': initial['views']['Red_0']['known']['subnet'][0]}})
            scanned = await finish(bridge, {'Red_0': {'action': 'DiscoverNetworkServices', 'target': fast_ip}})
            assert any(e['type'] == 'route_sensor_alert' and e['host'] == fast for e in scanned['defender_events'])
            blocked = await finish(bridge, {'Red_0': {'action': 'ExploitRemoteService', 'target': fast_ip}})
            assert blocked['actions'][0]['outcome'] == 'FALSE'
            assert blocked['truth']['route_pressure']['blocked_until'][fast] == 8
            assert initial['truth']['route_manifest']['foothold'] in blocked['truth']['blocks'][fast]
            scanned = await finish(bridge, {'Red_0': {'action': 'DiscoverNetworkServices', 'target': quiet_ip}})
            assert scanned['actions'][0]['outcome'] == 'TRUE'
            assert not any(e['type'] == 'route_sensor_alert' for e in scanned['defender_events'])
            frame = await finish(bridge, {'Red_0': {'action': 'ExploitRemoteService', 'target': quiet_ip}})
            assert frame['actions'][0]['outcome'] == 'TRUE'
            assert frame['truth']['route_pressure']['blocked_until'] == {}
            assert frame['truth']['blocks'] == initial['truth']['blocks']
            recovered = await finish(bridge, {'Red_0': {'action': 'ExploitRemoteService', 'target': fast_ip}})
            assert recovered['actions'][0]['outcome'] == 'TRUE'
            assert recovered['truth']['route_pressure']['responses_used'] == 1
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
def test_native_gateway_block_stops_pivot_traffic_without_revoking_owned_access(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / 'native.log', 'enterprise_cc4')
        try:
            await bridge.start()
            cfg = tradeoff_config(fast_detection_probability=1, quiet_detection_probability=0,
                                  reaction_delay=6, block_ticks=5, response_budget=1)
            initial = await bridge.call('create', config=cfg.model_dump())
            fast = next(r['target'] for r in initial['truth']['route_manifest']['rules'] if r['template'] == 'fast_ssh')
            await finish(bridge, {'Red_0': {'action': 'DiscoverRemoteSystems', 'target': initial['views']['Red_0']['known']['subnet'][0]}})
            for proposal in [{'action': 'DiscoverNetworkServices', 'target': address(initial, fast)},
                             {'action': 'ExploitRemoteService', 'target': address(initial, fast)},
                             {'action': 'PrivilegeEscalate', 'target': fast},
                             {'action': 'EstablishPivot', 'target': fast}]:
                frame = await finish(bridge, {'Red_0': proposal})
            assert frame['tick'] == 8 and frame['truth']['route_pressure']['blocked_until'][fast] == 13
            source = next(s['id'] for s in frame['views']['Red_0']['sessions'] if s['hostname'] == fast and s['controller'])
            target_ip = address(initial, cfg.scenario.targets[0])
            frame = await finish(bridge, {'Red_0': {'action': 'DiscoverNetworkServices', 'target': target_ip, 'session': source}})
            assert frame['actions'][0]['outcome'] == 'FALSE'
            assert any(s['id'] == source and s['active'] and s['privileged'] for s in frame['views']['Red_0']['sessions'])
            assert not any(e['type'] == 'route_sensor_observation' for e in frame['defender_events'])
            while frame['tick'] < 13:
                frame = await bridge.call('step', proposals={})
            assert frame['truth']['blocks'] == initial['truth']['blocks']
            frame = await finish(bridge, {'Red_0': {'action': 'DiscoverNetworkServices', 'target': target_ip, 'session': source}})
            assert frame['actions'][0]['outcome'] == 'TRUE'
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
def test_native_mixed_templates_across_layers_complete_a_legal_mission(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / 'native.log', 'enterprise_cc4')
        try:
            await bridge.start()
            cfg = tradeoff_config(workers=4, alternatives=3, privileged=True, reactive_blocks=False)
            cfg.scenario.complexity.routes.depth = 2
            initial = await bridge.call('create', config=cfg.model_dump())
            actors = initial['actors']
            await finish(bridge, {a: {'action': 'DiscoverRemoteSystems', 'target': initial['views'][a]['known']['subnet'][0]} for a in actors})
            sources = {a: 0 for a in actors}
            for layer in initial['truth']['route_manifest']['layers']:
                rules = [r for r in initial['truth']['route_manifest']['rules'] if r['target'] in layer]
                assert {'fast_ssh', 'quiet_ftp', 'privileged_ftp'} == {r['template'] for r in rules}
                for label, target in [('DiscoverNetworkServices', address(initial, layer[0])),
                                      ('ExploitRemoteService', address(initial, layer[0])),
                                      ('PrivilegeEscalate', layer[0]), ('EstablishPivot', layer[0])]:
                    frame = await finish(bridge, {a: {'action': label, 'target': target, 'session': sources[a]} for a in actors})
                    assert all(row['outcome'] == 'TRUE' for row in frame['actions'])
                sources = {a: next(s['id'] for s in frame['views'][a]['sessions'] if s['hostname'] == layer[0] and s['controller']) for a in actors}
            target = cfg.scenario.targets[0]
            for label, destination in [('DiscoverNetworkServices', address(initial, target)),
                                       ('ExploitRemoteService', address(initial, target)), ('PrivilegeEscalate', target)]:
                frame = await finish(bridge, {a: {'action': label, 'target': destination, 'session': sources[a]} for a in actors})
                assert all(row['outcome'] == 'TRUE' for row in frame['actions'])
            frame = await bridge.call('step', proposals={})
            assert frame['score']['mission_success']
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
@pytest.mark.parametrize('template,success', [('fast_ssh', True), ('quiet_ftp', False)])
def test_native_route_duration_changes_deadline_outcome(tmp_path, template, success):
    async def check():
        bridge = EngineBridge(tmp_path / 'native.log', 'enterprise_cc4')
        try:
            await bridge.start()
            cfg = tradeoff_config(reactive_blocks=False)
            cfg.scenario.mission.deadline_tick = 18
            initial = await bridge.call('create', config=cfg.model_dump())
            gate = next(r['target'] for r in initial['truth']['route_manifest']['rules'] if r['template'] == template)
            ip = address(initial, gate)
            await finish(bridge, {'Red_0': {'action': 'DiscoverRemoteSystems', 'target': initial['views']['Red_0']['known']['subnet'][0]}})
            for proposal in [{'action': 'DiscoverNetworkServices', 'target': ip},
                             {'action': 'ExploitRemoteService', 'target': ip},
                             {'action': 'PrivilegeEscalate', 'target': gate},
                             {'action': 'EstablishPivot', 'target': gate}]:
                frame = await finish(bridge, {'Red_0': proposal})
            source = next(s['id'] for s in frame['views']['Red_0']['sessions'] if s['hostname'] == gate and s['controller'])
            target = cfg.scenario.targets[0]
            for proposal in [{'action': 'DiscoverNetworkServices', 'target': address(initial, target)},
                             {'action': 'ExploitRemoteService', 'target': address(initial, target)},
                             {'action': 'PrivilegeEscalate', 'target': target}]:
                frame = await bridge.call('step', proposals={'Red_0': dict(proposal, session=source)})
                while frame['views']['Red_0']['pending_action'] and not frame['score']['mission_failure']:
                    frame = await bridge.call('step', proposals={})
                if frame['score']['mission_failure']:
                    break
            while not frame['score']['mission_success'] and not frame['score']['mission_failure']:
                frame = await bridge.call('step', proposals={})
            assert frame['score']['mission_success'] == success
            if success:
                assert frame['tick'] == 16
            else:
                assert frame['tick'] == 18 and frame['score']['mission_failure']['reason'] == 'mission_deadline'
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
def test_saved_workbench_clues_blocks_and_recovery_without_models(tmp_path):
    async def check():
        manager = RunManager(Store(tmp_path))
        try:
            cfg = tradeoff_config(fast_detection_probability=1, quiet_detection_probability=0,
                                  reaction_delay=6, block_ticks=5, response_budget=1)
            cfg.name = 'Software check - route clues and service quarantine'
            cfg.scenario.complexity.beliefs.enabled = True
            cfg.scenario.complexity.beliefs.stale_after = 1000
            cfg.cognition.scripted_policy = 'local_replan'
            run = manager.get((await manager.create(cfg))['id'])
            run.meta['software_fixture'] = True
            manager.store.update(run.meta)
            initial = run.frames[0]
            fast = next(r['target'] for r in initial['truth']['route_manifest']['rules'] if r['template'] == 'fast_ssh')
            async def act(proposal):
                await run.advance({'Red_0': proposal})
                while run.memory['Red_0'].view.get('pending_action'):
                    await run.advance()
                return run.frames[-1]
            await act({'action': 'DiscoverRemoteSystems', 'target': run.memory['Red_0'].view['known']['subnet'][0]})
            await act({'action': 'DiscoverNetworkServices', 'target': address(initial, fast)})
            scanned = manager.store.frame(run.id)
            assert scanned['private_views']['Red_0']['hosts'][address(initial, fast)]['fields']['Route clue']['service'] == 'SSH'
            assert 'route_pressure' not in str(run.memory['Red_0'].public_view(run.mission(), {}))
            for proposal in [{'action': 'ExploitRemoteService', 'target': address(initial, fast)},
                             {'action': 'PrivilegeEscalate', 'target': fast},
                             {'action': 'EstablishPivot', 'target': fast}]:
                frame = await act(proposal)
            source = next(s['id'] for s in run.memory['Red_0'].view['sessions'] if s['hostname'] == fast and s['controller'])
            target = cfg.scenario.targets[0]
            failed = await act({'action': 'DiscoverNetworkServices', 'target': address(initial, target), 'session': source})
            assert failed['tick'] == 9 and failed['actions'][0]['outcome'] == 'FALSE'
            while run.meta['tick'] < 13:
                await act({'action': 'Sleep'})
            for proposal in [{'action': 'DiscoverNetworkServices', 'target': address(initial, target)},
                             {'action': 'ExploitRemoteService', 'target': address(initial, target)},
                             {'action': 'PrivilegeEscalate', 'target': target}]:
                await act(dict(proposal, session=source))
            while run.meta['status'] != 'completed':
                await act({'action': 'Sleep'})
            saved = manager.store.frame(run.id)
            assert saved['score']['mission_success'] and run.meta['manual_intervention']
            assert run.meta['software_fixture'] and run.cognition.calls == 0
            assert any(e['type'] == 'route_block_started' for f in run.frames for e in f['defender_events'])
            assert any(e['type'] == 'route_block_released' for f in run.frames for e in f['defender_events'])
            assert saved['truth']['route_pressure']['blocked_until'] == {}
        finally:
            await manager.close()
    asyncio.run(check())
