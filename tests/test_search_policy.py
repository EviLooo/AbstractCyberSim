"""Hand-checkable search, privacy and bounded native software qualification."""
import asyncio
import copy
import itertools
import json

import pytest
from backend.app.search_policy import SearchPolicy, search_paths
from backend.app.runs import RunManager
from backend.app.storage import Store
from packages.contracts.models import SearchSettings
from tests.test_baselines import local_view, development_config
from tests.test_route_tradeoffs import tradeoff_config


def graph_fixture():
    return {'entry': [{'target': 'fast', 'ticks': 2, 'score': 12},
                      {'target': 'quiet', 'ticks': 7, 'score': 7}],
            'fast': [{'target': 'goal', 'ticks': 3, 'score': 3}],
            'quiet': [{'target': 'goal', 'ticks': 3, 'score': 3}]}


@pytest.mark.parametrize('budget,expected,ticks', [(None,'quiet',10), (6,'fast',5), (4,'fast',5)])
def test_uniform_cost_search_uses_risk_time_tradeoff_and_reports_infeasible_deadline(budget, expected, ticks):
    graph = graph_fixture()
    result = search_paths('entry', graph, {'goal'}, SearchSettings(), budget)
    assert result['path'][0]['target'] == expected and result['ticks'] == ticks
    assert result['deadline_feasible'] == (budget is None or ticks <= budget)
    assert not result['truncated']


def test_search_matches_exhaustive_small_graph_and_does_not_prune_fast_expensive_label():
    # Both paths join at the same node: a score-only visited set would wrongly
    # discard the fast label and fail to find the deadline-feasible goal path.
    for slow_ticks, fast_score, budget in itertools.product([4,8], [6,10], [5,12]):
        graph = {'entry':[{'target':'join','ticks':slow_ticks,'score':slow_ticks},
                          {'target':'join','ticks':2,'score':fast_score}],
                 'join':[{'target':'goal','ticks':2,'score':2}]}
        paths = [(e['ticks']+2,e['score']+2) for e in graph['entry']]
        feasible = [p for p in paths if p[0] <= budget]
        expected = min(feasible, key=lambda p:p[1]) if feasible else min(paths)
        actual = search_paths('entry',graph,{'goal'},SearchSettings(),budget)
        assert (actual['ticks'],actual['score']) == expected
    limited = search_paths('entry',graph_fixture(),{'goal'},SearchSettings(max_expansions=1))
    assert limited['truncated'] and limited['goal'] is None


def test_objective_deadlines_and_privileged_service_hints_are_public_planning_inputs():
    view, _ = local_view()
    view['mission']['requirements'] = {'hold_ticks':2,'deadline_tick':40,'objectives':[
        {'targets':['goal'],'hold_ticks':3,'deadline_tick':7,'requires_privileged_hosts':[]}]}
    view['hosts']['10.0.0.3']['fields']['Route clue'] = {'estimated_exploit_ticks':2,'service_account_hint':'privileged service'}
    proposal = {'action':'ExploitRemoteService','target':'10.0.0.3','session':0}
    _,trace = SearchPolicy().rank(view,[proposal],1)
    preferred = trace['alternatives'][0]
    assert [p['action'] for p in preferred['plan']] == ['ExploitRemoteService']
    assert trace['search']['goal_time_budgets']['goal'] == 3
    assert preferred['estimated_total_ticks'] == 2 and preferred['deadline_feasible']


def test_observed_policy_changes_route_for_deadline_and_ignores_hidden_state():
    view, _ = local_view()
    view['native']['scan_cache']['0'] = {'10.0.0.2':[22], '10.0.0.3':[21]}
    for ip, name, duration, risk in [('10.0.0.2','goal',2,'high'),('10.0.0.3','goal',8,'low')]:
        view['hosts'][ip] = {'fields':{'System info':{'Hostname':name},'Interface':[{'IP Address':ip}],
            'Route clue':{'estimated_exploit_ticks':duration,'route_sensor_exposure':risk}}}
    choices = [{'action':'ExploitRemoteService','target':ip,'session':0} for ip in ['10.0.0.2','10.0.0.3']]
    ranked, trace = SearchPolicy().rank(view, choices, 1)
    assert ranked[0]['target'] == '10.0.0.3'
    assert SearchPolicy({'risk_weight':0}).rank(view,choices,1)[0][0]['target'] == '10.0.0.2'
    view['mission']['requirements'] = {'deadline_tick':7,'hold_ticks':1}
    ranked, trace = SearchPolicy().rank(view, choices, 1)
    assert ranked[0]['target'] == '10.0.0.2'
    assert trace['alternatives'][0]['deadline_feasible']
    hidden = copy.deepcopy(view)
    hidden.update(truth={'winning_route':'SECRET'},route_pressure={'blocked_until':{'SECRET':999}},defender_events=[{'host':'SECRET'}])
    assert SearchPolicy().rank(hidden,choices,1) == SearchPolicy().rank(view,choices,1)
    assert 'SECRET' not in json.dumps(trace)


def test_search_remembers_observed_path_after_loss_but_requires_own_rescans():
    view, _ = local_view()
    policy = SearchPolicy()
    view['native']['pivot_enabled'] = True
    view['native']['sessions'].append({'id':2,'hostname':'gate','active':True,'controller':True,'privileged':True})
    view['native']['scan_cache']['2'] = {'10.0.0.3':[22]}
    view.pop('local_state',None)
    policy.rank(view,[],1)
    view['native']['sessions'] = view['native']['sessions'][:1]
    view['native']['scan_cache'] = {'0':{}}
    view['belief_epoch'] = 1
    view['hosts']['10.0.0.2'] = {'fields':{'System info':{'Hostname':'gate'},'Interface':[{'IP Address':'10.0.0.2'}]}}
    scan = {'action':'DiscoverNetworkServices','target':'10.0.0.2','session':0}
    ranked, trace = policy.rank(view,[scan],2)
    assert ranked == [scan]
    plan = trace['alternatives'][0]['plan']
    assert trace['alternatives'][0]['search_goal'] == 'goal'
    assert [p['action'] for p in plan] == ['DiscoverNetworkServices','ExploitRemoteService','PrivilegeEscalate','EstablishPivot',
                                         'DiscoverNetworkServices','ExploitRemoteService','PrivilegeEscalate']
    assert plan[4]['source_host'] == 'gate'
    assert view['native']['scan_cache'] == {'0':{}}


def test_positive_edge_memory_is_shared_with_every_provider_and_does_not_become_live_cache():
    from tests.test_organization_qualification import memory
    m = memory('Red_0')
    m.view['scan_cache']['0'] = {'10.0.0.3':[22]}
    first = m.public_view({'target_names':['goal']},{})
    edges = first['local_state']['observed_service_edges']
    assert len(edges)==1 and edges[0]['target_address']=='10.0.0.3'
    m.view['scan_cache'] = {'0':{}}
    m.epoch = 1
    m.tick = 5
    later = m.public_view({'target_names':['goal']},{})
    assert later['local_state']['observed_service_edges'] == edges
    assert later['native']['scan_cache']=={'0':{}}
    assert later['local_state']['belief_epoch']==1 and edges[0]['belief_epoch']==0
    assert all('truth' not in row for row in edges)


def test_failed_choices_replan_idempotently_and_peer_access_does_not_satisfy_goal():
    view, choices = local_view()
    view['mission']['target_names'].append('other_goal')
    view['hosts']['10.0.0.2'] = {'fields':{'System info':{'Hostname':'other_goal'},'Interface':[{'IP Address':'10.0.0.2'}]}}
    policy = SearchPolicy()
    before, _ = policy.rank(view,choices,1)
    view['history'] = [{'started_tick':1,'proposal':before[0],'valid':True,'outcome':'FALSE'}]
    after, trace = policy.rank(view,choices,2)
    assert after[0] != before[0]
    again, second = policy.rank(view,choices,2)
    assert again == after
    assert sum(a['observed_failures'] for a in trace['alternatives']) == sum(a['observed_failures'] for a in second['alternatives']) == 1
    view.setdefault('reported_hosts',{})['goal'] = {'fields':{'privileged':True}}
    assert policy.rank(view,choices,3)[1]['status'] != 'holding_own_goals'


@pytest.mark.engine
@pytest.mark.parametrize('architecture,workers', [('independent',1),('hierarchy',2),('swarm',2)])
def test_native_search_uses_delivered_organization_and_saves_decisions(tmp_path,architecture,workers):
    async def check():
        manager = RunManager(Store(tmp_path))
        try:
            cfg = development_config('C0','local_search',architecture,workers)
            run = manager.get((await manager.create(cfg))['id'])
            run.meta['software_fixture'] = True
            while run.meta['status'] not in ['completed','errored']:
                await run.advance()
            assert run.meta['termination_reason'] == 'mission_success', (run.meta,run.frames[-1].get('decisions'))
            assert run.cognition.calls == 0 and not run.meta['manual_intervention']
            traces = [d for f in run.frames for d in f['decisions'].values()]
            assert traces and all(d['policy'] == 'local_search' for d in traces)
            assert any(d['alternatives'] and d['alternatives'][0]['plan'] for d in traces)
            if architecture != 'independent':
                behavior = run.frames[-1]['diagnostics']['behavior']
                assert behavior['delivered_assignments' if architecture=='hierarchy' else 'delivered_claims'] > 0
        finally:
            await manager.close()
    asyncio.run(check())


@pytest.mark.engine
@pytest.mark.parametrize('cell',['C1','C2','route_pressure'])
def test_native_search_recovers_and_composes_route_choices_without_models(tmp_path,cell):
    async def check():
        manager = RunManager(Store(tmp_path))
        try:
            cfg = development_config(cell,'local_search') if cell != 'route_pressure' else tradeoff_config(
                fast_detection_probability=1,quiet_detection_probability=0,reaction_delay=6,block_ticks=5,response_budget=1)
            cfg.cognition.scripted_policy = 'local_search'
            cfg.cognition.action_retry_limit = 6
            cfg.cognition.failure_backoff_ticks = 8
            cfg.schedule.max_ticks = 240
            run = manager.get((await manager.create(cfg))['id'])
            run.meta['software_fixture'] = True
            while run.meta['status'] not in ['completed','errored']:
                await run.advance()
            assert run.meta['termination_reason'] == 'mission_success', (cell,run.meta,run.frames[-1].get('decisions'))
            assert run.cognition.calls == 0 and not run.meta['manual_intervention']
            if cell == 'C2':
                assert any(e['type']=='defender_response_completed' for f in run.frames for e in f['defender_events'])
                assert any(e['type']=='access_lost' for m in run.memory.values() for e in m.ledger.events)
        finally:
            await manager.close()
    asyncio.run(check())
