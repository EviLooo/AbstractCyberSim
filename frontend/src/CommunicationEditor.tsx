import type { EpisodeConfig } from './types';

type Communication = EpisodeConfig['communication'];
export default function CommunicationEditor({ value, actors, architecture, onChange }: { value: Communication; actors: string[]; architecture: string; onChange: (value: Communication) => void }) {
  const reasoners = [...actors, ...(architecture === 'hierarchy' ? ['Coordinator'] : [])];
  const possible = reasoners.flatMap(sender => reasoners.filter(recipient => recipient !== sender && architecture !== 'independent' && (architecture !== 'hierarchy' || (sender === 'Coordinator') !== (recipient === 'Coordinator'))).map(recipient => ({ sender, recipient })));
  return <details className="communication-settings"><summary>Links, interruptions & capacity</summary>
    <div className="field-pair"><label className="field">Bytes per tick<input type="number" min={256} max={10000000} value={value.bytes_per_tick} onChange={e => onChange({...value, bytes_per_tick:Number(e.target.value)})}/></label><label className="field">Envelopes per tick<input type="number" min={1} max={10000} value={value.envelopes_per_tick} onChange={e => onChange({...value, envelopes_per_tick:Number(e.target.value)})}/></label></div>
    <label className="field">Message TTL<input type="number" min={1} max={1000} value={value.ttl} onChange={e => onChange({...value, ttl:Number(e.target.value)})}/></label>
    <label className="checkbox"><input type="checkbox" checked={value.links !== null} onChange={e => onChange({...value, links:e.target.checked ? possible : null})}/>Use selected directed links</label>
    {value.links !== null && possible.map(link => <label className="checkbox" key={link.sender + link.recipient}><input type="checkbox" checked={value.links?.some(l => l.sender === link.sender && l.recipient === link.recipient)} onChange={e => onChange({...value, links:e.target.checked ? [...(value.links || []), link] : (value.links || []).filter(l => l.sender !== link.sender || l.recipient !== link.recipient)})}/>{link.sender} → {link.recipient}</label>)}
    {value.interruptions.map((window, index) => <fieldset key={index} className="outage-window"><legend>Interruption {index + 1}</legend>
      <div className="field-pair">{(['start_tick','end_tick'] as const).map(field => <label className="field" key={field}>{field === 'start_tick' ? 'Start tick' : 'End tick'}<input aria-label={`Interruption ${index + 1} ${field === 'start_tick' ? 'start' : 'end'} tick`} type="number" min={1} max={10000} value={window[field]} onChange={e => onChange({...value, interruptions:value.interruptions.map((w,i) => i === index ? {...w,[field]:Number(e.target.value)} : w)})}/></label>)}</div>
      {(['sender','recipient'] as const).map(field => <label className="field" key={field}>{field === 'sender' ? 'Sender' : 'Recipient'}<select aria-label={`Interruption ${index + 1} ${field}`} value={window[field] || ''} onChange={e => onChange({...value, interruptions:value.interruptions.map((w,i) => i === index ? {...w,[field]:e.target.value || null} : w)})}><option value="">All</option>{reasoners.map(a => <option key={a}>{a}</option>)}</select></label>)}
      <label className="checkbox"><input type="checkbox" checked={window.bidirectional} onChange={e => onChange({...value, interruptions:value.interruptions.map((w,i) => i === index ? {...w,bidirectional:e.target.checked} : w)})}/>Both directions</label>
      <button className="text-button" onClick={() => onChange({...value, interruptions:value.interruptions.filter((_,i) => i !== index)})}>Remove interruption {index + 1}</button>
    </fieldset>)}
    <button className="secondary" onClick={() => onChange({...value, interruptions:[...value.interruptions,{start_tick:5,end_tick:10,sender:null,recipient:null,bidirectional:true}]})}>Add interruption</button>
    <p className="field-hint">Start and end ticks are included. Messages due on an interrupted link are dropped. Later messages can arrive after the link recovers.</p>
  </details>;
}
