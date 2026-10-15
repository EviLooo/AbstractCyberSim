import type {Frame} from './types';
export function projectMission(frame:Frame, view:string) {
  if(view==='truth')return {mode:'truth',progress:frame.score.mission,requirements:null,owned:[]} as const;
  const worker=frame.private_views[view];
  const owned=worker?.native.sessions.filter(s=>s.active&&s.privileged).map(s=>String(s.hostname)) ?? [];
  return {mode:'private',progress:null,requirements:worker?.mission ?? null,owned:[...new Set(owned)]} as const;
}
