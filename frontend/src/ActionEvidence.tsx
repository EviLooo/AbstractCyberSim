import type { Frame } from './types';

export default function ActionEvidence({ frame }: { frame: Frame | null }) {
  return <section className="actions-panel"><div className="panel-heading"><h2>Actions at tick {frame?.tick ?? 0}</h2><span>Actual engine outcomes</span></div>
    <table><thead><tr><th>Worker</th><th>Requested action / target</th><th>Native result</th></tr></thead><tbody>{frame?.actions.map(a => <tr key={a.actor}><td className="mono">{a.actor}</td><td><strong>{a.proposal.action}</strong><small className="mono">{a.proposal.target || '—'}</small><details><summary>Rationale, checks & changes</summary><p>{a.proposal.rationale}</p><p>{a.concrete_action || a.native_action}</p>{a.rejection && <p className="error-text">{a.rejection}</p>}<h3>Local prerequisites</h3>{a.preconditions ? <pre>{JSON.stringify(a.preconditions,null,2)}</pre> : <p>Not recorded in this older run.</p>}<h3>Observed state changes</h3>{a.state_delta ? <pre>{JSON.stringify(a.state_delta,null,2)}</pre> : <p>Not recorded in this older run.</p>}</details></td><td><span className={'outcome ' + a.outcome}>{a.valid ? a.outcome : 'REJECTED'}</span></td></tr>)}{!frame?.actions.length && <tr><td colSpan={3} className="empty-cell">No actions yet. This world is initialized and paused.</td></tr>}</tbody></table>
    {!!frame?.suppressed_proposals?.length && <details className="suppressed-actions"><summary>Proposals deferred by team tool capacity</summary><pre>{JSON.stringify(frame.suppressed_proposals,null,2)}</pre></details>}
  </section>;
}
