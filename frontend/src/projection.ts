import type { Frame } from './types';

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
    return {id:host.id, subnet, label:knownName ? host.id : ip || 'Observed host', router:truth ? host.router : knownName && host.id.endsWith('_router'), target:truth && host.target, color:sessions.some(s => s.privileged) ? '#a74327' : sessions.length ? '#e9a164' : truth && host.router ? '#72868a' : '#becbc8'};
  });
  const zones = truth ? frame.truth.subnets.filter(s => hosts.some(h => h.subnet === s.id)).map(s => ({id:s.id,label:`${s.id.toUpperCase()} / ${s.cidr}`})) : [...new Set(hosts.map(h => h.subnet))].map(id => ({id,label:id === 'unknown' ? 'OBSERVED ADDRESSES · SUBNET UNKNOWN' : id}));
  const ids = new Set(hosts.map(h => h.id));
  return {hosts,zones,edges:truth ? frame.truth.edges.filter(e => ids.has(e.source) && ids.has(e.target)) : []};
}

export function projectTeam(frame: Frame, run: {architecture:string}, tick: number) {
  // Older saved frames use their declared architecture; new frames include
  // the exact configured directed links and their state at the saved tick.
  if (frame.communication_topology) return frame.communication_topology;
  const actors = Object.keys(frame.private_views);
  const reasoners = [...actors,...(run.architecture === 'hierarchy' ? ['Coordinator'] : [])];
  return reasoners.flatMap(sender => reasoners.filter(recipient => recipient !== sender && run.architecture !== 'independent' && (run.architecture !== 'hierarchy' || ((sender === 'Coordinator') !== (recipient === 'Coordinator')))).map(recipient => ({sender,recipient,active:true,interruption_indices:[],tick})));
}
