import {useEffect,useState} from 'react';

export default function StudyPanel(){
  const [text,setText]=useState(JSON.stringify({name:'Proposed split',purpose:'software_qualification',worlds:[],protocol:{}},null,2));
  const [result,setResult]=useState<unknown>(null);
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  const [studies,setStudies]=useState<{id:string;name:string;purpose:string;worlds:number}[]>([]);
  async function refresh(){const response=await fetch('/api/studies');if(response.ok)setStudies(await response.json());}
  useEffect(()=>{refresh().catch(e=>setError(String(e)));},[]);
  async function submit(){
    setBusy(true);setError('');
    try{
      const response=await fetch('/api/studies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(JSON.parse(text))});
      const value=await response.json();
      if(!response.ok)throw new Error(typeof value.detail==='string'?value.detail:JSON.stringify(value.detail));
      // The archive retains full native worlds. Keep the interactive receipt
      // small enough to inspect without rendering megabytes of privileged state.
      setResult({id:value.id,created_at:value.created_at,payload_hash:value.payload_hash,
        purpose:value.payload.purpose,worlds:value.payload.worlds.map((world:{split:string;causal_world_hash:string})=>
          ({split:world.split,causal_world_hash:world.causal_world_hash}))});
      await refresh();
    }catch(e){setError(String(e));}finally{setBusy(false);}
  }
  return <details className="editor-panel"><summary>Freeze qualified materialized splits</summary>
    <p>Declare existing native-qualified run IDs as development, validation and test worlds. Address changes alone are rejected. Freezing starts no simulation or model. A proposed study additionally needs a predeclared protocol and an authorized pilot reference.</p>
    <label className="field">Split manifest<textarea aria-label="Freeze manifest JSON" className="json-editor" value={text} onChange={e=>setText(e.target.value)}/></label>
    <button className="secondary" disabled={busy} onClick={submit}>Validate and freeze without running</button>
    {error&&<p role="alert" className="error-text">{error}</p>}
    {result!==null&&<pre>{JSON.stringify(result,null,2)}</pre>}
    {studies.map(study=><article key={study.id}><h3>{study.name}</h3><p>{study.purpose} · {study.worlds} frozen worlds</p>
      <a className="secondary" href={'/api/studies/'+study.id+'/export'}>Export frozen source, evidence, CSV and figures</a></article>)}
    <p className="field-hint">Use the returned freeze ID in the queue above. Full workflow and holdout definitions: docs/research/FREEZE_WORKFLOW.md. Model treatments require a local immutable artifact hash; live-provider validation remains separate.</p>
  </details>;
}
