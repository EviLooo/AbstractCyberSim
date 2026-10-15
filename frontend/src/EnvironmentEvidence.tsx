import type {Frame} from './types';
import {projectTimeline} from './timelineProjection';

export default function EnvironmentEvidence({frame, view}:{frame:Frame|null;view:string}) {
  if (!frame || !['enterprise_cc4','enterprise_cc4_research'].includes(frame.engine_profile??'')) return null;
  return <section className="environment-evidence"><div className="panel-heading"><h2>Environment at tick {frame.tick}</h2><span>Saved simulator state</span></div>
    {frame.engine_profile==='enterprise_cc4_research'&&<div className="environment-timeline"><p>Separate recorded tracks. Observation time and delivery time can differ; symptoms do not disclose a hidden defender decision.</p>{Object.entries(projectTimeline(frame,view)).map(([track,events])=><section key={track}><h3>{track}</h3>{events.length?<div className="timeline-scroll"><table><thead><tr><th>Observed tick</th><th>Delivered tick</th><th>Actor / source</th><th>Host</th><th>Recorded event</th></tr></thead><tbody>{events.map((e,i)=><tr key={i}><td>t{e.tick}</td><td>{e.received===undefined?'—':`t${e.received}`}</td><td>{e.actor}</td><td>{e.host}</td><td>{e.event}</td></tr>)}</tbody></table></div>:<p>No recorded events in this track.</p>}</section>)}</div>}
    {view !== 'truth' ? <p className="field-hint">Select researcher truth to inspect defender signals and network policies.</p> : <div className="environment-details">
      <p>Mission phase {(frame.truth.mission_phase ?? 0) + 1}. Intended policy and actual firewall blocks are separate.</p>
      <details><summary>Intended communication policy</summary><pre>{JSON.stringify(frame.truth.intended_policy,null,2)}</pre></details>
      <details><summary>Actual firewall blocks</summary><pre>{JSON.stringify(frame.truth.blocks,null,2)}</pre></details>
      <details open={!!frame.defender_events?.length}><summary>Defender signals and response decisions ({frame.defender_events?.length ?? 0})</summary><pre>{JSON.stringify(frame.defender_events ?? [],null,2)}</pre></details>
    </div>}
  </section>;
}
