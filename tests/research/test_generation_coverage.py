"""A10 finite software qualification, not policy or scientific performance.

Each supported recipe/count/access/condition/change cell has an isolated legal
native witness and three unchanged negative attempts. Two role permutations are
checked; one worker uses the common-entry single-agent control. Live models and
scientific metrics are never invoked. Reports survive a failing later cell.
"""
import asyncio
import itertools
import json
import random

import pytest
from backend.app.bridge import EngineBridge
from tests.research.helpers import config, finish, ip, action, TARGET_A


def role_seeds():
    found = {}
    for seed in range(20):
        order = [1, 2]
        random.Random(f'recipe-v1:{seed}').shuffle(order)
        found.setdefault(tuple(order), seed)
    assert len(found) == 2
    return list(found.values())


def cells():
    access = [(1, 'common_entry'), (2, 'common_entry'), (4, 'common_entry'),
              (2, 'matched_split_entry'), (4, 'matched_split_entry')]
    variants = ['import_enabled', 'import_disabled', 'source_denied', 'ssh_hardened']
    for recipe, (workers, entry), variant, seed in itertools.product(
            ['linear_control', 'investigate', 'combine', 'recover'], access, variants, role_seeds()):
        for change in (['patch_rfi', 'restore'] if recipe == 'recover' else [None]):
            yield recipe, workers, entry, variant, seed, change


@pytest.mark.engine
def test_every_core_cell_native_positive_negative_and_feasibility(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / 'native.log', 'enterprise_cc4_research')
        evidence = tmp_path / 'coverage.jsonl'
        count = 0
        try:
            await bridge.start()
            for recipe, workers, entry_access, variant, seed, change in cells():
                options = dict(initial_access=entry_access, credential_variant='invalid',
                               seed_namespaces={'recipe': seed, 'event': 701})
                if change:
                    options['change'] = {'mode': change, 'response_budget': 1, 'response_delay': 4}
                cfg = config(variant, recipe, workers, **options)
                initial = await bridge.call('create', config=cfg)
                report = await bridge.call('qualify', config=cfg)
                label = [recipe, workers, entry_access, variant, seed, change]
                with evidence.open('a', encoding='utf-8') as saved:
                    saved.write(json.dumps({'cell': label, 'qualification': report}) + '\n')
                assert report['status'] == 'native_witness_validated', (label, report)
                assert report['world_id'] == initial['world']['world_id']
                assert report['ticks'] == report['native_step_count']
                assert report['final_score']['mission_success']
                assert all(a['valid'] and a['outcome'] == 'TRUE' for a in report['witness'])
                # Negative checks run on the evaluated world, still at tick zero:
                # qualification cannot grant it a token, session or action tick.
                assert not initial['views']['Red_0']['possessed_tokens']
                entry = initial['views']['Red_0']['sessions'][0]['hostname']
                frame = await finish(bridge, {'action':'InspectArtifacts', 'target':entry})
                assert frame['tick'] == 2
                target = ip(initial, TARGET_A)
                effective_variant = 'import_enabled' if recipe == 'linear_control' else variant
                if effective_variant == 'source_denied' and recipe != 'combine':
                    # The entry route is denied: it cannot acquire a scan cache,
                    # so an attempted access there would be gateway-invalid.
                    denied = await finish(bridge, {'action':'Probe', 'target':target,
                                                  'probe':'connectivity', 'port':80})
                    assert any(r.get('response') == 'timeout' for fields in denied['observations']['Red_0']['data'].values()
                               if isinstance(fields, dict) for r in fields.get('Research evidence', []))
                if effective_variant == 'source_denied' or recipe == 'combine':
                    # Combine's target lead itself requires local investigation
                    # on a branch; do not fabricate initial target knowledge.
                    target = ip(initial, initial['truth']['research_truth']['roles']['archive'])
                await finish(bridge, {'action':'DiscoverNetworkServices', 'target':target})
                method = 'web_rfi' if effective_variant in ('import_disabled', 'source_denied') or recipe == 'combine' else 'ssh_weak_auth'
                failures = []
                for _ in range(3):
                    frame = await finish(bridge, {'action':'AttemptAccess', 'target':target, 'method':method})
                    record = action(frame)
                    assert record['valid'] and record['outcome'] == 'FALSE', (label, record)
                    failures.append(record)
                assert not frame['score']['mission_success']
                assert frame['views']['Red_0']['access_resources']['reserved'] == 3
                with evidence.open('a', encoding='utf-8') as saved:
                    saved.write(json.dumps({'cell':label, 'negative_attempts':failures,
                                           'negative_final_tick':frame['tick']})+'\n')
                count += 1
            assert count == 200
        finally:
            await bridge.close()
    asyncio.run(check())
