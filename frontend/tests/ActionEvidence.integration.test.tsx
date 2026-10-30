import { cleanup, render, screen, within } from '@testing-library/react';
import { afterEach, expect, test } from 'vitest';
import ActionEvidence from '../src/ActionEvidence';
import type { Action, Frame } from '../src/types';
import { createWorkbenchFixture } from './fixtures/workbench.mock';

afterEach(cleanup);

function action(overrides: Partial<Action> = {}): Action {
  return {
    actor: 'Red_0', proposal: { action: 'Probe', target: 'TEST_TARGET', session: 2, rationale: 'TEST_RECORDED_REASON' },
    native_action: 'TEST_NATIVE_ACTION', valid: true, rejection: null, outcome: 'TRUE', ...overrides,
  };
}

function frameWith(...actions: Action[]): Frame {
  return { ...createWorkbenchFixture().frame, actions };
}

test.each(['TRUE', 'FALSE', 'UNKNOWN', 'IN_PROGRESS'])('keeps accepted validation separate from recorded outcome %s', outcome => {
  render(<ActionEvidence frame={frameWith(action({ outcome }))}/>);
  const row = within(screen.getAllByRole('row')[1]);
  expect(row.getByText('Accepted', { exact: true })).toBeTruthy();
  expect(row.getByText(outcome, { exact: true })).toBeTruthy();
  expect(row.getByText('Recorded reason: TEST_RECORDED_REASON')).toBeTruthy();
  expect(row.getByText('Frame tick 4')).toBeTruthy();
  expect(row.getByText('Target: TEST_TARGET')).toBeTruthy();
  expect(row.getByText('Source session 2')).toBeTruthy();
  expect(row.getByText('Native action, checks & changes').parentElement?.hasAttribute('open')).toBe(false);
});

test('shows rejection and its recorded reason without replacing the recorded outcome', () => {
  render(<ActionEvidence frame={frameWith(action({ valid: false, rejection: 'TEST_GATEWAY_REJECTION', outcome: 'FALSE' }))}/>);
  expect(screen.getByText('Rejected', { exact: true })).toBeTruthy();
  expect(screen.getByText('TEST_GATEWAY_REJECTION')).toBeTruthy();
  expect(screen.getByText('FALSE', { exact: true })).toBeTruthy();
  expect(screen.getByText('Rejected proposal; outcome does not confirm execution.')).toBeTruthy();
  expect(screen.queryByText('Accepted', { exact: true })).toBeNull();
});

test.each([undefined, '', '   '])('reports an absent/blank reason without inventing one (%s)', rationale => {
  render(<ActionEvidence frame={frameWith(action({ proposal: { action: 'Sleep', rationale }, outcome: '' }))}/>);
  expect(screen.getByText('Recorded reason: Not recorded')).toBeTruthy();
  expect(screen.getByText('Source session Not recorded')).toBeTruthy();
  const outcome = screen.getByText('Recorded execution outcome').parentElement;
  expect(outcome?.querySelector('.outcome')?.textContent).toBe('Not recorded');
  expect(document.body.textContent).not.toContain('Fallback');
  expect(screen.queryByText('TRUE', { exact: true })).toBeNull();
});

test('private view excludes peer actions, technical details and deferred proposals across view changes', () => {
  const frame = frameWith(action(), action({
    actor: 'Red_1', proposal: { action: 'AttemptAccess', target: 'TEST_PEER_TARGET', rationale: 'TEST_PEER_REASON' },
    native_action: 'TEST_PEER_NATIVE', valid: false, rejection: 'TEST_PEER_REJECTION',
    preconditions: { TEST_PEER_CHECK: false }, state_delta: { secret: 'TEST_PEER_DELTA' },
  }));
  frame.suppressed_proposals = [
    { actor: 'Red_0', proposal: { action: 'Sleep', rationale: 'TEST_OWN_DEFERRED' } },
    { actor: 'Red_1', proposal: { action: 'Sleep', rationale: 'TEST_PEER_DEFERRED' } },
  ];
  const original = structuredClone(frame);
  const { rerender } = render(<ActionEvidence frame={frame} view="truth"/>);
  const hidden = ['Red_1', 'TEST_PEER_TARGET', 'TEST_PEER_REASON', 'TEST_PEER_NATIVE', 'TEST_PEER_REJECTION', 'TEST_PEER_CHECK', 'TEST_PEER_DELTA', 'TEST_PEER_DEFERRED'];
  for (const text of hidden) expect(document.body.textContent).toContain(text);
  rerender(<ActionEvidence frame={frame} view="Red_0"/>);
  for (const text of hidden) expect(document.body.textContent).not.toContain(text);
  expect(document.body.textContent).toContain('TEST_RECORDED_REASON');
  expect(document.body.textContent).toContain('TEST_OWN_DEFERRED');
  rerender(<ActionEvidence frame={frame} view="Red_1"/>);
  expect(document.body.textContent).toContain('TEST_PEER_REASON');
  expect(document.body.textContent).not.toContain('TEST_RECORDED_REASON');
  expect(document.body.textContent).not.toContain('TEST_OWN_DEFERRED');
  expect(frame).toEqual(original);
});

test('empty private view does not disclose whether another worker acted or claim a paused world', () => {
  const { rerender } = render(<ActionEvidence frame={frameWith(action({ actor: 'Red_1' }))} view="Red_0"/>);
  expect(screen.getByText('No recorded actions for this view at this tick.')).toBeTruthy();
  expect(document.body.textContent).not.toContain('Red_1');
  expect(document.body.textContent).not.toContain('paused');
  rerender(<ActionEvidence frame={null}/>);
  expect(screen.getByRole('heading', { name: 'Actions at tick —' })).toBeTruthy();
  expect(screen.getByText('No saved frame loaded.')).toBeTruthy();
});
