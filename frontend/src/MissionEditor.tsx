import type {EpisodeConfig} from './types';
type Settings=NonNullable<EpisodeConfig['scenario']['mission']>;
type Bounds={minimum?:number;maximum?:number};
export default function MissionEditor({value,targets,hosts,bounds,onChange}:{value:Settings|null;targets:string[];hosts:string[];bounds:{hold?:Bounds;deadline?:Bounds};onChange:(v:Settings|null)=>void}) {
  const current=value ?? {hold_ticks:5,deadline_tick:null,objectives:[]};
  const edit=(index:number,patch:Partial<Settings['objectives'][number]>)=>onChange({...current,objectives:current.objectives.map((o,i)=>i===index?{...o,...patch}:o)});
  const parse=(s:string)=>s.split(',').map(h=>h.trim()).filter(Boolean);
  return <details className="communication-settings"><summary>Mission duration and objectives</summary>
    <label className="field">Success requirement<select value={value?'sustained':'instant'} onChange={e=>onChange(e.target.value==='instant'?null:current)}><option value="instant">Immediate privileged access</option><option value="sustained">Sustained access and deadlines</option></select></label>
    {value && <><label className="field">Final simultaneous hold (ticks)<input type="number" min={bounds.hold?.minimum ?? 1} max={bounds.hold?.maximum ?? 1000} value={current.hold_ticks} onChange={e=>onChange({...current,hold_ticks:Number(e.target.value)})}/></label>
      <label className="field">Mission deadline (tick, optional)<input type="number" min={bounds.deadline?.minimum ?? 1} max={bounds.deadline?.maximum ?? 10000} value={current.deadline_tick ?? ''} placeholder="Episode tick limit" onChange={e=>onChange({...current,deadline_tick:e.target.value===''?null:Number(e.target.value)})}/></label>
      <p className="field-hint">All named targets must stay privileged together. A sampled access loss resets the hold; defenders keep acting. Deadlines include their final tick.</p>
      <details><summary>Physical objective stages ({current.objectives.length || 'one default group'})</summary>
        <p className="field-hint">Stage targets must cover exactly the mission targets. Prerequisites mean current privileged access on those hosts; report text never satisfies them. Stages do not unlock attack actions.</p>
        <datalist id="mission-hosts">{hosts.map(h=><option key={h} value={h}/>)}</datalist>
        {current.objectives.map((o,i)=><fieldset className="outage-window" key={i}><legend>Objective {i+1}</legend>
          <label className="field">Objective ID<input value={o.id} onChange={e=>edit(i,{id:e.target.value})}/></label>
          <label className="field">Objective targets<input list="mission-hosts" value={o.targets.join(', ')} onChange={e=>edit(i,{targets:parse(e.target.value)})}/></label>
          <label className="field">Required privileged hosts<input list="mission-hosts" value={o.requires_privileged_hosts.join(', ')} onChange={e=>edit(i,{requires_privileged_hosts:parse(e.target.value)})}/></label>
          <label className="field">Objective hold (ticks)<input type="number" min={bounds.hold?.minimum ?? 1} max={bounds.hold?.maximum ?? 1000} value={o.hold_ticks} onChange={e=>edit(i,{hold_ticks:Number(e.target.value)})}/></label>
          <label className="field">Objective deadline (tick, optional)<input type="number" min="1" max={bounds.deadline?.maximum ?? 10000} value={o.deadline_tick ?? ''} onChange={e=>edit(i,{deadline_tick:e.target.value===''?null:Number(e.target.value)})}/></label>
          <button className="text-button" onClick={()=>onChange({...current,objectives:current.objectives.filter((_,n)=>n!==i)})}>Remove objective</button>
        </fieldset>)}
        <button className="text-button" disabled={current.objectives.length>=16} onClick={()=>onChange({...current,objectives:[...current.objectives,{id:`objective_${current.objectives.length+1}`,targets:targets.slice(),requires_privileged_hosts:[],hold_ticks:1,deadline_tick:null}]})}>Add objective stage</button>
      </details>
    </>}
  </details>;
}
