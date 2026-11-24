import { useEffect, useMemo, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import type { Frame, Run } from './types';
import { projectNetwork, projectTeam, projectLinkCount } from './projection';

export default function Network({ frame, run, view, mode, selected = null, onSelect }: { frame: Frame; run: Run; view: string; mode: 'network' | 'team'; selected?: string | null; onSelect: (id: string | null) => void }) {
  const container = useRef<HTMLDivElement>(null);
  const cy = useRef<cytoscape.Core | null>(null);
  const [zoom, setZoom] = useState(1);
  const projection = useMemo(() => projectNetwork(frame, view), [frame, view]);
  const actors = Object.keys(frame.private_views).sort();
  const hierarchy = run.architecture === 'hierarchy';
  const choices = mode === 'network'
    ? projection.hosts.map(host => ({ id: host.id, label: host.label.replaceAll('\n', ' · ') }))
    : [...actors, ...(hierarchy ? ['Coordinator'] : [])].map(id => ({ id, label: id === 'Coordinator' ? 'Coordinator' : id.replace('Red_', 'Worker ') }));
  const selectedIndex = choices.findIndex(choice => choice.id === selected);
  const previousKey = useRef('');
  const remembered = useRef<{ zoom: number; pan: cytoscape.Position; positions: Map<string, cytoscape.Position> } | null>(null);
  useEffect(() => {
    if (!container.current) return;
    const hosts = projection.hosts;
    // Discovery may add a zone before an existing zone. Reusing the old
    // absolute positions then overlaps hosts belonging to different parents.
    // Retain the camera only while the displayed node/zone inventory is stable.
    const inventory = mode==='network' ? hosts.map(h=>`${h.id}:${h.subnet}`).sort().join('|') : Object.keys(frame.private_views).sort().join('|');
    const layoutKey = `${run.id}:${run.architecture}:${mode}:${view}:${inventory}`;
    const sameView = previousKey.current === layoutKey;
    const camera = sameView ? remembered.current : null;
    const savedPositions = camera?.positions || new Map<string, cytoscape.Position>();
    let elements: cytoscape.ElementDefinition[] = [];
    if (mode === 'network') {
      const zones = projection.zones;
      const columns = zones.length > 4 ? 3 : zones.length;
      const zoneHeight = Math.max(320,...zones.map(zone=>Math.ceil(hosts.filter(h=>h.subnet===zone.id && !h.router).length / 2)*100 + 90));
      elements = zones.map(s => ({ data: { id: 'zone-' + s.id, label:s.label }, classes: 'zone', selectable: false }));
      for (const host of hosts) {
        const zoneIndex = zones.findIndex(s => s.id === host.subnet);
        const peers = hosts.filter(h => h.subnet === host.subnet && !h.router);
        const index = peers.findIndex(h => h.id === host.id);
        const origin = {x:(zoneIndex % columns)*420,y:Math.floor(zoneIndex / columns)*zoneHeight};
        const position = savedPositions.get(host.id) || (host.router ? { x: origin.x + 90, y: origin.y + zoneHeight - 55 } : { x: origin.x + (index % 2) * 180, y: origin.y + 35 + Math.floor(index / 2) * 100 });
        elements.push({ data: { id: host.id, label: host.target ? host.label + '\n[target]' : host.label, parent: 'zone-' + host.subnet, color:host.color, target:host.target ? 'TARGET' : '' }, position, classes: host.router ? 'router' : '' });
      }
      const ids = new Set(hosts.map(h => h.id));
      elements.push(...projection.edges.filter(e => ids.has(e.source) && ids.has(e.target)).map(e => ({ data: { ...e, label: e.label??'' },classes:[e.evidence_id?'observed-probe':'',e.reported||e.stale?'reported-probe':'',e.failed?'failed-probe':''].join(' ') })));
      // Agent view intentionally does not infer a routing graph from truth.
    } else {
      const actors = Object.keys(frame.private_views).sort();
      const hierarchy = run.architecture === 'hierarchy';
      elements = [...actors, ...(hierarchy ? ['Coordinator'] : [])].map((id, index) => ({ data: { id, label: id === 'Coordinator' ? 'COORDINATOR' : id.replace('Red_', 'WORKER '), color: id === 'Coordinator' ? '#a74327' : '#366661' }, ...(hierarchy ? { position: savedPositions.get(id) || (id === 'Coordinator' ? { x: (actors.length - 1) * 90, y: 0 } : { x: index * 180, y: 200 }) } : savedPositions.has(id) ? { position: savedPositions.get(id) } : {}) }));
      for (const link of projectTeam(frame,run,frame.tick)) elements.push({data:{id:link.sender + '-to-' + link.recipient,source:link.sender,target:link.recipient,label:String(projectLinkCount(frame,view,link.sender,link.recipient)??'—')},classes:link.active ? 'communication-link' : 'communication-link interrupted'});
    }
    cy.current?.destroy();
    const instance = cytoscape({ container: container.current, elements, style: [
      { selector: 'node', style: { 'background-color': 'data(color)', 'label': 'data(label)', 'width': 32, 'height': 32, 'font-size': 14, 'font-family': 'Consolas, monospace', 'color': '#243833', 'text-valign': 'bottom', 'text-margin-y': 9, 'text-wrap': 'wrap', 'text-max-width':'150px', 'border-width': 2, 'border-color': '#fff', 'overlay-opacity': 0 } },
      { selector: 'node.router', style: { 'shape': 'diamond', 'width': 23, 'height': 23 } },
      { selector: 'node.zone', style: { 'background-color': '#eff2ed', 'background-opacity': 0.9, 'border-color': '#d5ddd6', 'border-width': 1, 'shape': 'round-rectangle', 'padding': '30px', 'text-valign': 'top', 'text-halign': 'center', 'text-margin-y': -12, 'font-size': 12, 'color': '#5a6e64' } },
      { selector: 'edge', style: { 'width': 2.2, 'line-color': '#c3cec7', 'curve-style': 'bezier', 'label': 'data(label)', 'font-size': 12, 'color': '#304e45', 'text-background-color': '#f7f8f3', 'text-background-opacity': 1, 'text-background-padding': '3px' } },
      { selector: 'node:selected', style: { 'border-color': '#b85a37', 'border-width': 4 } }
      ,{selector:'edge.communication-link',style:{'target-arrow-shape':'triangle','target-arrow-color':'#8ba49a','control-point-step-size':30}}
      ,{selector:'edge.interrupted',style:{'line-color':'#a74327','target-arrow-color':'#a74327','line-style':'dashed'}}
      ,{selector:'edge.observed-probe',style:{'target-arrow-shape':'triangle','target-arrow-color':'#476c91','line-color':'#476c91'}}
      ,{selector:'edge.reported-probe',style:{'line-style':'dashed'}}
      ,{selector:'edge.failed-probe',style:{'line-color':'#a74327','target-arrow-color':'#a74327'}}
    ], layout: mode === 'team' && !hierarchy && !camera ? { name: 'circle', padding: 50 } : { name: 'preset', padding: 40 }, minZoom: 0.05, maxZoom: 3, boxSelectionEnabled: false });
    if (camera) { instance.zoom(camera.zoom); instance.pan(camera.pan); }
    else if (instance.zoom() > 1.2) { instance.zoom(1.2); instance.center(); }
    instance.on('tap', 'node', event => { if (!event.target.hasClass('zone')) onSelect(event.target.id()); });
    instance.on('tap', event => { if (event.target === instance) onSelect(null); });
    instance.on('zoom', () => setZoom(instance.zoom()));
    setZoom(instance.zoom());
    // Resizing must update the canvas without silently fitting/resetting its camera.
    const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(() => instance.resize());
    observer?.observe(container.current);
    cy.current = instance;
    previousKey.current = layoutKey;
    return () => {
      observer?.disconnect();
      const positions = new Map<string, cytoscape.Position>();
      instance.nodes().forEach(node => { if (!node.isParent()) positions.set(node.id(), { ...node.position() }); });
      remembered.current = { zoom: instance.zoom(), pan: { ...instance.pan() }, positions };
      instance.destroy(); cy.current = null;
    };
  }, [frame, projection, run.id, run.architecture, mode, view, onSelect]);
  useEffect(() => {
    cy.current?.nodes().unselect();
    if (selectedIndex >= 0 && selected) cy.current?.getElementById(selected).select();
    else if (selected) onSelect(null);
  }, [selected, selectedIndex, frame, run.id, run.architecture, mode, view, onSelect]);

  function changeZoom(factor: number) {
    const instance = cy.current;
    if (!instance) return;
    instance.zoom({ level: Math.max(0.05, Math.min(3, instance.zoom() * factor)), renderedPosition: { x: instance.width() / 2, y: instance.height() / 2 } });
  }
  function fitVisible() {
    const instance = cy.current;
    if (!instance) return;
    instance.resize();
    instance.fit(undefined, 40);
    if (instance.zoom() > 1.2) { instance.zoom(1.2); instance.center(); }
    setZoom(instance.zoom());
  }
  return <>
    <div className="graph-tools" role="group" aria-label="Graph controls">
      <div className="graph-camera">
        <button type="button" className="secondary" aria-label="Zoom out" disabled={!choices.length || zoom <= 0.05} onClick={() => changeZoom(1 / 1.25)}>−</button>
        <span className="graph-zoom" aria-label="Graph zoom">{Math.round(zoom * 100)}%</span>
        <button type="button" className="secondary" aria-label="Zoom in" disabled={!choices.length || zoom >= 3} onClick={() => changeZoom(1.25)}>+</button>
        <button type="button" className="secondary" disabled={!choices.length} onClick={fitVisible}>Fit graph</button>
      </div>
      <label className="graph-node-picker">Inspect node<select value={selectedIndex < 0 ? '' : String(selectedIndex)} onChange={event => onSelect(event.target.value === '' ? null : choices[Number(event.target.value)].id)}><option value="">Choose a visible node</option>{choices.map((choice, index) => <option key={choice.id} value={index}>{choice.label}</option>)}</select></label>
      <button type="button" className="secondary" disabled={selectedIndex < 0} onClick={() => onSelect(null)}>Clear selection</button>
    </div>
    <div className="graph-selection" role="status">{selectedIndex >= 0 ? `Selected: ${choices[selectedIndex].label} · details in Inspector` : 'Choose a node in the graph or the list to inspect it.'}</div>
    <div className="graph-stage"><div className="graph" ref={container} aria-label={mode === 'network' ? 'CybORG network graph' : 'Agent communication graph'}/>{!choices.length && <p className="graph-empty">No nodes are available in this view at this tick.</p>}</div>
  </>;
}
