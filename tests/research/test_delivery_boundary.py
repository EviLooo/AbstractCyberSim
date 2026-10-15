"""A8 actual native evidence, observation delay and organization transport."""
import asyncio
import copy
import json

import pytest
from backend.app.runs import Run
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig
from tests.research.helpers import config


@pytest.mark.engine
@pytest.mark.parametrize('architecture', ['hierarchy', 'swarm'])
def test_token_requires_observed_origin_and_delivered_authorized_message(tmp_path, architecture):
    async def check():
        cfg = config(workers=2, architecture=architecture, credential_variant='valid',
                     evidence={'observation_delay':2, 'stale_after':8})
        cfg['communication']['extra_delay'] = 2
        run = Run(EpisodeConfig.model_validate(cfg), Store(tmp_path))
        try:
            await run.initialize()
            tick = 0
            async def step(proposals=None):
                nonlocal tick
                frame = await run.engine.call('step', proposals=proposals or {})
                tick = frame['tick']
                for actor in run.actors:
                    run.memory[actor].observe(frame['observations'][actor], frame['views'][actor])
                deliveries, _ = run.bus.deliver(tick)
                await run.bridge_messages(deliveries)
                if architecture == 'hierarchy':
                    run.organization.coordinator_view(deliveries['Coordinator'], tick)
                return frame

            entry = run.memory['Red_1'].view['sessions'][0]['hostname']
            await step({'Red_1':{'action':'InspectArtifacts', 'target':entry}})
            completed = await step()
            eid = completed['observations']['Red_1']['evidence_id']
            token = completed['views']['Red_1']['possessed_tokens'][0]
            assert token not in run.memory['Red_1'].view.get('possessed_tokens', [])
            peer_before = copy.deepcopy(completed['views']['Red_0'])
            # A worker cannot forward evidence still hidden by its own channel.
            kind = 'assignment' if architecture == 'hierarchy' else 'claim'
            sender = 'Coordinator' if architecture == 'hierarchy' else 'Red_1'
            run.bus.enqueue(sender, ['Red_0'], kind, {}, [eid], tick)
            if architecture == 'swarm':
                run.bus.enqueue('Red_1', ['Red_0'], 'claim', {}, ['Red_1:invented'], tick)
            for _ in range(3):
                await step()
            assert token in run.memory['Red_1'].view['possessed_tokens']
            assert token not in run.memory['Red_0'].view.get('possessed_tokens', [])
            if architecture == 'hierarchy':
                assert not run.organization.reports
                report = {'sessions':copy.deepcopy(run.memory['Red_1'].view['sessions'])}
                run.bus.enqueue('Red_1', ['Coordinator'], 'report', report, [eid], tick)
                # Coordinator cannot relay a report before its delivery.
                run.bus.enqueue('Coordinator', ['Red_0'], 'assignment', {}, [eid], tick)
                for _ in range(3):
                    await step()
                assert token not in run.memory['Red_0'].view.get('possessed_tokens', [])
                assert run.organization.reports['Red_1']['evidence_ids'] == [eid]
                assert run.relay_evidence[eid] == tick
            run.bus.enqueue(sender, ['Red_0'], kind, {}, [eid], tick)
            for _ in range(2):
                await step()
                assert token not in run.memory['Red_0'].view.get('possessed_tokens', [])
            delivered = await step()
            assert token in run.memory['Red_0'].view['possessed_tokens']
            assert delivered['views']['Red_0']['sessions'] == peer_before['sessions']
            assert delivered['views']['Red_0']['scan_cache'] == peer_before['scan_cache']
            assert run.memory['Red_0'].view['sessions'] == peer_before['sessions']
            records = [r for r in run.memory['Red_0'].research_evidence if r.get('token_ref') == token]
            assert records and all(r['observed_tick'] == 2 and r['received_tick'] == tick for r in records)
            assert all(r['origin'] == 'Red_1' for r in records)
            events = [json.loads(row) for row in (run.directory/'events.jsonl').read_text(encoding='utf-8').splitlines()]
            assert any(e['type'] == 'intel_rejected' for e in events)
            assert any(e['type'] == 'intel_delivery' for e in events)
            assert run.cognition.calls == 0
        finally:
            await run.stop()
    asyncio.run(check())
