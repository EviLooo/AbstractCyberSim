import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import type { Frame, Host, Run } from './types';

export default function Network({ frame, run, view, mode, onSelect }: { frame: Frame; run: Run; view: string; mode: 'network' | 'team'; onSelect: (id: string) => void }) {
  const container = useRef<HTMLDivElement>(null);
  const cy = useRef<cytoscape.Core | null>(null);
  const previousKey = useRef('');
  const remembered = useRef<{ zoom: number; pan: cytoscape.Position; positions: Map<string, cytoscape.Position> } | null>(null);
  useEffect(() => {
    if (!container.current) return;
    const layoutKey = `${run.id}:${mode}:${view}`;
    const sameView = previousKey.current === layoutKey;
    const camera = sameView ? remembered.current : null;
    const savedPositions = camera?.positions || new Map<string, cytoscape.Position>();
    const native = frame.private_views[view]?.native;
    const visible = (host: Host) => !native || native.known.hostname.includes(host.id) || host.interfaces.some(i => native.known.ip_address.includes(String(i['IP Address'])));
    const hosts = frame.truth.hosts.filter(visible);
    let elements: cytoscape.ElementDefinition[] = [];
    if (mode === 'network') {
      const zones = frame.truth.subnets.filter(s => hosts.some(h => h.subnet === s.id));
      elements = zones.map(s => ({ data: { id: 'zone-' + s.id, label: view === 'truth' ? `${s.id.toUpperCase()} / ${s.cidr}` : s.cidr }, classes: 'zone' }));
      for (const host of hosts) {
        const sessions = native ? host.sessions.filter(s => s.agent === view) : host.sessions.filter(s => s.agent.startsWith('Red_'));
        const color = sessions.some(s => s.privileged) ? '#a74327' : sessions.length ? '#e9a164' : host.router ? '#72868a' : '#becbc8';
        const label = !native || native.known.hostname.includes(host.id) ? host.id : String(host.interfaces.find(i => native.known.ip_address.includes(String(i['IP Address'])))?.['IP Address'] || 'Observed host');
        const zoneIndex = zones.findIndex(s => s.id === host.subnet);
        const peers = hosts.filter(h => h.subnet === host.subnet && !h.router);
        const index = peers.findIndex(h => h.id === host.id);
        const position = savedPositions.get(host.id) || (host.router ? { x: zoneIndex * 240 + 70, y: 185 } : { x: zoneIndex * 240 + (index % 2) * 140, y: 35 + Math.floor(index / 2) * 100 });
        elements.push({ data: { id: host.id, label: !native && host.target ? label + '\n[target]' : label, parent: 'zone-' + host.subnet, color, target: !native && host.target ? 'TARGET' : '' }, position, classes: host.router ? 'router' : '' });
      }
      const ids = new Set(hosts.map(h => h.id));
      if (!native) elements.push(...frame.truth.edges.filter(e => ids.has(e.source) && ids.has(e.target)).map(e => ({ data: { ...e, label: '' } })));
      // Agent view intentionally does not infer a routing graph from truth.
    } else {
      const actors = Object.keys(frame.private_views);
      const hierarchy = run.architecture === 'hierarchy';
      elements = [...actors, ...(hierarchy ? ['Coordinator'] : [])].map(id => ({ data: { id, label: id === 'Coordinator' ? 'COORDINATOR' : id.replace('Red_', 'WORKER '), color: id === 'Coordinator' ? '#a74327' : '#366661' } }));
      if (hierarchy) actors.forEach(a => elements.push({ data: { id: 'coord-' + a, source: 'Coordinator', target: a, label: String(frame.messages.filter(m => (m.sender === a || m.recipient === a) && m.status === 'delivered').length) } }));
      else if (run.architecture === 'swarm') actors.forEach((a, i) => actors.slice(i + 1).forEach(b => elements.push({ data: { id: a + '-' + b, source: a, target: b, label: String(frame.messages.filter(m => ((m.sender === a && m.recipient === b) || (m.sender === b && m.recipient === a)) && m.status === 'delivered').length) } })));
    }
    cy.current?.destroy();
    const instance = cytoscape({ container: container.current, elements, style: [
      { selector: 'node', style: { 'background-color': 'data(color)', 'label': 'data(label)', 'width': 32, 'height': 32, 'font-size': 14, 'font-family': 'Consolas, monospace', 'color': '#243833', 'text-valign': 'bottom', 'text-margin-y': 9, 'text-wrap': 'wrap', 'border-width': 2, 'border-color': '#fff', 'overlay-opacity': 0 } },
      { selector: 'node.router', style: { 'shape': 'diamond', 'width': 23, 'height': 23 } },
      { selector: 'node.zone', style: { 'background-color': '#eff2ed', 'background-opacity': 0.9, 'border-color': '#d5ddd6', 'border-width': 1, 'shape': 'round-rectangle', 'padding': '30px', 'text-valign': 'top', 'text-halign': 'center', 'text-margin-y': -12, 'font-size': 12, 'color': '#5a6e64' } },
      { selector: 'edge', style: { 'width': 1.4, 'line-color': '#c3cec7', 'curve-style': 'bezier', 'label': 'data(label)', 'font-size': 10, 'color': '#4c6761', 'text-background-color': '#f7f8f3', 'text-background-opacity': 1, 'text-background-padding': '3px' } },
      { selector: 'node:selected', style: { 'border-color': '#b85a37', 'border-width': 4 } }
    ], layout: mode === 'team' ? { name: 'circle', padding: 80 } : { name: 'preset', padding: 25 }, minZoom: 0.25, maxZoom: 3 });
    if (camera) { instance.zoom(camera.zoom); instance.pan(camera.pan); }
    else if (instance.zoom() > 1.2) { instance.zoom(1.2); instance.center(); }
    instance.on('tap', 'node', event => { if (!event.target.hasClass('zone')) onSelect(event.target.id()); });
    cy.current = instance;
    previousKey.current = layoutKey;
    return () => {
      const positions = new Map<string, cytoscape.Position>();
      instance.nodes().forEach(node => { if (!node.isParent()) positions.set(node.id(), { ...node.position() }); });
      remembered.current = { zoom: instance.zoom(), pan: { ...instance.pan() }, positions };
      instance.destroy(); cy.current = null;
    };
  }, [frame, run.id, run.architecture, mode, view, onSelect]);
  return <div className="graph" ref={container} aria-label={mode === 'network' ? 'CybORG network graph' : 'Agent communication graph'}/>;
}
