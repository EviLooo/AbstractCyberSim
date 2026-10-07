import test from 'node:test';
import assert from 'node:assert/strict';
import {readLocation,writeLocation} from '../src/location.ts';
import {projectNetwork,projectTeam,projectSummary,projectLinkCount} from '../src/projection.ts';
import {projectBeliefs} from '../src/beliefProjection.ts';
import {projectRoutes} from '../src/routeProjection.ts';
import {projectMission} from '../src/missionProjection.ts';
import {projectTimeline} from '../src/timelineProjection.ts';
import {projectDecisions} from '../src/decisionProjection.ts';

test('refresh preserves saved run, tick, selected worker and panel', () => {
  const state = {page:'laboratory',run:'a'.repeat(32),tick:3,mode:'team',view:'Red_1',selection:'Red_1'};
  assert.deepEqual(readLocation(writeLocation(state)),state);
  assert.equal(readLocation('?run=../../file&tick=-1&view=unknown').run,null);
  assert.equal(readLocation('?run='+'a'.repeat(32)+'&tick=10001').tick,null);
});

const frame = {
  tick:2, messages:[],
  truth:{subnets:[{id:'SecretZone',cidr:'10.0.0.0/24'}],edges:[{id:'physical',source:'UnknownName',target:'HiddenHost'}],hosts:[
    {id:'UnknownName',subnet:'SecretZone',router:false,target:true,interfaces:[{'IP Address':'10.0.0.2'}],sessions:[{agent:'Red_1',privileged:true}]},
    {id:'HiddenHost',subnet:'SecretZone',router:true,target:false,interfaces:[{'IP Address':'10.0.0.3'}],sessions:[]}
  ]},
  private_views:{Red_0:{native:{known:{hostname:[],ip_address:['10.0.0.2'],subnet:[]},sessions:[]}},Red_1:{native:{known:{hostname:[],ip_address:[],subnet:[]},sessions:[]}}}
};

test('route view discloses ACL recipes only to researcher truth',()=>{
  const f=structuredClone(frame);
  f.truth.route_manifest={enabled:true,layers:[['HiddenGateway']],rules:[{target:'HiddenTarget',allowed_sources:['HiddenGateway']}]};
  f.private_views.Red_0.native.sessions=[{id:2,hostname:'OwnedPivot',active:true,controller:true,privileged:true}];
  f.private_views.Red_1.native.sessions=[{id:3,hostname:'OtherPivot',active:true,controller:true,privileged:true}];
  const privateData=projectRoutes(f,'Red_0');
  assert.equal(privateData.manifest,null);
  assert.equal(privateData.controllers.length,1);
  assert.equal(privateData.controllers[0].host,'OwnedPivot');
  assert.ok(!JSON.stringify(privateData).includes('Hidden'));
  assert.equal(projectRoutes(f,'truth').controllers.length,2);
  assert.deepEqual(projectRoutes(f,'truth').manifest,f.truth.route_manifest);
});

test('private mission projection never reveals confirmed team dwell or peer access',()=>{
  const f=structuredClone(frame);
  f.score={mission:{hold_ticks:9,failure:{reason:'hidden'},objectives:[{id:'hidden_objective'}]}};
  f.private_views.Red_0.mission={target_names:['PublicTarget'],requirements:{hold_ticks:10,deadline_tick:50}};
  f.private_views.Red_0.native.sessions=[{hostname:'OwnedTarget',active:true,privileged:true}];
  f.private_views.Red_1.native.sessions=[{hostname:'PeerSecret',active:true,privileged:true}];
  const projected=projectMission(f,'Red_0');
  assert.equal(projected.progress,null);
  assert.deepEqual(projected.owned,['OwnedTarget']);
  assert.equal(projected.requirements.requirements.hold_ticks,10);
  assert.ok(!JSON.stringify(projected).includes('PeerSecret'));
  assert.ok(!JSON.stringify(projected).includes('hidden'));
  assert.deepEqual(projectMission(f,'truth').progress,f.score.mission);
});

test('CC4 labels stay readable while keeping native host identities', () => {
  const host='restricted_zone_a_subnet_server_host_0';
  const cc4={...frame,engine_profile:'enterprise_cc4',truth:{...frame.truth,hosts:[{...frame.truth.hosts[0],id:host,subnet:'restricted_zone_a_subnet'}],subnets:[{id:'restricted_zone_a_subnet',cidr:'10.0.0.0/24'}]}};
  const projected=projectNetwork(cc4,'truth');
  assert.equal(projected.hosts[0].id,host);
  assert.equal(projected.hosts[0].label,'SERVER 0');
  assert.equal(projected.zones[0].label,'RESTRICTED ZONE A / 10.0.0.0/24');
  assert.equal(projectNetwork(cc4,'Red_0').hosts[0].label,'10.0.0.2');
});

test('private graph hides unknown hostname, subnet, edges and peer privilege', () => {
  const projected = projectNetwork(frame,'Red_0');
  assert.equal(projected.hosts.length,1);
  assert.equal(projected.hosts[0].label,'10.0.0.2');
  assert.equal(projected.hosts[0].subnet,'unknown');
  assert.equal(projected.hosts[0].target,false);
  assert.equal(projected.hosts[0].color,'#becbc8');
  assert.deepEqual(projected.edges,[]);
  assert.ok(!JSON.stringify(projected.zones).includes('SecretZone'));
  assert.deepEqual(projectNetwork(frame,'Red_7').hosts,[]);
  assert.equal(projectNetwork(frame,'truth').hosts.length,2);
});

test('known subnet can group an observed address without truth zone names', () => {
  const copy = structuredClone(frame);
  copy.private_views.Red_0.native.known.subnet = ['10.0.0.0/24'];
  assert.equal(projectNetwork(copy,'Red_0').hosts[0].subnet,'10.0.0.0/24');
});

test('team visualization uses recorded sparse link direction and outage', () => {
  const copy = {...frame,communication_topology:[{sender:'Red_0',recipient:'Red_1',active:false,interruption_indices:[0]}]};
  assert.deepEqual(projectTeam(copy,{architecture:'swarm'},2),copy.communication_topology);
  assert.equal(projectTeam(frame,{architecture:'hierarchy'},2).length,4);
  assert.equal(projectTeam(frame,{architecture:'independent'},2).length,0);
});

test('belief panel selects recipient-local evidence without truth or peer events', () => {
  const copy=structuredClone(frame);
  copy.private_views.Red_0.beliefs={records:[{host:'10.0.0.2',stale:true}],events:[{type:'access_lost',host:'observed'}]};
  copy.private_views.Red_1.beliefs={records:[{host:'SECRET_PEER'}],events:[{type:'access_recovered',host:'SECRET_HOST'}]};
  const privateEvidence=projectBeliefs(copy,'Red_0');
  assert.equal(privateEvidence.length,1);
  assert.ok(!JSON.stringify(privateEvidence).includes('SECRET'));
  assert.ok(!JSON.stringify(privateEvidence).includes('SecretZone'));
  assert.equal(privateEvidence[0].beliefs.records[0].stale,true);
  assert.equal(projectBeliefs(copy,'truth').length,2);
  assert.deepEqual(projectBeliefs(copy,'Red_7'),[]);
  assert.deepEqual(projectBeliefs(frame,'Red_0'),[]);
});


test('private decision view hides structural recipes and other workers choices',()=>{
  const f=structuredClone(frame);
  f.diagnostics={structure:{hiddenRecipe:'secret'},behavior:{teamFailures:9}};
  f.decisions={Red_0:{actor:'Red_0',policy:'local_replan'},Red_1:{actor:'Red_1',secret:'peer'}};
  const d=projectDecisions(f,'Red_0');
  assert.equal(d.structure,null);assert.equal(d.behavior,null);
  assert.deepEqual(Object.keys(d.decisions),['Red_0']);
  assert.ok(!JSON.stringify(d).includes('secret'));
  assert.deepEqual(projectDecisions(f,'truth').structure,f.diagnostics.structure);
});

test('route tradeoff projection shows delivered clues but hides recipes and sensor state',()=>{
  const f=structuredClone(frame);
  f.truth.route_manifest={enabled:true,tradeoffs:{enabled:true},rules:[{target:'secret',tradeoff:{detection_probability:0.9}}]};
  f.truth.route_pressure={blocked_until:{secret:20},pending_alerts:{secret:2}};
  f.private_views.Red_0.hosts={'10.0.0.2':{fields:{'Route clue':{service:'FTP',route_sensor_exposure:'low'}},evidence_ids:['own']}};
  f.private_views.Red_0.reported_hosts={'10.0.0.4':{fields:{'Route clue':{service:'SSH'}},evidence_ids:['delivered']}};
  const own=projectRoutes(f,'Red_0');
  assert.equal(own.manifest,null);assert.equal(own.pressure,null);
  assert.equal(own.clues.length,2);
  assert.ok(!JSON.stringify(own).includes('secret'));
  assert.deepEqual(projectRoutes(f,'Red_7').clues,[]);
  assert.equal(projectRoutes(f,'truth').pressure.blocked_until.secret,20);
});

test('search plan projection preserves own estimated path and excludes peer plans',()=>{
  const f=structuredClone(frame);
  f.decisions={Red_0:{policy:'local_search',alternatives:[{plan:[{action:'DiscoverNetworkServices',target:'observed',estimated_ticks:1}],planning_score:12,deadline_feasible:false}]},
    Red_1:{policy:'local_search',alternatives:[{plan:[{target:'PEER_SECRET'}]}]}};
  const own=projectDecisions(f,'Red_0');
  assert.equal(own.decisions.Red_0.alternatives[0].plan[0].target,'observed');
  assert.equal(own.decisions.Red_0.alternatives[0].deadline_feasible,false);
  assert.ok(!JSON.stringify(own).includes('PEER_SECRET'));
  assert.deepEqual(projectDecisions(f,'Red_7').decisions,{});
});


test('private summary cannot disclose peer access, team progress, tokens or messages',()=>{
  const f=structuredClone(frame);
  f.score={targets_reached:2,target_count:2,controlled_hosts:['peer1','peer2','own']};
  f.cognition={is_llm:true,charged_tokens:900,per_actor_usage:{Red_0:{charged_tokens:14},Red_1:{charged_tokens:886}}};
  f.messages=[{status:'delivered'},{status:'delivered'}];
  f.private_views.Red_0.mission={target_names:['public-target']};
  f.private_views.Red_0.native.sessions=[{active:true,hostname:'own',privileged:true},{active:false,hostname:'public-target',privileged:true}];
  f.private_views.Red_0.inbox=[{status:'delivered'}];
  assert.deepEqual(projectSummary(f,'Red_0'),{targets:0,targetCount:1,hosts:1,tokens:14,messages:1});
  f.score.targets_reached=100;f.score.controlled_hosts=['secret'];f.cognition.charged_tokens=50000;f.messages.push({status:'delivered'});
  assert.deepEqual(projectSummary(f,'Red_0'),{targets:0,targetCount:1,hosts:1,tokens:14,messages:1});
  assert.deepEqual(projectSummary(f,'truth'),{targets:100,targetCount:2,hosts:1,tokens:50000,messages:3});
  delete f.cognition.per_actor_usage;
  assert.equal(projectSummary(f,'Red_0').tokens,null);
});


test('environment timeline separates recorded truth events from delivered own symptoms',()=>{
  const f=structuredClone(frame);
  f.truth.research_truth={response:{history:[{type:'research_defender_signal',signal_tick:3,host:'hidden',sensor:'sensor'},
    {type:'research_defender_decision',decision_tick:7,host:'hidden',action:'Restore'},
    {type:'research_defender_effect',effect_tick:11,host:'hidden',action:'Restore',outcome:'TRUE'}]}};
  f.private_views.Red_0.beliefs={events:[{type:'access_lost',tick:11,host:'known'}]};
  f.private_views.Red_0.research_evidence=[{observed_tick:9,received_tick:12,host:'known',response:'timeout',origin:'Red_0',source:'self_observed'}];
  f.private_views.Red_1.beliefs={events:[{type:'access_recovered',tick:13,host:'peer-hidden'}]};
  const own=projectTimeline(f,'Red_0');
  assert.deepEqual(Object.keys(own),['Observed worker symptoms']);
  assert.equal(own['Observed worker symptoms'][0].received,12);
  assert.ok(!JSON.stringify(own).includes('hidden'));
  const truth=projectTimeline(f,'truth');
  assert.equal(truth['Defender signals'][0].tick,3);
  assert.equal(truth['Defender decisions'][0].tick,7);
  assert.equal(truth['Defender effects'][0].tick,11);
  assert.equal(truth['Observed worker symptoms'].length,3);
});


test('private graph uses delivered source-bound probe records, never physical truth links',()=>{
  const f=structuredClone(frame); f.engine_profile='enterprise_cc4_research';
  f.private_views.Red_0.native.known.hostname=['HiddenHost'];
  f.private_views.Red_0.research_evidence=[{host:'10.0.0.2',source_host:'HiddenHost',probe:'connectivity',response:'tcp_handshake',observed_tick:1,evidence_id:'own1',origin:'Red_0',stale:false},
    {host:'10.0.0.2',source_host:'HiddenHost',probe:'connectivity',response:'timeout',observed_tick:2,evidence_id:'peer2',origin:'Red_1',stale:true},
    {host:'10.0.0.2',source_host:'undiscovered',probe:'connectivity',response:'tcp_handshake',observed_tick:2,evidence_id:'hidden'}];
  const edges=projectNetwork(f,'Red_0').edges;
  assert.equal(edges.length,1);assert.equal(edges[0].evidence_id,'peer2');
  assert.equal(edges[0].source,'HiddenHost');assert.equal(edges[0].target,'UnknownName');
  assert.equal(edges[0].failed,true);assert.equal(edges[0].reported,true);assert.equal(edges[0].stale,true);
  assert.ok(!JSON.stringify(edges).includes('physical'));
});

test('private organization graph never counts unseen peer communications',()=>{
  const f=structuredClone(frame);f.messages=[{sender:'Red_0',recipient:'Red_1',status:'delivered'}];
  f.private_views.Red_0.inbox=[{sender:'Red_1',recipient:'Red_0',status:'delivered'}];
  assert.equal(projectLinkCount(f,'Red_0','Red_0','Red_1'),null);
  assert.equal(projectLinkCount(f,'Red_0','Red_1','Red_0'),1);
  assert.equal(projectLinkCount(f,'truth','Red_0','Red_1'),1);
});
