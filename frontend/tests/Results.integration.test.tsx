import { act } from 'react';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import App from '../src/App';
import type { Metrics, Run } from '../src/types';
import { createWorkbenchFixture } from './fixtures/workbench.mock';

let originalUrl: string;
let originalState: unknown;
let unexpected: string[];
let comparisonBodies: unknown[];
let rejectComparison: boolean;
let deferredComparison: Promise<Response> | null;
let runs: Record<string, unknown>[];
const metrics: Metrics = { success: true, charged_tokens: 0, attempted_actions: 0, invalid_actions: 0, duplicate_actions: 0, message_delivered: 0, message_dropped: 0, calls: 0, is_llm: false };

beforeEach(() => {
  originalUrl = window.location.href;
  originalState = window.history.state;
  window.history.replaceState(null, '', '/?page=results');
  vi.useFakeTimers();
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  unexpected = []; comparisonBodies = []; rejectComparison = false;
  deferredComparison = null;
  const fixture = createWorkbenchFixture();
  const run = (id: string, name: string): Run => ({ ...fixture.run, id, name, status: 'completed', metrics });
  // JSON boundary variants deliberately include absent/null historical fields;
  // the TypeScript API contract is not broadened or replaced to hide them.
  runs = [{ ...run('b'.repeat(32), 'MOCK success') }, { ...run('c'.repeat(32), 'MOCK failure'), metrics: { ...metrics, success: false, charged_tokens: 12 } },
    { ...run('d'.repeat(32), 'MOCK missing metrics'), metrics: undefined },
    { ...run('e'.repeat(32), 'MOCK missing success'), metrics: { charged_tokens: 5 } },
    { ...run('f'.repeat(32), 'MOCK null fields'), metrics: { success: null, charged_tokens: null } },
    { ...run('1'.repeat(32), 'MOCK missing tokens'), metrics: { success: false } }];
  vi.stubGlobal('fetch', vi.fn<typeof fetch>(async (input, init) => {
    const address = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
    const url = new URL(address, window.location.origin);
    const method = init?.method ?? 'GET';
    const reply = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status });
    if (url.origin === window.location.origin && !url.search) {
      if (method === 'GET' && url.pathname === '/api/runs') return reply(runs);
      if (method === 'GET' && url.pathname === '/api/capabilities') return reply(fixture.capabilities);
      if (method === 'POST' && url.pathname === '/api/configs/validate') return reply(fixture.config);
      if (method === 'POST' && url.pathname === '/api/analysis/compare') {
        comparisonBodies.push(JSON.parse(String(init?.body)));
        if (deferredComparison) return deferredComparison;
        return rejectComparison ? reply({ detail: 'Compare a single profile at a time; action catalogs and metrics differ' }, 409)
          : reply({ excluded: [{ id: runs[1].id, reason: 'MOCK backend exclusion' }], paired_episodes: 0 });
      }
    }
    unexpected.push(`${method} ${url.href}`);
    throw new Error('Unexpected API request');
  }));
});

function holdComparison() {
  let finish!: (response: Response) => void;
  deferredComparison = new Promise<Response>(resolve => { finish = resolve; });
  return async (data: unknown, status = 200) => {
    await act(async () => { finish(new Response(JSON.stringify(data), { status })); });
    deferredComparison = null;
  };
}

function selectPair() {
  fireEvent.click(screen.getByRole('checkbox', { name: 'Compare MOCK success' }));
  fireEvent.click(screen.getByRole('checkbox', { name: 'Compare MOCK failure' }));
}

test('pending comparison locks selection and returns only the requested active context', async () => {
  await mount();
  selectPair();
  const finish = holdComparison();
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Compare selected evaluations' })); });
  const pending = screen.getByRole('button', { name: 'Comparing…' });
  expect(pending.hasAttribute('disabled')).toBe(true);
  expect(pending.getAttribute('aria-busy')).toBe('true');
  expect(screen.getByRole('status').textContent).toContain('Run selections are locked');
  const first = screen.getByRole('checkbox', { name: 'Compare MOCK success' });
  const other = screen.getByRole('checkbox', { name: 'Compare MOCK missing metrics' });
  for (const checkbox of screen.getAllByRole('checkbox')) expect(checkbox.hasAttribute('disabled')).toBe(true);
  fireEvent.click(first); fireEvent.click(other);
  expect((first as HTMLInputElement).checked).toBe(true);
  expect((other as HTMLInputElement).checked).toBe(false);
  expect(comparisonBodies).toEqual([{ run_ids: [runs[0].id, runs[1].id] }]);
  expect(screen.queryByRole('heading', { name: 'Paired analysis' })).toBeNull();
  // An identical polling response is not a new comparison context.
  await act(async () => { await vi.advanceTimersByTimeAsync(1000); });
  await finish({ run_ids: [runs[0].id, runs[1].id], marker: 'MOCK active comparison' });
  expect(screen.getByText(/"MOCK active comparison"/)).toBeTruthy();
  for (const id of [runs[0].id, runs[1].id]) expect(screen.getByText(/"MOCK active comparison"/).textContent).toContain(id);
  expect(first.hasAttribute('disabled')).toBe(false);
  expect(screen.getByRole('button', { name: 'Compare selected evaluations' }).hasAttribute('disabled')).toBe(false);
});

test.each(['navigation', 'metadata', 'removed run'])('discards a pending result invalidated by %s, then permits a fresh comparison', async path => {
  await mount(); selectPair();
  const finish = holdComparison();
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Compare selected evaluations' })); });
  expect(screen.getByRole('button', { name: 'Comparing…' }).hasAttribute('disabled')).toBe(true);
  if (path === 'navigation') {
    fireEvent.click(screen.getByRole('button', { name: 'Saved runs' }));
    fireEvent.click(screen.getByRole('button', { name: 'Compare & export' }));
  } else {
    runs = path === 'metadata' ? runs.map((run, i) => i ? run : { ...run, status: 'interrupted', tick: 99 }) : runs.slice(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(1000); });
  }
  await finish({ marker: 'MOCK stale response' });
  expect(screen.queryByText(/MOCK stale response/)).toBeNull();
  expect(screen.queryByRole('heading', { name: 'Paired analysis' })).toBeNull();
  expect(screen.queryByRole('button', { name: 'Export analysis' })).toBeNull();
  expect(screen.getByRole('button', { name: 'Compare selected evaluations' }).hasAttribute('disabled')).toBe(false);
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Compare selected evaluations' })); });
  expect(screen.getByRole('heading', { name: 'Paired analysis' })).toBeTruthy();
});

test('deferred rejection clears previous output, announces error and unlocks controls', async () => {
  await mount(); selectPair();
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Compare selected evaluations' })); });
  expect(screen.getByRole('heading', { name: 'Paired analysis' })).toBeTruthy();
  const finish = holdComparison();
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Compare selected evaluations' })); });
  expect(screen.queryByRole('heading', { name: 'Paired analysis' })).toBeNull();
  await finish({ detail: 'MOCK deferred rejection' }, 409);
  expect(screen.getByRole('alert').textContent).toContain('MOCK deferred rejection');
  expect(screen.queryByRole('button', { name: 'Export analysis' })).toBeNull();
  expect(screen.getByRole('checkbox', { name: 'Compare MOCK success' }).hasAttribute('disabled')).toBe(false);
  expect(screen.getByRole('button', { name: 'Compare selected evaluations' }).hasAttribute('disabled')).toBe(false);
});

test('an obsolete deferred error does not appear after navigating away and back', async () => {
  await mount(); selectPair();
  const finish = holdComparison();
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Compare selected evaluations' })); });
  fireEvent.click(screen.getByRole('button', { name: 'Saved runs' }));
  fireEvent.click(screen.getByRole('button', { name: 'Compare & export' }));
  await finish({ detail: 'MOCK obsolete error' }, 409);
  expect(screen.queryByRole('alert')).toBeNull();
  expect(screen.queryByRole('heading', { name: 'Paired analysis' })).toBeNull();
  expect(screen.getByRole('button', { name: 'Compare selected evaluations' }).hasAttribute('disabled')).toBe(false);
});

afterEach(() => {
  try { cleanup(); expect(vi.getTimerCount()).toBe(0); expect(unexpected).toEqual([]); }
  finally { vi.clearAllTimers(); vi.useRealTimers(); vi.unstubAllGlobals(); vi.restoreAllMocks(); window.history.replaceState(originalState, '', originalUrl); }
});

async function mount() {
  await act(async () => { render(<App/>); });
  await act(async () => { await vi.advanceTimersByTimeAsync(250); });
}

function row(name: string) {
  const element = screen.getByRole('checkbox', { name: `Compare ${name}` }).closest('tr');
  if (!element) throw new Error('Result row missing');
  return within(element).getAllByRole('cell');
}

test('recorded success, failure, zero and missing/null results remain distinct', async () => {
  await mount();
  expect(row('MOCK success')[3].textContent).toBe('Yes');
  expect(row('MOCK failure')[3].textContent).toBe('No');
  expect(row('MOCK success')[4].textContent).toBe('0');
  expect(row('MOCK failure')[4].textContent).toBe('12');
  for (const name of ['MOCK missing metrics', 'MOCK missing success', 'MOCK null fields']) expect(row(name)[3].textContent).toBe('Not recorded');
  expect(row('MOCK missing success')[4].textContent).toBe('5');
  for (const name of ['MOCK missing metrics', 'MOCK null fields', 'MOCK missing tokens']) expect(row(name)[4].textContent).toBe('Not recorded');
  expect(row('MOCK success')[5].textContent).toBe('0');
  expect(row('MOCK missing metrics')[5].textContent).toBe('Not recorded');
});

test.each(['initializing', 'ready', 'running', 'paused', 'completed', 'stopped', 'errored', 'interrupted'])('preserves authoritative %s status and context without inventing eligibility', async status => {
  runs = [{ ...runs[0], status, purpose: 'exploration', manual_intervention: true, termination_reason: 'MOCK reason', error: 'MOCK recorded error' }];
  await mount();
  expect(row('MOCK success')[2].textContent).toBe(`${status}Termination reason: MOCK reasonRecorded error: MOCK recorded error`);
  expect(row('MOCK success')[1].textContent).toContain('exploration · manual');
  expect(screen.getByRole('checkbox', { name: 'Compare MOCK success' }).hasAttribute('disabled')).toBe(false);
});

test('comparison preserves selected IDs, backend exclusions, exports and clear rejection without stale success', async () => {
  await mount();
  const button = screen.getByRole('button', { name: 'Compare selected evaluations' });
  expect(button.hasAttribute('disabled')).toBe(true);
  const first = screen.getByRole('checkbox', { name: 'Compare MOCK success' });
  const second = screen.getByRole('checkbox', { name: 'Compare MOCK failure' });
  expect(first.closest('label')?.textContent).toBe(' Select MOCK success');
  fireEvent.click(first); fireEvent.click(second);
  expect(button.hasAttribute('disabled')).toBe(false);
  expect(button.getAttribute('aria-describedby')).toBe('comparison-help');
  await act(async () => { fireEvent.click(button); });
  expect(comparisonBodies).toEqual([{ run_ids: [runs[0].id, runs[1].id] }]);
  expect(screen.getByText(/"MOCK backend exclusion"/)).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Export analysis' })).toBeTruthy();
  expect(screen.getByRole('link', { name: 'All metrics CSV' }).getAttribute('href')).toBe('/api/export/metrics.csv');
  fireEvent.click(second);
  expect(screen.queryByRole('heading', { name: 'Paired analysis' })).toBeNull();
  fireEvent.click(second);
  await act(async () => { fireEvent.click(button); });
  expect(screen.getByRole('heading', { name: 'Paired analysis' })).toBeTruthy();
  rejectComparison = true;
  await act(async () => { fireEvent.click(button); });
  expect(screen.getByRole('alert').textContent).toContain('Compare a single profile at a time');
  expect(screen.queryByRole('heading', { name: 'Paired analysis' })).toBeNull();
  expect(screen.queryByRole('button', { name: 'Export analysis' })).toBeNull();
  expect(button.hasAttribute('disabled')).toBe(false);
  expect(comparisonBodies).toHaveLength(3);
  fireEvent.click(screen.getByRole('button', { name: 'Dismiss error' }));
  expect(screen.queryByRole('alert')).toBeNull();
});
