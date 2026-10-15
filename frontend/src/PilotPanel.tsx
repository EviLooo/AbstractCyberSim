import {useState} from 'react';
import {api,downloadJson} from './api';
type Preparation={job_count:number;team_token_upper_bound:number;provider_request_upper_bound:number;
  mechanism_checklist:Record<string,string[]>;failure_checklist:string[];before_scientific_execution:string[];limitations:string[]};
export default function PilotPanel({spec}:{spec:string}){
  const [report,setReport]=useState<Preparation|null>(null);
  const [error,setError]=useState(''); const [busy,setBusy]=useState(false);
  async function prepare(){setBusy(true);setError('');try{
    setReport(await api('/experiments/prepare-pilot','POST',JSON.parse(spec)));
  }catch(e){setError(String(e));}finally{setBusy(false);}}
  return <details className="editor-panel"><summary>Pilot preparation · starts nothing</summary>
    <p>Check the current research plan’s limits and review checklist before requesting a scientific pilot.</p>
    <button className="secondary" disabled={busy} onClick={prepare}>Prepare checklist without running</button>
    {error&&<p role="alert" className="error-text">{error}</p>}
    {report&&<><p>{report.job_count} planned episodes · {report.team_token_upper_bound.toLocaleString()} maximum team tokens · {report.provider_request_upper_bound.toLocaleString()} maximum requests including repairs</p>
      {Object.entries(report.mechanism_checklist).map(([name,items])=><section key={name}><h3>{name}</h3><ul>{items.map(item=><li key={item}>{item}</li>)}</ul></section>)}
      <h3>Failures to record</h3><ul>{report.failure_checklist.map(item=><li key={item}>{item}</li>)}</ul>
      <h3>Before scientific execution</h3><ul>{report.before_scientific_execution.map(item=><li key={item}>{item}</li>)}</ul>
      {report.limitations.map(item=><p key={item} className="field-hint">{item}</p>)}
      <button className="secondary" onClick={()=>downloadJson(report,'pilot-preparation.json')}>Export preparation</button></>}
  </details>;
}
