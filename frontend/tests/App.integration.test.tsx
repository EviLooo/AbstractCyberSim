import { StrictMode, act } from 'react';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import type cytoscape from 'cytoscape';
import App from '../src/App';
import {
  createWorkbenchFixture, OBSERVED_HOST, OWN_EVIDENCE, OWN_HOST,
  PEER_EVIDENCE, PEER_HOST, PEER_REPORT, PEER_ZONE, TEST_RUN_ID, TRUTH_ONLY,
} from './fixtures/workbench.mock';

const renderer = vi.hoisted(() => ({
  calls: [] as cytoscape.CytoscapeOptions[],
  instances: [] as { destroy: ReturnType<typeof vi.fn> }[],
}));

// Only the canvas boundary is replaced. App, api.ts, Network and projections run unchanged.
vi.mock('cytoscape', () => ({
  default: (options: cytoscape.CytoscapeOptions) => {
    if (!Array.isArray(options.elements)) throw new Error('Expected explicit graph elements');
    renderer.calls.push(options);
    const elements = options.elements;
    let zoom = 1;
    let pan = { x: 0, y: 0 };
    const nodes = elements.filter(e => !e.data.source).map(e => ({
      id: () => String(e.data.id),
      isParent: () => elements.some(child => child.data.parent === e.data.id),
      position: () => e.position ?? { x: 0, y: 0 },
    }));
    const instance = {
      destroy: vi.fn(),
      zoom: (value?: number) => { if (value !== undefined) zoom = value; return zoom; },
      pan: (value?: { x: number; y: number }) => { if (value !== undefined) pan = value; return pan; },
      center: vi.fn(), nodes: () => nodes, on: vi.fn(),
    };
    renderer.instances.push(instance);
    return instance;
  },
}));

let originalUrl: string;
let originalHistoryState: unknown;
const unexpectedRequests: string[] = [];

beforeEach(() => {
  originalUrl = window.location.href;
  originalHistoryState = window.history.state;
  window.history.replaceState(null, '', `/?run=${TEST_RUN_ID}`);
  renderer.calls.length = 0;
  renderer.instances.length = 0;
  unexpectedRequests.length = 0;
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  vi.useFakeTimers();
});

afterEach(() => {
  try {
    cleanup();
    // Unmount must cancel App's polling/replay/config timers and dispose every graph.
    expect(vi.getTimerCount()).toBe(0);
    for (const instance of renderer.instances) expect(instance.destroy).toHaveBeenCalled();
    expect(unexpectedRequests).toEqual([]);
  } finally {
    vi.clearAllTimers();
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    vi.clearAllMocks();
    renderer.calls.length = 0;
    renderer.instances.length = 0;
    window.history.replaceState(originalHistoryState, '', originalUrl);
  }
});

function graphElements(): cytoscape.ElementDefinition[] {
  const options = renderer.calls.at(-1);
  if (!options || !Array.isArray(options.elements)) throw new Error('No rendered graph snapshot');
  return options.elements;
}

function graphElement(id: string) {
  const element = graphElements().find(e => e.data.id === id);
  if (!element) throw new Error(`Graph element missing: ${id}`);
  return element;
}

function legendContaining(text: string) {
  const legends = document.querySelectorAll('.graph-legend');
  expect(legends).toHaveLength(1);
  const legend = legends.item(0);
  if (!(legend instanceof HTMLElement)) throw new Error('Legend missing');
  const queries = within(legend);
  expect(queries.getByText(text, { exact: true })).toBeTruthy();
  return queries;
}

test('Network/Organization switching preserves the legend and private worker information boundary', async () => {
  const fixture = createWorkbenchFixture();
  const requests: string[] = [];
  const validationBodies: unknown[] = [];
  const reject = (description: string): never => {
    unexpectedRequests.push(description);
    throw new Error(`Unexpected API request: ${description}`);
  };
  const fetchMock = vi.fn<typeof fetch>(async (input, init) => {
    const address = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
    const url = new URL(address, window.location.origin);
    const method = (init?.method ?? (typeof input === 'object' && 'method' in input ? input.method : 'GET')).toUpperCase();
    const description = `${method} ${url.pathname}${url.search}`;
    requests.push(description);
    if (url.origin !== window.location.origin || url.search) return reject(description);
    const reply = (data: unknown) => new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } });
    if (description === 'GET /api/runs') return reply([fixture.run]);
    if (description === 'GET /api/capabilities') return reply(fixture.capabilities);
    if (description === `GET /api/runs/${TEST_RUN_ID}/frame`) return reply(fixture.frame);
    if (description === 'POST /api/configs/validate') {
      validationBodies.push(JSON.parse(String(init?.body)));
      // A fixed contract-shaped response, not a replacement backend validator.
      return reply(fixture.config);
    }
    // Never delegate to real fetch: creation, controls, providers and all other routes fail.
    return reject(description);
  });
  vi.stubGlobal('fetch', fetchMock);

  await act(async () => { render(<StrictMode><App/></StrictMode>); });
  await act(async () => { await vi.advanceTimersByTimeAsync(250); });
  expect(screen.getByRole('heading', { name: fixture.run.name })).toBeTruthy();
  expect(requests).toContain('POST /api/configs/validate');
  expect(screen.queryByRole('alert')).toBeNull();

  const networkLegend = legendContaining('Uncontrolled');
  for (const text of ['User access', 'Privileged access', '◇ Router']) expect(networkLegend.getByText(text, { exact: true })).toBeTruthy();
  expect(screen.queryByText('Active communication', { exact: true })).toBeNull();
  expect(graphElement(PEER_HOST).data.label).toContain(PEER_HOST);
  expect(graphElement(OBSERVED_HOST).data.color).toBe('#a74327');
  expect(document.body.textContent).toContain(PEER_EVIDENCE);

  fireEvent.click(screen.getByRole('button', { name: /^Organization$/ }));
  const teamLegend = legendContaining('Worker');
  for (const text of ['Coordinator', 'Active communication', 'Interrupted communication']) expect(teamLegend.getByText(text, { exact: true })).toBeTruthy();
  expect(screen.queryByText('Uncontrolled', { exact: true })).toBeNull();
  const explanation = teamLegend.getByText('Number = visible delivered messages · — = unavailable in this view', { exact: true });
  expect(explanation.closest('.graph-tip')).toBeNull();
  expect(graphElement('Red_0').data.color).toBe('#366661');
  expect(graphElement('Coordinator').data.color).toBe('#a74327');
  expect(graphElement('Coordinator-to-Red_0').data.label).toBe('1'); // queued message is not counted
  expect(graphElement('Red_1-to-Coordinator').data.label).toBe('3');
  expect(graphElement('Coordinator-to-Red_1').classes).toBe('communication-link interrupted');

  const knowledgeView = screen.getByRole('combobox', { name: 'Knowledge view' });
  fireEvent.change(knowledgeView, { target: { value: 'Red_0' } });
  expect(teamLegend.getByText('Worker', { exact: true })).toBeTruthy();
  expect(graphElement('Coordinator-to-Red_0').data.label).toBe('1');
  for (const link of ['Red_0-to-Coordinator', 'Coordinator-to-Red_1', 'Red_1-to-Coordinator']) expect(graphElement(link).data.label).toBe('—');
  expect(screen.getByText('OWN DELIVERED MESSAGES', { exact: true }).parentElement?.querySelector('strong')?.textContent).toBe('1');
  expect(screen.getByText('OWN CONTROLLED HOSTS', { exact: true }).parentElement?.querySelector('strong')?.textContent).toBe('1');
  expect(document.body.textContent).toContain(OWN_EVIDENCE);
  for (const hidden of [PEER_HOST, PEER_ZONE, PEER_EVIDENCE, PEER_REPORT, TRUTH_ONLY, 'TEST_NOT_DELIVERED_YET']) expect(document.body.textContent).not.toContain(hidden);

  // A known zero must stay different from an unavailable count.
  fireEvent.change(knowledgeView, { target: { value: 'Red_1' } });
  expect(graphElement('Coordinator-to-Red_1').data.label).toBe('0');
  expect(graphElement('Red_1-to-Coordinator').data.label).toBe('—');
  expect(document.body.textContent).toContain(PEER_EVIDENCE);
  expect(document.body.textContent).not.toContain(OWN_EVIDENCE);

  fireEvent.change(knowledgeView, { target: { value: 'Red_0' } });
  fireEvent.click(screen.getByRole('button', { name: /^Network$/ }));
  expect(legendContaining('Uncontrolled').getByText('Privileged access', { exact: true })).toBeTruthy();
  expect(screen.queryByText('Active communication', { exact: true })).toBeNull();
  expect(screen.queryByText('Number = visible delivered messages · — = unavailable in this view', { exact: true })).toBeNull();
  const nodes = graphElements().filter(e => !e.data.source && !String(e.data.id).startsWith('zone-'));
  expect(nodes.map(e => e.data.id).sort()).toEqual([OBSERVED_HOST, OWN_HOST].sort());
  expect(graphElement(OWN_HOST).data.color).toBe('#e9a164');
  expect(graphElement(OBSERVED_HOST).data.color).toBe('#becbc8'); // peer privilege must not color this worker's graph
  expect(graphElement(OBSERVED_HOST).data.target).toBe('');
  const edges = graphElements().filter(e => e.data.source);
  expect(edges).toHaveLength(1);
  expect(edges[0].data).toMatchObject({ source: OWN_HOST, target: OBSERVED_HOST, evidence_id: 'test-own-probe' });
  for (const hidden of [PEER_HOST, PEER_ZONE, PEER_EVIDENCE, PEER_REPORT, 'test-physical-hidden', 'test-physical-observed']) expect(JSON.stringify(graphElements())).not.toContain(hidden);
  for (const hidden of [PEER_HOST, PEER_EVIDENCE, PEER_REPORT, TRUTH_ONLY]) expect(document.body.textContent).not.toContain(hidden);
  expect(new URLSearchParams(window.location.search).get('view')).toBe('Red_0');
  // Assert outside fetch: App catches request errors, including a thrown assertion.
  expect(validationBodies.length).toBeGreaterThan(0);
  for (const body of validationBodies) expect(body).toEqual(fixture.config);
  expect(unexpectedRequests).toEqual([]);
});
