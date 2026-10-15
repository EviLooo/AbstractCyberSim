import type {Frame} from './types';

export function projectBeliefs(frame:Frame,view:string) {
  const selected = view === 'truth' ? Object.entries(frame.private_views) : Object.entries(frame.private_views).filter(([actor])=>actor===view);
  return selected.filter(([,state])=>state.beliefs).map(([actor,state])=>({actor,beliefs:state.beliefs!}));
}
