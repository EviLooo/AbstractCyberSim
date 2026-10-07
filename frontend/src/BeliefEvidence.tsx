import type {Frame} from './types';
import {projectBeliefs} from './beliefProjection';

export default function BeliefEvidence({frame,view}:{frame:Frame|null;view:string}) {
  if (!frame) return null;
  const selected = projectBeliefs(frame,view);
  if (!selected.length) return null;
  return <section className="environment-evidence belief-evidence"><div className="panel-heading"><h2>Evidence age and observable recovery</h2><span>{view==='truth' ? 'Researcher view of private evidence' : 'This worker only'}</span></div><div className="environment-details">
    <p>Stale evidence may still be correct. Reports stay unconfirmed; new evidence preserves history. Access events come from own session status.</p>
    {selected.map(({actor,beliefs})=><details key={actor} open={view!=='truth'}><summary>{actor.replace('Red_','Worker ')} · {beliefs.records.filter(r=>r.stale).length} stale · {beliefs.records.filter(r=>r.conflict).length} conflicting · {beliefs.events.length} access events</summary>
      <div className="belief-table-wrap"><table><thead><tr><th>Observed host / field</th><th>Source</th><th>Observed / received</th><th>Age / status</th></tr></thead><tbody>{beliefs.records.map((r,i)=><tr key={i}><td>{r.host}<small>{r.field}</small></td><td>{r.origin}<small>{r.confirmation}</small></td><td>t{r.observed_tick} / t{r.received_tick}</td><td>{r.age} ticks · {r.stale ? 'STALE' : 'RECENT'}{r.conflict ? ' · CONFLICT' : ''}</td></tr>)}</tbody></table></div>
      <h3>Observable access events</h3>{beliefs.events.length ? <ul>{beliefs.events.map((e,i)=><li key={i}>t{e.tick} · {e.type.replaceAll('_',' ')} · {e.host}</li>)}</ul> : <p>No access loss or recovery observed.</p>}
      <details><summary>Preserved evidence history ({beliefs.history.length})</summary><pre>{JSON.stringify(beliefs.history,null,2)}</pre></details>
    </details>)}
    {view==='truth' && <details><summary>Resolved complexity settings</summary><pre>{JSON.stringify(frame.complexity,null,2)}</pre></details>}
  </div></section>;
}
