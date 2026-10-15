import type {Frame} from './types';
import {projectMission} from './missionProjection';
export default function MissionEvidence({frame,view}:{frame:Frame|null;view:string}) {
  if(!frame || !['enterprise_cc4','enterprise_cc4_research'].includes(frame.engine_profile??''))return null;
  const data=projectMission(frame,view);
  const mission=data.progress;
  return <section className="mission-evidence"><div className="panel-heading"><h2>Mission progress at tick {frame.tick}</h2><span>{view==='truth'?'Engine-confirmed team access':'Private access only'}</span></div>
    {mission && <><div className="mission-summary"><strong>{mission.status.replaceAll('_',' ')}</strong><span>Final hold {mission.hold_ticks} / {mission.required_hold_ticks} ticks</span><span>{mission.deadline_tick===null?'No mission deadline':`Deadline t${mission.deadline_tick} · ${mission.remaining_ticks} ticks remaining`}</span><span>{mission.reset_count} final-hold resets</span></div><progress aria-label="Confirmed mission hold" max={mission.required_hold_ticks} value={mission.hold_ticks}/>
      {mission.failure && <p className="error-text">{mission.failure.reason.replaceAll('_',' ')} at t{mission.failure.tick}{mission.failure.objective?` · ${mission.failure.objective}`:''}</p>}
      <div className="mission-objectives">{mission.objectives.map(o=><article key={o.id}><h3>{o.id} <span>{o.status.replaceAll('_',' ')}</span></h3><p>Targets: {o.targets.join(', ')}</p>{!!o.requires_privileged_hosts.length && <p>Requires active privileged access: {o.requires_privileged_hosts.join(', ')}</p>}<p>Consecutive hold {o.hold_ticks} / {o.required_hold_ticks} · best {o.best_hold_ticks} · resets {o.reset_count}{o.deadline_tick!==null?` · deadline t${o.deadline_tick}`:''}</p>{!!o.missing_targets.length && <p className="field-hint">Missing target access: {o.missing_targets.join(', ')}</p>}{!!o.missing_prerequisites.length && <p className="field-hint">Missing prerequisite access: {o.missing_prerequisites.join(', ')}</p>}</article>)}</div>
      {!!mission.events.length && <details><summary>Mission events this tick ({mission.events.length})</summary><pre>{JSON.stringify(mission.events,null,2)}</pre></details>}
      <p className="field-hint">Counters sample native sessions after each joint tick, including defender effects. Completed stages reset if required access is lost. Durations are configurable simulation controls.</p>
    </>}
    {data.mode==='private' && <div className="mission-objectives"><p>Team progress is unconfirmed in this private view. Only this worker’s active privileged sessions are listed.</p>{data.requirements?.target_names.map(h=><p key={h}>{h} · {data.owned.includes(h)?'owned privileged access':'no own privileged access'}</p>)}<details><summary>Public mission requirements</summary><pre>{JSON.stringify(data.requirements,null,2)}</pre></details></div>}
    {data.mode==='truth' && !mission && <p className="field-hint">This older frame has no saved sustained-mission state.</p>}
  </section>;
}
