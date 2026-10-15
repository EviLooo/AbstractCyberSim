import type {Frame} from './types';
export function projectDecisions(frame:Frame,view:string) {
  return view==='truth'
    ? {structure:frame.diagnostics?.structure??null,behavior:frame.diagnostics?.behavior??null,decisions:frame.decisions??{}}
    : {structure:null,behavior:null,decisions:frame.decisions?.[view]?{[view]:frame.decisions[view]}:{}};
}
