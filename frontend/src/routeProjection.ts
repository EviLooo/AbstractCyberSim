import type {Frame} from './types';

export function projectRoutes(frame:Frame, view:string) {
  const own = Object.entries(frame.private_views).filter(([actor])=>view==='truth'||actor===view)
    .flatMap(([actor,data])=>data.native.sessions.filter(s=>s.active&&s.controller).map(s=>({actor,id:Number(s.id),host:String(s.hostname),privileged:!!s.privileged})));
  const clues=Object.entries(frame.private_views).filter(([actor])=>view==='truth'||actor===view)
    .flatMap(([actor,data])=>[data.reported_hosts??{},data.hosts??{}].flatMap(hosts=>Object.entries(hosts)
      .filter(([,host])=>!!host.fields['Route clue']).map(([target,host])=>({actor,target,clue:host.fields['Route clue'] as Record<string,unknown>}))));
  return {controllers:own,clues,manifest:view==='truth'?frame.truth.route_manifest:null,
          pressure:view==='truth'?frame.truth.route_pressure:null};
}
