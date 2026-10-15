import type { ActorView, Host } from './types';

export default function KnowledgeInspector({ actor, host }: {actor: ActorView;host: Host}) {
  const addresses = host.interfaces.map(i => String(i['IP Address'])).filter(ip => actor.native.known.ip_address.includes(ip));
  const matching = (records: ActorView['hosts']) => Object.fromEntries(Object.entries(records).filter(([id,record]) => id === host.id || (record.fields['System info'] as {Hostname?:string}|undefined)?.Hostname === host.id || addresses.includes(id)));
  return <><p>Only this worker’s observations and delivered verified reports are shown.</p><h3>Self observations</h3><pre>{JSON.stringify(matching(actor.hosts),null,2)}</pre><h3>Verified peer reports</h3><pre>{JSON.stringify(matching(actor.reported_hosts || {}),null,2)}</pre></>;
}
