"""Aging evidence must not starve a new source-specific investigation."""
from backend.app.research_policy import ResearchPolicy
from packages.contracts.research_catalog import PUBLIC_CATALOG
from backend.app.policies import Organization
from packages.contracts.models import EpisodeConfig
from tests.research.helpers import config
from types import SimpleNamespace


def view(records=(), epoch=0):
    return {"belief_epoch": epoch, "history": [], "hosts": {}, "reported_hosts": {},
            "mission": {"target_names": ["goal"]}, "research_evidence": list(records),
            "native": {"sessions": [], "catalog": PUBLIC_CATALOG,
                       "scan_cache": {"0": {host: [80, 22] for host in ("blocked", "fresh", "goal", "unexplored")}},
                       "possessed_tokens": [], "access_resources": {"remaining": 4}}}


def probe(target, kind="service_behavior", source="owned"):
    return {"action": "Probe", "target": target, "source_host": source,
            "session": 0, "probe": kind, "port": 80 if kind == "service_behavior" else 22}


def record(target, response, stale=True):
    return {"kind": "probe", "host": target, "source_host": "owned", "probe": "service_behavior",
            "port": 80, "response": response, "observed_tick": 2, "stale": stale}


def test_negative_peer_evidence_is_not_repeated_just_because_it_aged():
    policy = ResearchPolicy("evidence_controller")
    policy.rank(view(), [], 0)
    options, _ = policy.rank(view([record("blocked", "timeout")]),
                             [probe("blocked"), probe("fresh", "auth_policy")], 20)
    assert [p["target"] for p in options] == ["fresh"]
    # A new own-access epoch legitimately permits reinvestigating old evidence.
    options, _ = policy.rank(view([record("blocked", "timeout")], epoch=1), [probe("blocked")], 21)
    assert len(options) == 1


def test_stale_positive_refresh_does_not_starve_unknown_authentication():
    policy = ResearchPolicy("evidence_controller")
    policy.rank(view(), [], 0)
    options, _ = policy.rank(view([record("goal", "external_import_accepted")]),
                             [probe("goal"), probe("unexplored", "auth_policy")], 20)
    assert options[0]["target"] == "unexplored"
    options, _ = policy.rank(view([record("fresh", "external_import_accepted", stale=False)]),
                             [probe("fresh")], 20)
    assert options == []


def test_controller_does_not_age_diagnostics_before_acquiring_its_own_cache():
    state = view()
    state["native"]["scan_cache"] = {}
    options, _ = ResearchPolicy("evidence_controller").rank(state, [probe("fresh")], 0)
    assert options == []


def test_hierarchy_progress_report_keeps_original_age_and_grants_no_session():
    state=view([record('fresh','external_import_accepted',stale=False)])
    state.update(actor='Red_1',coordination={'claim_ttl':5})
    state['inbox']=[{'kind':'assignment','created_tick':10,'payload':{'coordination_reports':[
        {'sender':'Red_0','created_tick':8,'reported_sessions':[
            {'hostname':'fresh','active':True,'privileged':False}]}]}}]
    proposal={'action':'AttemptAccess','target':'fresh','session':0,'source_host':'owned','method':'web_rfi'}
    options,_=ResearchPolicy('evidence_controller').rank(state,[proposal],10)
    assert options==[] and state['native']['sessions']==[]
    # A newer relay time cannot extend the original report's lifetime.
    options,_=ResearchPolicy('evidence_controller').rank(state,[proposal],14)
    assert len(options)==1 and state['native']['sessions']==[]


def test_hierarchy_duplicate_admission_identity_ignores_evidence_ids_only():
    organization=Organization(EpisodeConfig.model_validate(config(architecture='hierarchy')),['Red_0','Red_1'])
    proposal={'action':'AttemptAccess','session':0,'target':'fresh','source_host':'owned','method':'web_rfi'}
    for index,actor in enumerate(organization.actors):
        organization.reports[actor]={'sender':actor,'created_tick':2,'evidence_ids':[actor+':obs'],
            'payload':{'belief_epoch':0,'sessions':[{'active':True,'controller':True,'id':0}],
                       'candidates':[dict(proposal,basis_evidence_ids=[actor+':obs'])]}}
    tasks=organization.scripted_assignments()
    assert len(tasks)==1
    assert tasks['Red_0']['proposal']['basis_evidence_ids']==['Red_0:obs']
    assert tasks['Red_0']['coordination_reports'][0]['created_tick']==2
    organization.reports['Red_1']['payload']['candidates'][0]['source_host']='different_owned_source'
    assert len(organization.scripted_assignments())==2


def test_hierarchy_access_assignment_reservation_survives_report_round_trip():
    organization=Organization(EpisodeConfig.model_validate(config(architecture='hierarchy')),['Red_0','Red_1'])
    original={'action':'AttemptAccess','target':'fresh','session':0,'source_host':'owned',
              'method':'web_rfi','basis_evidence_ids':['Red_0:1']}
    task={'proposal':original,'evidence_ids':['Red_0:1']}
    accepted,_=organization.admit_hierarchy_assignments({'Red_0':task},2)
    assert accepted=={'Red_0':task}
    duplicate={'proposal':dict(original,basis_evidence_ids=['Red_1:2']),'evidence_ids':['Red_1:2']}
    accepted,rejected=organization.admit_hierarchy_assignments({'Red_1':duplicate},4)
    assert not accepted and len(rejected)==1
    # Completion is learned from an actual delivered report, not shared memory.
    organization.reports['Red_0']={'payload':{'recent_actions':[
        {'proposal':original,'observed_tick':6,'remaining_ticks':0,'outcome':'FALSE'}]}}
    accepted,_=organization.admit_hierarchy_assignments({'Red_1':duplicate},7)
    assert accepted=={'Red_1':duplicate}
    # Lost reports have a bounded expiry; no permanent global lock.
    organization.reports.clear()
    accepted,_=organization.admit_hierarchy_assignments({'Red_0':task},30)
    assert accepted=={'Red_0':task}


def test_swarm_claim_delivery_precedes_access_for_every_decision_provider():
    cfg = EpisodeConfig.model_validate(config(workers=2, architecture="swarm"))
    # extra_delay belongs to transport, not to the hidden recipe.
    cfg.communication.extra_delay = 2
    organization = Organization(cfg, ["Red_0", "Red_1"])
    proposal = {"action": "AttemptAccess", "target": "10.0.0.1", "source_host": "owned",
                "session": 0, "method": "web_rfi", "basis_evidence_ids": ["Red_1:0"]}
    memory = SimpleNamespace(actor="Red_1", inbox=[])
    assert organization.admit_swarm(memory, proposal, 1)["action"] == "Sleep"
    assert organization.admit_swarm(memory, proposal, 3)["action"] == "Sleep"
    memory.inbox.append({"kind": "claim", "sender": "Red_0", "created_tick": 1,
                         "payload": {"proposal": dict(proposal, basis_evidence_ids=["Red_0:0"])}})
    assert organization.admit_swarm(memory, proposal, 4)["action"] == "Sleep"
    # Without a delivered conflicting claim, the local intent can be admitted.
    memory.inbox.clear()
    assert organization.admit_swarm(memory, proposal, 4) == proposal


def test_programmed_leader_uses_fresh_delivered_ownership_without_transfer():
    org=Organization(EpisodeConfig.model_validate(config(architecture='hierarchy')),['Red_0','Red_1'])
    target='10.0.0.2'
    attempt={'action':'AttemptAccess','target':target,'session':0,'source_host':'entry','method':'web_rfi'}
    other={'action':'DiscoverNetworkServices','target':'10.0.0.3','session':0,'source_host':'entry'}
    for actor in org.actors:
        org.reports[actor]={'sender':actor,'created_tick':8,'evidence_ids':[actor+':8'],
          'payload':{'belief_epoch':0,'sessions':[{'active':True,'controller':True,'id':0,'hostname':'entry'}],
                     'research_evidence':[{'lead':{'address':target,'hostname':'branch'}}],
                     'candidates':[attempt,other]}}
    org.reports['Red_0']['payload']['sessions'].append({'active':True,'controller':False,'id':1,'hostname':'branch'})
    org.reports['Red_0']['payload']['candidates']=[]
    org.coordinator_view([],10)
    assert org.scripted_assignments()['Red_1']['proposal']==other
    assert len(org.reports['Red_1']['payload']['sessions'])==1
    # No fresh report means no permanent ownership lock or invented knowledge.
    org.coordinator_view([],14)
    assert org.scripted_assignments()['Red_1']['proposal']==attempt


def test_evidence_controller_prioritizes_disclosed_leads_without_filtering_unknowns():
    state=view()
    state['research_evidence']=[{'kind':'artifact','host':'own','leads':[{'address':'hinted','hostname':'note-claim'}], 'evidence_id':'note'}]
    scans=[{'action':'DiscoverNetworkServices','target':target,'session':0,'source_host':'owned'} for target in ['incidental','hinted']]
    ranked,_=ResearchPolicy('evidence_controller').rank(state,scans,1)
    assert [p['target'] for p in ranked]==['hinted','incidental']
    assert scans[0]['target']=='incidental'
    ranked,_=ResearchPolicy('fixed_workflow').rank(state,scans,1)
    # Fixed priority is unchanged by the contents of notes.
    empty=dict(state,research_evidence=[])
    assert ResearchPolicy('fixed_workflow').rank(empty,scans,1)[0]==ranked


def test_observed_goal_completion_precedes_nonessential_local_inventory():
    state=view()
    state['native']['sessions']=[{'hostname':'goal','active':True,'privileged':False}]
    options=[{'action':'InspectArtifacts','target':'goal','session':1,'source_host':'goal'},
             {'action':'PrivilegeEscalate','target':'goal','session':0,'source_host':'owned'}]
    ranked,_=ResearchPolicy('evidence_controller').rank(state,options,10)
    assert ranked[0]['action']=='PrivilegeEscalate'
    assert {p['action'] for p in ranked}=={'PrivilegeEscalate','InspectArtifacts'}
