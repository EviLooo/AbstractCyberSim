import {useEffect,useState} from 'react';

type Queue = {id:string;status:string;jobs:{job_id:string;status:string;attempts:{id:string;run_id:string;status:string;reason?:string}[]}[]};

export default function BatchPanel({spec}:{spec:string}) {
  const [queue,setQueue]=useState<Queue|null>(null);
  const [confirmed,setConfirmed]=useState(false);
  const [limit,setLimit]=useState(1);
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  const [queueId,setQueueId]=useState('');
  const [freezeId,setFreezeId]=useState('');
  const [split,setSplit]=useState('test');
  async function request(path:string,method='GET',body?:unknown) {
    const response=await fetch('/api'+path,{method,headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});
    const value=await response.json();
    if(!response.ok)throw new Error(value.detail??'Queue request failed');
    return value;
  }
  async function perform(action:()=>Promise<void>) {
    setBusy(true);setError('');
    try{await action();}catch(e){setError(String(e));}finally{setBusy(false);}
  }
  useEffect(()=>{
    if(!queue||queue.status!=='running')return;
    const timer=setInterval(()=>{request('/batches/'+queue.id).then(setQueue).catch(e=>setError(String(e)));},1000);
    return()=>clearInterval(timer);
  },[queue?.id,queue?.status]);
  return <section className="editor-panel"><div className="panel-heading"><h2>Saved sequential queue</h2><span>Explicit scripted execution</span></div>
    <p>Saving validates the jobs and starts nothing. A stopped episode restarts as a new recorded attempt; replay never resumes native state.</p>
    <label className="field">Frozen study ID (empty for software checks)<input aria-label="Frozen study ID" value={freezeId} onChange={e=>setFreezeId(e.target.value.trim())}/></label>
    <label className="field">Frozen split<select aria-label="Frozen split" value={split} onChange={e=>setSplit(e.target.value)}><option value="development">Development</option><option value="validation">Validation</option><option value="test">Test</option></select></label>
    <button className="secondary" disabled={busy||queue?.status==='running'} onClick={()=>perform(async()=>{setQueue(await request('/batches'+(freezeId?'?freeze_id='+encodeURIComponent(freezeId)+'&split='+split:''),'POST',JSON.parse(spec)));setConfirmed(false);})}>Save queue without running</button>
    <label className="field">Reopen a saved queue<input aria-label="Saved queue ID" value={queueId} onChange={e=>setQueueId(e.target.value.trim())} placeholder="32-character queue ID"/></label>
    <button className="secondary" disabled={busy||queue?.status==='running'||!/^[a-f0-9]{32}$/.test(queueId)} onClick={()=>perform(async()=>{setQueue(await request('/batches/'+queueId));setConfirmed(false);})}>Load saved queue</button>
    {queue&&<><p className="mono">{queue.id} · {queue.status}</p><p>{queue.jobs.filter(j=>j.status==='completed').length}/{queue.jobs.length} jobs completed</p>
      <label className="field">Maximum jobs this execution<input aria-label="Maximum queued jobs" type="number" min={1} max={queue.jobs.length} value={limit} onChange={e=>setLimit(Number(e.target.value))}/></label>
      <label><input type="checkbox" aria-label="Confirm scripted queue execution" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/> Execute these scripted jobs locally. This will advance the simulator.</label>
      <div className="editor-footer"><button className="primary" disabled={busy||!confirmed||queue.status==='running'||queue.status==='completed'} onClick={()=>perform(async()=>{await request('/batches/'+queue.id+'/execute','POST',{confirm_execution:true,max_jobs:limit,technical_retries:0});setQueue({...queue,status:'running'});setConfirmed(false);})}>Execute / resume scheduling</button>
      <button className="secondary" disabled={busy||queue.status!=='running'} onClick={()=>perform(async()=>{await request('/batches/'+queue.id+'/stop','POST');})}>Stop after current boundary</button></div>
      <details><summary>Saved job and attempt records</summary><pre>{JSON.stringify(queue,null,2)}</pre></details></>}
    {error&&<p className="error-text">{error}</p>}<p className="field-hint">Ordinary mission failure is retained. The UI does not retry it or make live model calls. Research studies and model execution need separate authorization and qualification.</p>
  </section>;
}
