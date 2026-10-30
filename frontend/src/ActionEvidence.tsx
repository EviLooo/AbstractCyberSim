import type { Frame } from './types';

export default function ActionEvidence({ frame, view="truth" }: { frame: Frame | null;view?:string }) {
  const actions = frame?.actions.filter(a=>view==='truth'||a.actor===view) ?? [];
  return <section className="actions-panel"><div className="panel-heading"><h2>Actions at tick {frame?.tick ?? '—'}</h2><span>Recorded proposals and outcomes</span></div>
    <table><thead><tr><th>Worker / tick</th><th>Recorded proposal</th><th>Validation / outcome</th></tr></thead><tbody>{actions.map(a => <tr key={a.actor}>
      <td className="mono">{a.actor}<small>Frame tick {frame?.tick}</small></td>
      <td><strong>{a.proposal.action}</strong><small className="mono">Target: {a.proposal.target || '—'}</small>
        <small>{a.proposal.method??a.proposal.probe??''} {a.proposal.token_ref??''}</small>
        <small>Source session {a.proposal.session ?? 'Not recorded'}</small>
        <p>Recorded reason: {a.proposal.rationale?.trim() ? a.proposal.rationale : 'Not recorded'}</p>
        {a.duration !== undefined && a.proposal.action !== 'Sleep' && <small>Started tick {a.started_tick ?? 'Not recorded'} · {a.duration} ticks · {a.remaining_ticks ?? 'Not recorded'} remaining{a.submitted === false ? ' · continuation' : ''}</small>}
        <details><summary>Native action, checks & changes</summary><p>{a.concrete_action || a.native_action || 'Not recorded'}</p>
          <h3>Local prerequisites</h3>{a.preconditions ? <pre>{JSON.stringify(a.preconditions,null,2)}</pre> : <p>Not recorded</p>}
          <h3>Observed state changes</h3>{a.state_delta ? <pre>{JSON.stringify(a.state_delta,null,2)}</pre> : <p>Not recorded</p>}
        </details>
      </td>
      <td><small>Gateway validation</small><strong>{a.valid === true ? 'Accepted' : a.valid === false ? 'Rejected' : 'Not recorded'}</strong>
        {a.rejection && <p className="error-text">{a.rejection}</p>}
        <small>Recorded execution outcome</small><span className={'outcome ' + a.outcome}>{a.outcome?.trim() ? a.outcome : 'Not recorded'}</span>
        {a.valid === false && <small>Rejected proposal; outcome does not confirm execution.</small>}
      </td>
    </tr>)}{!actions.length && <tr><td colSpan={3} className="empty-cell">{frame ? 'No recorded actions for this view at this tick.' : 'No saved frame loaded.'}</td></tr>}</tbody></table>
    {!!frame?.suppressed_proposals?.filter(p=>view==='truth'||p.actor===view).length && <details className="suppressed-actions"><summary>Proposals deferred by team tool capacity</summary><pre>{JSON.stringify(frame.suppressed_proposals.filter(p=>view==='truth'||p.actor===view),null,2)}</pre></details>}
  </section>;
}
