import type {Frame} from './types';
export default function ResearchEvidence({frame,view}:{frame:Frame|null;view:string}) {
  if(frame?.engine_profile!=='enterprise_cc4_research')return null;
  const workers=Object.entries(frame.private_views).filter(([a])=>view==='truth'||a===view);
  return <section className="mission-evidence"><div className="panel-heading"><h2>Investigation evidence at tick {frame.tick}</h2><span>{view==='truth'?'Researcher inspection of private records':'Delivered evidence only'}</span></div>
    <p className="field-hint">A note is a claim. A probe is a source-specific observation at its recorded time. Neither reveals hidden token validity or a future response.</p>
    {workers.map(([actor,data])=><article key={actor}><h3>{actor} · access attempts {data.native.access_resources?.reserved??0}/{data.native.access_resources?.limit??'—'}</h3><div className="decision-options"><table><thead><tr><th>Host / source</th><th>Evidence</th><th>Observed → delivered</th><th>Origin / age</th></tr></thead><tbody>{data.research_evidence?.slice(-18).map((r,i)=><tr key={i}><td>{r.host}<br/><small>{r.source_host??'Local artifact'}</small></td><td>{r.response??r.text??r.kind}<br/>{r.token_ref&&<small>Opaque reference {r.token_ref}<br/>Claimed scope: {r.claimed_scope??'unspecified'}</small>}</td><td>t{r.observed_tick} → t{r.received_tick}</td><td>{r.origin}<br/>{r.age} ticks · {r.stale?'stale':'recent'}<br/><small>{r.source}</small></td></tr>)}</tbody></table></div>{!data.research_evidence?.length&&<p>No diagnostic or local artifact evidence delivered yet.</p>}<details><summary>Public action manual and costs</summary><pre>{JSON.stringify(data.native.catalog,null,2)}</pre></details></article>)}
    {view==='truth'&&<details><summary>Privileged defensive response and attempt history</summary><pre>{JSON.stringify({defender_events:frame.defender_events,research:frame.truth.research_truth},null,2)}</pre></details>}
  </section>;
}
