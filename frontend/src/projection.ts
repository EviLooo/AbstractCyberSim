import type { Frame } from './types';

export function projectSummary(frame: Frame, view: string) {
  if (view === 'truth') return {targets:frame.score.targets_reached, targetCount:frame.score.target_count,
    hosts:frame.score.controlled_hosts.length, tokens:frame.cognition.charged_tokens,
    messages:frame.messages.filter(m=>m.status==='delivered').length};
  const actor=frame.private_views[view];
  const sessions=actor?.native.sessions.filter(s=>s.active) ?? [];
  const targets=actor?.mission?.target_names ?? [];
  return {targets:new Set(sessions.filter(s=>s.privileged && targets.includes(String(s.hostname))).map(s=>s.hostname)).size,
    targetCount:targets.length, hosts:new Set(sessions.map(s=>s.hostname)).size,
    tokens:frame.cognition.per_actor_usage?.[view]?.charged_tokens ?? (frame.cognition.is_llm ? null : 0),
    messages:actor?.inbox.filter(m=>m.status==='delivered').length ?? 0};
}

function contains(cidr: string, ip: string) {
  const [network, bits] = cidr.split('/');
  const number = (address: string) => address.split('.').reduce((total, part) => (total * 256 + Number(part)) >>> 0,0);
  const mask = Number(bits) === 0 ? 0 : (0xffffffff << (32 - Number(bits))) >>> 0;
  return (number(network) & mask) === (number(ip) & mask);
}

export function projectNetwork(frame: Frame, view: string) {
  const truth = view === 'truth';
  const native = frame.private_views[view]?.native;
  const observed = truth ? frame.truth.hosts : native ? frame.truth.hosts.filter(h => native.known.hostname.includes(h.id) || h.interfaces.some(i => native.known.ip_address.includes(String(i['IP Address'])))) : [];
  const hosts = observed.map(host => {
    const knownName = truth || !!native?.known.hostname.includes(host.id);
    const ip = host.interfaces.map(i => String(i['IP Address'])).find(ip => native?.known.ip_address.includes(ip));
    const subnet = truth ? host.subnet : native?.known.subnet.find(cidr => ip && contains(cidr,ip)) || 'unknown';
    const sessions = truth ? host.sessions.filter(s => s.agent.startsWith('Red_')) : native!.sessions.filter(s => s.hostname === host.id && s.active);
    const name = frame.engine_profile?.startsWith('enterprise_cc4') ? host.id.replace(/^.*_subnet_user_host_(\d+)$/,'USER $1').replace(/^.*_subnet_server_host_(\d+)$/,'SERVER $1').replace(/^.*_subnet_router$/,'ROUTER').replace(/^internet_root_host$/,'INTERNET') : host.id;
    return {id:host.id, subnet, label:knownName ? name + (frame.engine_profile === 'enterprise_cc4_research' && !truth && ip ? '\n' + ip : '') : ip || 'Observed host', router:truth ? host.router : knownName && host.id.endsWith('_router'), target:truth && host.target, color:sessions.some(s => s.privileged) ? '#a74327' : sessions.length ? '#e9a164' : truth && host.router ? '#72868a' : '#becbc8'};
  });
  const zones = truth ? frame.truth.subnets.filter(s => hosts.some(h => h.subnet === s.id)).map(s => ({id:s.id,label:`${s.id.replace(/_subnet$/,'').replaceAll('_',' ').toUpperCase()} / ${s.cidr}`})) : [...new Set(hosts.map(h => h.subnet))].map(id => ({id,label:id === 'unknown' ? 'OBSERVED ADDRESSES · SUBNET UNKNOWN' : id}));
  const ids = new Set(hosts.map(h => h.id));
  const edges:{id:string;source:string;target:string;label?:string;reported?:boolean;stale?:boolean;failed?:boolean;evidence_id?:string}[]=truth ? frame.truth.edges.filter(e => ids.has(e.source) && ids.has(e.target)) : [];
  if(!truth && frame.engine_profile==='enterprise_cc4_research') {
    const latest=new Map<string,NonNullable<Frame['private_views'][string]['research_evidence']>[number]>();
    for(const r of frame.private_views[view]?.research_evidence??[]) {
      if(r.probe!=='connectivity' || !r.source_host || !ids.has(r.source_host))continue;
      const target=observed.find(h=>h.interfaces.some(i=>String(i['IP Address'])===r.host));
      if(!target || !ids.has(target.id))continue;
      const k=`${r.source_host}:${target.id}:${r.port??0}`;
      if(!latest.has(k) || latest.get(k)!.observed_tick<=r.observed_tick)latest.set(k,r);
    }
    for(const [k,r] of latest) {
      const target=observed.find(h=>h.interfaces.some(i=>String(i['IP Address'])===r.host))!;
      edges.push({id:`observed-${k}`,source:r.source_host!,target:target.id,
        label:`${r.response}${r.port ? ` :${r.port}` : ''} · t${r.observed_tick}`,reported:r.origin!==view,stale:r.stale,
        failed:r.response==='timeout',evidence_id:r.evidence_id});
    }
  }
  return {hosts,zones,edges};
}

export function projectLinkCount(frame:Frame,view:string,sender:string,recipient:string) {
  if(view!=='truth' && recipient!==view)return null;
  return (view==='truth' ? frame.messages : frame.private_views[view]?.inbox??[])
    .filter(m=>m.sender===sender && m.recipient===recipient && m.status==='delivered').length;
}

export function projectTeam(frame: Frame, run: {architecture:string}, tick: number) {
  // Older saved frames use their declared architecture; new frames include
  // the exact configured directed links and their state at the saved tick.
  if (frame.communication_topology) return frame.communication_topology;
  const actors = Object.keys(frame.private_views);
  const reasoners = [...actors,...(run.architecture === 'hierarchy' ? ['Coordinator'] : [])];
  return reasoners.flatMap(sender => reasoners.filter(recipient => recipient !== sender && run.architecture !== 'independent' && (run.architecture !== 'hierarchy' || ((sender === 'Coordinator') !== (recipient === 'Coordinator')))).map(recipient => ({sender,recipient,active:true,interruption_indices:[],tick})));
}
