"""Ownership, fixed-policy and interrupted-clock acceptance fixtures."""
import asyncio
import copy
import json

import pytest
from backend.app.bridge import EngineBridge
from backend.app.runs import Run
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig
from tests.research.helpers import config, finish, ip, action, evidence, TARGET_A


@pytest.mark.engine
def test_root_only_artifact_ownership_and_direct_infrastructure_denial(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / 'native.log', 'enterprise_cc4_research')
        try:
            await bridge.start()
            frame = await bridge.call('create', config=config(recipe='combine', initial_access='matched_split_entry'))
            roles = frame['truth']['research_truth']['roles']
            entry = roles['entry']
            wrong_local = await finish(bridge, {'action':'InspectArtifacts','target':roles['split_entry']})
            assert not action(wrong_local)['valid']
            await finish(bridge, {'action':'InspectArtifacts','target':entry})
            archive = ip(frame, roles['archive'])
            await finish(bridge, {'action':'DiscoverNetworkServices','target':archive})
            frame = await finish(bridge, {'action':'AttemptAccess','method':'ssh_weak_auth','target':archive})
            local = next(s['id'] for s in frame['views']['Red_0']['sessions'] if s['hostname']==roles['archive'])
            frame = await finish(bridge, {'action':'InspectArtifacts','session':local,'target':roles['archive']})
            assert not any('Administrator-only' in r.get('text','') for r in evidence(frame))
            await finish(bridge, {'action':'PrivilegeEscalate','target':roles['archive']})
            frame = await finish(bridge, {'action':'InspectArtifacts','session':local,'target':roles['archive']})
            assert any('Administrator-only' in r.get('text','') for r in evidence(frame))
            subnet = frame['views']['Red_0']['known']['subnet'][0]
            frame = await finish(bridge, {'action':'DiscoverRemoteSystems','target':subnet})
            router = next(h for h in frame['truth']['hosts'] if h['router'])
            address = ip(frame, router['id'])
            before = copy.deepcopy(frame['views']['Red_0']['sessions'])
            await finish(bridge, {'action':'DiscoverNetworkServices','target':address})
            frame = await finish(bridge, {'action':'AttemptAccess','method':'web_rfi','target':address})
            assert frame['views']['Red_0']['sessions']==before
            assert action(frame)['outcome']!='TRUE'
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
def test_fixed_native_policy_remains_constant_across_historical_phase_boundary(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / 'native.log', 'enterprise_cc4_research')
        try:
            await bridge.start()
            frame = await bridge.call('create', config=config())
            initial = copy.deepcopy(frame['truth']['intended_policy'])
            blocks = copy.deepcopy(frame['truth']['blocks'])
            for _ in range(65):
                frame = await bridge.call('step', proposals={})
            assert frame['truth']['mission_phase']==0
            assert frame['truth']['intended_policy']==initial and frame['truth']['blocks']==blocks
            assert frame['tick']==frame['native_step_count']==65
        finally:
            await bridge.close()
    asyncio.run(check())


@pytest.mark.engine
def test_stop_preserves_an_unfinished_native_action_without_claiming_completion(tmp_path):
    async def check():
        run = Run(EpisodeConfig.model_validate(config(workers=1)), Store(tmp_path))
        try:
            await run.initialize()
            await run.advance()
            assert run.memory['Red_0'].view['pending_action']['remaining_ticks']==1
            await run.stop()
            partial = json.loads((run.directory/'interrupted-actions.json').read_text(encoding='utf-8'))
            assert partial['tick']==1 and partial['actions']['Red_0']['proposal']['action']=='InspectArtifacts'
            assert run.meta['status']=='stopped' and not run.meta['metrics']['success']
        finally:
            await run.stop()
    asyncio.run(check())


@pytest.mark.engine
def test_interrupted_access_keeps_its_team_reservation_and_unknown_outcome(tmp_path):
    async def check():
        run = Run(EpisodeConfig.model_validate(config(workers=1)), Store(tmp_path))
        try:
            await run.initialize()
            await run.advance()
            await run.advance()
            target = ip(run.frames[-1], TARGET_A)
            await run.advance({'Red_0': {'action':'DiscoverNetworkServices', 'target':target}})
            await run.advance({'Red_0': {'action':'AttemptAccess', 'method':'web_rfi', 'target':target}})
            assert run.memory['Red_0'].view['access_resources']['reserved']==1
            await run.stop()
            partial = json.loads((run.directory/'interrupted-actions.json').read_text(encoding='utf-8'))
            assert partial['actions']['Red_0']['proposal']['action']=='AttemptAccess'
            assert partial['actions']['Red_0']['remaining_ticks']==3
            assert run.memory['Red_0'].view['access_resources']['settled']==0
            assert not run.meta['metrics']['success']
        finally:
            await run.stop()
    asyncio.run(check())
