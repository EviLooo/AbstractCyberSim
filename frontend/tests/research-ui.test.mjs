import test from 'node:test';
import assert from 'node:assert/strict';
import {readLocation,writeLocation} from '../src/location.ts';
import {projectNetwork,projectTeam} from '../src/projection.ts';

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
