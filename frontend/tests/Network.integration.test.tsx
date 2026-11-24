import { act, useState } from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import type cytoscape from 'cytoscape';
import Network from '../src/Network';
import type { Frame, Run } from '../src/types';
import { createWorkbenchFixture, OWN_HOST, OBSERVED_HOST, PEER_HOST, PEER_EVIDENCE } from './fixtures/workbench.mock';

const renderer = vi.hoisted(() => ({ instances: [] as cytoscape.Core[], options: [] as cytoscape.CytoscapeOptions[] }));
// Use the real graph/layout/selection model; replace only its browser canvas.
vi.mock('cytoscape', async importOriginal => {
  const actual = await importOriginal<{ default: typeof cytoscape }>();
  return { default: (options: cytoscape.CytoscapeOptions) => {
    renderer.options.push(options);
    const core = actual.default({ ...options, container: undefined, headless: true, styleEnabled: true });
    vi.spyOn(core, 'fit');
    vi.spyOn(core, 'resize');
    renderer.instances.push(core);
    return core;
  } };
});

beforeEach(() => {
  renderer.instances.length = 0; renderer.options.length = 0;
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
});
afterEach(() => {
  try { cleanup(); for (const core of renderer.instances) expect(core.destroyed()).toBe(true); }
  finally { vi.restoreAllMocks(); vi.unstubAllGlobals(); }
});

function Harness({ frame, run, view = 'truth', mode = 'network' }: { frame: Frame; run: Run; view?: string; mode?: 'network' | 'team' }) {
  const [selected, setSelected] = useState<string | null>(null);
  return <Network frame={frame} run={run} view={view} mode={mode} selected={selected} onSelect={setSelected}/>;
}
function current() { return renderer.instances.at(-1)!; }

test('zoom buttons clamp around the camera center; Fit changes the camera without moving nodes', () => {
  const fixture = createWorkbenchFixture();
  render(<Harness {...fixture}/>);
  act(() => { current().zoom(1); });
  const panBefore = { ...current().pan() };
  fireEvent.click(screen.getByRole('button', { name: 'Zoom in' }));
  expect(current().zoom()).toBeCloseTo(1.25);
  expect(current().pan()).not.toEqual(panBefore);
  expect(screen.getByLabelText('Graph zoom').textContent).toBe('125%');
  fireEvent.click(screen.getByRole('button', { name: 'Zoom out' }));
  expect(current().zoom()).toBeCloseTo(1);
  for (let i = 0; i < 20; i++) fireEvent.click(screen.getByRole('button', { name: 'Zoom in' }));
  expect(current().zoom()).toBe(3);
  expect(screen.getByRole('button', { name: 'Zoom in' }).hasAttribute('disabled')).toBe(true);
  for (let i = 0; i < 40; i++) fireEvent.click(screen.getByRole('button', { name: 'Zoom out' }));
  expect(current().zoom()).toBe(0.05);
  expect(screen.getByRole('button', { name: 'Zoom out' }).hasAttribute('disabled')).toBe(true);
  const before = current().nodes().map(node => ({ id: node.id(), position: { ...node.position() } }));
  fireEvent.click(screen.getByRole('button', { name: 'Fit graph' }));
  expect(current().resize).toHaveBeenCalled();
  expect(current().fit).toHaveBeenCalledWith(undefined, 40);
  expect(current().nodes().map(node => ({ id: node.id(), position: { ...node.position() } }))).toEqual(before);
});

test('hierarchy has coordinator above workers; selection survives a stable frame refresh with its camera', () => {
  const fixture = createWorkbenchFixture();
  const app = render(<Harness {...fixture} mode="team"/>);
  const coordinator = current().getElementById('Coordinator');
  for (const worker of ['Red_0', 'Red_1']) expect(current().getElementById(worker).position('y')).toBeGreaterThan(coordinator.position('y'));
  fireEvent.change(screen.getByRole('combobox', { name: 'Inspect node' }), { target: { value: '0' } });
  expect(current().getElementById('Red_0').selected()).toBe(true);
  act(() => { current().zoom(0.8); current().pan({ x: 42, y: 19 }); current().getElementById('Red_0').position({ x: 40, y: 240 }); });
  const old = current();
  app.rerender(<Harness {...fixture} frame={{ ...fixture.frame, tick: fixture.frame.tick + 1 }} mode="team"/>);
  expect(old.destroyed()).toBe(true);
  expect(current().zoom()).toBeCloseTo(0.8);
  expect(current().pan()).toEqual({ x: 42, y: 19 });
  expect(current().getElementById('Red_0').position()).toEqual({ x: 40, y: 240 });
  expect(current().getElementById('Red_0').selected()).toBe(true);
  fireEvent.click(screen.getByRole('button', { name: 'Clear selection' }));
  expect(current().nodes(':selected').length).toBe(0);
});

test('swarm uses circle initially and preserves moved positions during frame updates', () => {
  const fixture = createWorkbenchFixture();
  const run = { ...fixture.run, architecture: 'swarm' };
  const frame = { ...fixture.frame, communication_topology: [{ sender: 'Red_0', recipient: 'Red_1', active: true, interruption_indices: [] }, { sender: 'Red_1', recipient: 'Red_0', active: true, interruption_indices: [] }] };
  const app = render(<Harness {...fixture} frame={frame} run={run} mode="team"/>);
  expect(renderer.options.at(-1)?.layout?.name).toBe('circle');
  expect(current().getElementById('Coordinator').length).toBe(0);
  act(() => { current().getElementById('Red_0').position({ x: 70, y: 90 }); });
  app.rerender(<Harness {...fixture} run={run} frame={{ ...frame, tick: 5 }} mode="team"/>);
  expect(renderer.options.at(-1)?.layout?.name).toBe('preset');
  expect(current().getElementById('Red_0').position()).toEqual({ x: 70, y: 90 });
});

test('private node picker and Fit use only the projected graph, clearing a hidden selected host', () => {
  const fixture = createWorkbenchFixture();
  const app = render(<Harness {...fixture}/>);
  const elements = current().nodes().filter(node => !node.isParent());
  const peerIndex = elements.map(node => node.id()).indexOf(PEER_HOST);
  fireEvent.change(screen.getByRole('combobox', { name: 'Inspect node' }), { target: { value: String(peerIndex) } });
  expect(current().getElementById(PEER_HOST).selected()).toBe(true);
  app.rerender(<Harness {...fixture} view="Red_0"/>);
  const picker = screen.getByRole('combobox', { name: 'Inspect node' });
  expect(picker.textContent).not.toContain(PEER_HOST);
  expect(picker.textContent).toContain(OWN_HOST);
  expect(picker.textContent).toContain(OBSERVED_HOST);
  expect(document.body.textContent).not.toContain(PEER_EVIDENCE);
  expect(current().getElementById(PEER_HOST).length).toBe(0);
  expect(screen.getByRole('button', { name: 'Clear selection' }).hasAttribute('disabled')).toBe(true);
  fireEvent.click(screen.getByRole('button', { name: 'Fit graph' }));
  expect(current().nodes().filter(node => !node.isParent()).map(node => node.id()).sort()).toEqual([OWN_HOST, OBSERVED_HOST].sort());
});

test('an address-only host never gains its hidden hostname in picker text or option values', () => {
  const fixture = createWorkbenchFixture();
  const frame = structuredClone(fixture.frame);
  frame.private_views.Red_0.native.known.hostname = [];
  render(<Harness {...fixture} frame={frame} view="Red_0"/>);
  const picker = screen.getByRole('combobox', { name: 'Inspect node' });
  expect(picker.outerHTML).not.toContain(OWN_HOST);
  expect(picker.outerHTML).not.toContain(OBSERVED_HOST);
  expect(picker.textContent).toContain('10.0.0.1');
});

test('tap selection and blank-canvas clearing stay synchronized with the accessible picker', () => {
  const fixture = createWorkbenchFixture();
  render(<Harness {...fixture} mode="team"/>);
  act(() => { current().getElementById('Red_0').emit('tap'); });
  expect(screen.getByRole('status').textContent).toContain('Selected: Worker 0');
  expect((screen.getByRole('combobox', { name: 'Inspect node' }) as HTMLSelectElement).value).toBe('0');
  act(() => { current().emit('tap'); });
  expect(current().nodes(':selected').length).toBe(0);
  expect(screen.getByRole('status').textContent).toContain('Choose a node');
});

test('empty private graph disables camera commands and provides a truthful empty state', () => {
  const fixture = createWorkbenchFixture();
  render(<Harness {...fixture} view="unavailable"/>);
  for (const name of ['Zoom in', 'Zoom out', 'Fit graph', 'Clear selection']) expect(screen.getByRole('button', { name }).hasAttribute('disabled')).toBe(true);
  expect(screen.getByText('No nodes are available in this view at this tick.')).toBeTruthy();
});

test('resize updates the canvas without fitting or losing its camera and disconnects on unmount', () => {
  let resize!: () => void;
  const observe = vi.fn(); const disconnect = vi.fn();
  vi.stubGlobal('ResizeObserver', class {
    constructor(callback: () => void) { resize = callback; }
    observe = observe;
    disconnect = disconnect;
  });
  const fixture = createWorkbenchFixture();
  const app = render(<Harness {...fixture}/>);
  expect(observe).toHaveBeenCalled();
  act(() => { current().zoom(0.7); current().pan({ x: 17, y: 29 }); });
  vi.mocked(current().fit).mockClear();
  act(() => { resize(); });
  expect(current().resize).toHaveBeenCalled();
  expect(current().fit).not.toHaveBeenCalled();
  expect(current().zoom()).toBe(0.7);
  expect(current().pan()).toEqual({ x: 17, y: 29 });
  app.unmount();
  expect(disconnect).toHaveBeenCalledTimes(1);
});

test('changing organization architecture resets its layout instead of reusing the previous camera', () => {
  const fixture = createWorkbenchFixture();
  const app = render(<Harness {...fixture} mode="team"/>);
  act(() => { current().pan({ x: 999, y: 999 }); });
  const frame = { ...fixture.frame, communication_topology: [{ sender: 'Red_0', recipient: 'Red_1', active: true, interruption_indices: [] }] };
  app.rerender(<Harness {...fixture} frame={frame} run={{ ...fixture.run, architecture: 'swarm' }} mode="team"/>);
  expect(renderer.options.at(-1)?.layout?.name).toBe('circle');
  expect(current().pan()).not.toEqual({ x: 999, y: 999 });
  expect(current().getElementById('Coordinator').length).toBe(0);
});
