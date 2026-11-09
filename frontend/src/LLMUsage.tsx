import type { Frame } from './types';
import { projectSummary } from './projection';

export default function LLMUsage({ frame, view }: { frame: Frame | null; view: string }) {
  const cognition = frame?.cognition;
  const tokens = frame && cognition ? projectSummary(frame, view).tokens : null;
  const researcher = view === 'truth';
  return <div>
    <span>{researcher ? 'TEAM ACCOUNTED TOKENS' : 'OWN ACCOUNTED TOKENS'}</span>
    <strong>{tokens?.toLocaleString() ?? 'Not recorded'}</strong>
    {researcher && <small style={{ display: 'block' }}>LLM calls: {cognition?.calls?.toLocaleString() ?? 'Not recorded'}</small>}
    <details><summary>Usage accounting</summary>
      <p>{researcher ? 'Saved frame team total, including worker, coordinator and repair calls when used.' : 'Selected worker only; team and peer usage are not shown.'}</p>
      <p>Accounted tokens may include budget reservations when measured usage is unknown. A measured/reserved breakdown is not available in this view.</p>
      <p>Not recorded means unavailable, not zero. These values are not monetary cost or provider latency.</p>
    </details>
  </div>;
}
