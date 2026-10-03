export type ReplayLocation = { page: 'laboratory' | 'experiments' | 'runs' | 'results'; run: string | null; tick: number | null; mode: 'network' | 'team'; view: string; selection: string | null };
export function readLocation(search: string): ReplayLocation {
  const p = new URLSearchParams(search);
  const run = /^[a-f0-9]{32}$/.test(p.get('run') || '') ? p.get('run') : null;
  const tick = p.get('tick');
  const page = p.get('page');
  const view = p.get('view') || 'truth';
  const selection = p.get('selection');
  return {page:page === 'experiments' || page === 'runs' || page === 'results' ? page : 'laboratory', run, tick:run && tick !== null && /^\d+$/.test(tick) && Number(tick) <= 10000 ? Number(tick) : null, mode:p.get('mode') === 'team' ? 'team' : 'network', view:/^Red_[0-7]$/.test(view) ? view : 'truth', selection:selection && /^[\w.-]{1,100}$/.test(selection) ? selection : null};
}
export function writeLocation(state: ReplayLocation): string {
  const p = new URLSearchParams();
  if (state.page !== 'laboratory') p.set('page',state.page);
  if (state.run) {
    p.set('run',state.run);
    if (state.tick !== null) p.set('tick',String(state.tick));
    if (state.mode === 'team') p.set('mode','team');
    if (state.view !== 'truth') p.set('view',state.view);
    if (state.selection) p.set('selection',state.selection);
  }
  return p.size ? '?' + p.toString() : '';
}
