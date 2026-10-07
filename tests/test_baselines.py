"""T12f development fixtures. No research sweep, provider calls or oracle input."""
import asyncio
import copy
import json
import pytest
from backend.app.baselines import BaselinePolicy, LocalStateTracker
from backend.app.diagnostics import reduce_decisions
from backend.app.knowledge import PrivateMemory
from backend.app.policies import candidates, key
from backend.app.runs import RunManager
from backend.app.storage import Store
from packages.contracts.models import CognitionConfig, EpisodeConfig
from packages.contracts.complexity import BeliefSettings
from packages.contracts.missions import MissionSettings
from tests.test_cc4_routes import routed
from tests.test_organization_qualification import memory


def local_view():
    m = memory('Red_0')
    m.view['scan_cache']['0'] = {'10.0.0.2': [22]}
    m.hosts['10.0.0.3'] = {'fields': {'System info': {'Hostname': 'goal'},
        'Interface': [{'IP Address': '10.0.0.3'}]}, 'evidence_ids': [], 'source': 'self_observed'}
    return m.public_view({'target_names': ['goal']}, {}), candidates(m)


def test_rules_and_replan_choose_different_observed_frontiers_without_truth():
    view, options = local_view()
    rules, r = BaselinePolicy('local_rules').rank(view, options, 1)
    plans, p = BaselinePolicy('local_replan').rank(view, options, 1)
    assert rules[0]['action'] == 'ExploitRemoteService'
    assert plans[0]['action'] == 'DiscoverNetworkServices' and plans[0]['target'] == '10.0.0.3'
    assert p['candidate_count'] > 1 and p['alternatives'][0]['observed_goal']
    hidden = copy.deepcopy(view)
    hidden.update(truth={'winning_path': 'secret'}, defender_events=[{'host': 'secret'}])
    assert BaselinePolicy('local_replan').rank(hidden, options, 1) == BaselinePolicy('local_replan').rank(view, options, 1)
    assert 'secret' not in json.dumps(p)


def test_tracker_separates_facts_from_policy_and_resets_after_own_loss():
    view, options = local_view()
    tracker = LocalStateTracker()
    tracker.update(view, 0)
    view['history'] = [{'started_tick': 1, 'belief_epoch': 0,
        'proposal': options[0], 'valid': True, 'outcome': 'FALSE'}]
    tracker.update(view, 2); tracker.update(view, 2)
    assert sum(tracker.failures.values()) == 1
    view['native']['sessions'] = []
    view['belief_epoch'] = 1
    changed = tracker.update(view, 3)
    assert changed['lost_controllers'] == [0] and tracker.failures == {}
    assert tracker.address_names['10.0.0.3'] == 'goal'


def test_replan_prefers_observed_reachable_source_over_newer_failed_source():
    view, _ = local_view()
    view['native']['sessions'].append({'id': 2, 'hostname': 'new_pivot', 'active': True, 'controller': True, 'privileged': True})
    view['native']['scan_cache']['0']['10.0.0.3'] = [22]
    scan = {'action': 'DiscoverNetworkServices', 'target': '10.0.0.3', 'session': 2}
    exploit = {'action': 'ExploitRemoteService', 'target': '10.0.0.3', 'session': 0}
    view['history'] = [{'started_tick': 1, 'proposal': scan, 'outcome': 'FALSE', 'valid': True}]
    ranked, trace = BaselinePolicy('local_replan').rank(view, [scan, exploit], 3)
    assert ranked[0] == exploit
    assert trace['alternatives'][0]['observed_service_evidence']


def test_inventory_hostname_key_is_usable_observed_goal_evidence():
    view, options = local_view()
    view['hosts'] = {'goal': {'fields': {'Interface': [{'IP Address': '10.0.0.3'}]}}}
    ranked, trace = BaselinePolicy('local_replan').rank(view, options, 1)
    assert ranked[0]['target'] == '10.0.0.3' and trace['alternatives'][0]['observed_goal']


def test_local_holding_uses_owned_access_not_forged_peer_reports():
    view, options = local_view()
    view['reported_hosts'] = {'goal': {'fields': {'privileged': True}}}
    assert BaselinePolicy('local_replan').rank(view, options, 1)[1]['status'] != 'holding_own_goals'
    view['native']['sessions'].append({'id': 1, 'hostname': 'goal', 'active': True, 'controller': False, 'privileged': True})
    assert BaselinePolicy('local_replan').rank(view, options, 2)[1]['status'] == 'holding_own_goals'


def test_diagnostics_count_completions_and_delivery_once_by_hand():
    attempt = {'actor': 'Red_0', 'proposal': {'action': 'ExploitRemoteService', 'target': 'x', 'session': 0},
               'valid': True, 'submitted': True, 'remaining_ticks': 3, 'outcome': 'IN_PROGRESS'}
    completed = dict(attempt, submitted=False, remaining_ticks=0, outcome='FALSE')
    scan = dict(attempt, proposal={'action': 'DiscoverNetworkServices', 'target': 'y', 'session': 2},
                remaining_ticks=0, outcome='TRUE')
    message = {'id': 'a', 'status': 'delivered', 'kind': 'assignment'}
    frames = [{'actions': [], 'messages': []}, {'actions': [attempt], 'decisions': {
        'Red_0': {'candidate_count': 2, 'state_change': {'changed': True}}}},
        {'actions': [completed]}, {'actions': [scan], 'messages': [message]},
        {'actions': [], 'messages': [message]}]
    d = reduce_decisions(frames)
    assert d['decision_count'] == d['multiple_candidate_decisions'] == d['changed_state_decisions'] == 1
    assert d['completed_failed_actions'] == d['completed_service_scans'] == d['source_switches'] == 1
    assert d['delivered_assignments'] == 1 and d['delivered_claims'] == 0


def test_shared_candidate_retry_backoff_and_recovery_reset():
    cognition = CognitionConfig(action_retry_limit=3, failure_backoff_ticks=4)
    m = PrivateMemory('Red_0', cognition=cognition, track_access_loss=True)
    m.view = memory('Red_0').view
    proposal = candidates(m)[0]
    m.history = [{'proposal': proposal, 'valid': True, 'outcome': 'FALSE',
                  'started_tick': 1, 'observed_tick': 2, 'belief_epoch': 0}]
    m.tick = 5
    assert key(proposal) not in [key(p) for p in candidates(m)]
    m.tick = 6
    assert key(proposal) in [key(p) for p in candidates(m)]
    m.history *= 3
    assert key(proposal) not in [key(p) for p in candidates(m)]
    m.epoch = 1
    assert key(proposal) in [key(p) for p in candidates(m)]
    for patch in [{'scripted_policy': 'oracle'}, {'action_retry_limit': 0},
                  {'provider': 'ollama', 'model': 'unused', 'scripted_policy': 'local_replan'}]:
        with pytest.raises(ValueError): CognitionConfig.model_validate(patch)


def development_config(cell, policy, architecture='independent', workers=1):
    cfg = routed(workers=workers, depth=1, alternatives=1 if cell == 'C0' else 2,
                 dead=cell != 'C0')
    cfg.team.architecture = architecture
    cfg.cognition.scripted_policy = policy
    cfg.cognition.action_retry_limit = 3
    cfg.cognition.failure_backoff_ticks = 3
    cfg.schedule.max_ticks = 240
    cfg.name = f'Software fixture {cell} {policy} {architecture}'
    if cell != 'C0':
        cfg.scenario.targets = ['restricted_zone_a_subnet_server_host_0', 'restricted_zone_b_subnet_server_host_0']
    if cell == 'C2':
        cfg.scenario.defender = 'reactive_restore'
        cfg.scenario.cc4.response_delay = 12
        cfg.scenario.cc4.response_budget = 1
        cfg.scenario.complexity.beliefs = BeliefSettings(enabled=True, stale_after=8)
        cfg.scenario.mission = MissionSettings(hold_ticks=20)
    return EpisodeConfig.model_validate(cfg.model_dump())


@pytest.mark.engine
@pytest.mark.parametrize('cell', ['C0', 'C1', 'C2'])
@pytest.mark.parametrize('policy', ['local_rules', 'local_replan'])
def test_native_development_cells_succeed_without_hidden_plans(tmp_path, cell, policy):
    async def check():
        manager = RunManager(Store(tmp_path))
        try:
            run = manager.get((await manager.create(development_config(cell, policy)))['id'])
            run.meta['software_fixture'] = True
            while run.meta['status'] not in ['completed', 'errored']:
                await run.advance()
            assert run.meta['termination_reason'] == 'mission_success', (cell, policy, run.meta, run.frames[-1].get('decisions'))
            assert run.cognition.calls == 0 and not run.meta['manual_intervention']
            assert all(d['policy'] == policy for f in run.frames for d in f['decisions'].values())
            assert any(d['candidate_count'] > 1 for f in run.frames for d in f['decisions'].values())
            final = manager.store.frame(run.id)
            assert final['diagnostics']['behavior'] == reduce_decisions(run.frames)
            if cell == 'C2':
                assert any(e['type'] == 'defender_response_completed' for f in run.frames for e in f['defender_events'])
                assert any(e['type'] == 'access_lost' for m in run.memory.values() for e in m.ledger.events)
                assert any(e['type'] == 'access_recovered' for m in run.memory.values() for e in m.ledger.events)
            if cell == 'C1':
                assert final['diagnostics']['structure']['declared_gateway_combinations'] == 2
        finally:
            await manager.close()
    asyncio.run(check())


@pytest.mark.engine
@pytest.mark.parametrize('architecture', ['hierarchy', 'swarm'])
def test_new_policy_respects_organization_and_delivered_coordination(tmp_path, architecture):
    async def check():
        manager = RunManager(Store(tmp_path))
        try:
            cfg = development_config('C0', 'local_replan', architecture, 2)
            run = manager.get((await manager.create(cfg))['id'])
            run.meta['software_fixture'] = True
            while run.meta['status'] not in ['completed', 'errored']:
                await run.advance()
            assert run.meta['termination_reason'] == 'mission_success', run.meta
            counts = run.frames[-1]['diagnostics']['behavior']
            assert counts['delivered_assignments' if architecture == 'hierarchy' else 'delivered_claims'] > 0
            assert counts['delivered_claims' if architecture == 'hierarchy' else 'delivered_assignments'] == 0
            assert run.cognition.calls == 0
        finally:
            await manager.close()
    asyncio.run(check())
