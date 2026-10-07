"""A delivered task's eligibility is independent of strategy preferences."""
from types import SimpleNamespace
import asyncio

import pytest

from backend.app.knowledge import PrivateMemory
from backend.app.policies import Organization, candidates, key
from backend.app.research_policy import ResearchPolicy
from backend.app.runs import Run
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig
from packages.contracts.research_catalog import PUBLIC_CATALOG
from tests.research.helpers import config


def stale_task():
    memory = PrivateMemory('Red_0', SimpleNamespace(enabled=True, observation_delay=0, stale_after=8))
    target = '10.0.0.2'
    native = {'actor': 'Red_0', 'sessions': [
        {'id': 0, 'hostname': 'owned', 'controller': True, 'privileged': False, 'active': True}],
        'known': {'ip_address': [target], 'hostname': ['owned', 'goal'], 'subnet': []},
        'scan_cache': {'0': {target: [22]}}, 'catalog': PUBLIC_CATALOG,
        'possessed_tokens': ['opaque-local-test'], 'pending_action': None,
        'access_resources': {'remaining': 12}}
    memory.observe({'tick': 1, 'evidence_id': 'Red_0:1:0', 'data': {
        'owned': {'System info': {'Hostname': 'owned'}, 'Research evidence': [
            {'kind': 'artifact', 'token_ref': 'opaque-local-test', 'claimed_scope': 'goal'}]},
        target: {'System info': {'Hostname': 'goal'}, 'Research evidence': [
            {'kind': 'probe', 'source_host': 'owned', 'probe': 'auth_policy', 'port': 22,
             'response': 'password_and_account_token_supported'}]}}}, native)
    memory.advance_clock(20)
    task = next(p for p in candidates(memory) if p['action'] == 'AttemptAccess'
                and p['method'] == 'credential_login')
    memory.receive([{'kind': 'assignment', 'created_tick': 19, 'sender': 'Coordinator',
                    'payload': {'proposal': task}}])
    return memory, task


@pytest.mark.parametrize('provider', ['scripted', 'ollama'])
def test_visible_stale_task_is_admitted_for_both_providers(provider):
    memory, task = stale_task()
    cfg = EpisodeConfig.model_validate(config(workers=1, architecture='hierarchy'))
    cfg.cognition.provider = provider
    organization = Organization(cfg, ['Red_0'])
    state = memory.public_view({'target_names': ['goal']}, {})
    ranked, _ = ResearchPolicy('evidence_controller').rank(state, candidates(memory), 20)
    # The strategy recommends refreshing the aged handshake. That preference
    # cannot erase an otherwise eligible, fully cited, delivered leader task.
    assert not any(key(p) == key(task) for p in ranked)
    assert organization.assigned(memory, 20) == task
    if provider == 'scripted':
        assert organization.preferred(memory, 20)['action'] == 'Sleep'
    else:
        assert organization.preferred(memory, 20) == task


@pytest.mark.parametrize('invalid', ['citation', 'source', 'session', 'token'])
def test_assignment_never_rebinds_missing_owned_prerequisites(invalid):
    memory, task = stale_task()
    changes = {'citation': {'basis_evidence_ids': ['never-delivered']},
               'source': {'source_host': 'unowned'}, 'session': {'session': 9},
               'token': {'token_ref': 'not-possessed'}}[invalid]
    memory.inbox[-1]['payload']['proposal'] = dict(task, **changes)
    cfg = EpisodeConfig.model_validate(config(workers=1, architecture='hierarchy'))
    organization = Organization(cfg, ['Red_0'])
    assert organization.assigned(memory, 20)['action'] == 'Sleep'
    assert organization.preferred(memory, 20)['action'] == 'Sleep'


@pytest.mark.engine
def test_actual_native_gateway_admits_task_despite_scripted_recommendation(tmp_path):
    async def check():
        cfg = EpisodeConfig.model_validate(config(workers=1, architecture='hierarchy'))
        run = Run(cfg, Store(tmp_path))
        try:
            await run.initialize()
            # A mocked leader leaves the test's actual delivered task in place.
            # Transport remains the supported healthy research configuration.
            async def no_assignments(view, default):
                return {}
            run.cognition.coordinator = no_assignments
            task = next(p for p in candidates(run.memory['Red_0']) if p['action'] == 'InspectArtifacts')
            run.bus.enqueue('Coordinator', ['Red_0'], 'assignment', {'proposal': task}, [], 0)
            await run.advance()
            for _ in range(4):
                if not run.memory['Red_0'].view.get('pending_action'):
                    break
                await run.advance()
            assert any(h['proposal']['action'] == 'InspectArtifacts' and h.get('outcome') == 'TRUE'
                       for h in run.memory['Red_0'].history)
            exercised = []
            async def choose(actor, view, preferred):
                assert preferred['action'] == 'Sleep'
                assert run.organization.assigned(run.memory[actor], run.meta['tick'] + 1) == task
                exercised.append(actor)
                return task
            run.cognition.worker = choose
            tick = run.meta['tick']
            run.bus.enqueue('Coordinator', ['Red_0'], 'assignment', {'proposal': task}, [], tick)
            await run.advance()
            for _ in range(4):
                if not run.memory['Red_0'].view.get('pending_action'):
                    break
                await run.advance()
            assert exercised
            completed = [a for frame in run.frames[tick + 1:] for a in frame['actions']
                         if a['proposal']['action'] == 'InspectArtifacts' and a.get('lifecycle') == 'completed']
            assert completed and all(a['valid'] and a['outcome'] == 'TRUE' for a in completed)
            assert run.cognition.calls == 0
            assert run.meta['organization_version'] == '1.1'
        finally:
            await run.stop()
    asyncio.run(check())
