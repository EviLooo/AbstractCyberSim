"""A task's declared source cannot silently rebind an actor-local session ID."""
import asyncio

import pytest
from backend.app.bridge import EngineBridge
from tests.research.helpers import config, finish, action, TARGET_A, ip


@pytest.mark.engine
def test_identical_session_number_different_owner_host_is_rejected(tmp_path):
    async def check():
        bridge=EngineBridge(tmp_path/'native.log','enterprise_cc4_research')
        try:
            await bridge.start()
            frame=await bridge.call('create',config=config(workers=2,initial_access='matched_split_entry',credential_variant='valid'))
            target=ip(frame,TARGET_A)
            own=frame['views']['Red_0']['sessions'][0]['hostname']
            peer=frame['views']['Red_1']['sessions'][0]['hostname']
            assert own!=peer
            await finish(bridge,{'action':'InspectArtifacts','target':own})
            forged=await finish(bridge,{'action':'Probe','probe':'connectivity','port':80,'target':target,'source_host':peer})
            assert not action(forged)['valid']
            assert 'source does not match' in action(forged)['rejection']
            assert forged['views']['Red_0']['access_resources']['reserved']==0
            accepted=await finish(bridge,{'action':'Probe','probe':'connectivity','port':80,'target':target,'source_host':own})
            assert action(accepted)['valid'] and action(accepted)['outcome']=='TRUE'
            assert len(accepted['views']['Red_0']['sessions'])==1
            assert len(accepted['views']['Red_1']['sessions'])==1
        finally:
            await bridge.close()
    asyncio.run(check())
