import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import type { Frame, Run } from './types';
import { projectNetwork, projectTeam, projectLinkCount } from './projection';

export default function Network({ frame, run, view, mode, onSelect }: { frame: Frame; run: Run; view: string; mode: 'network' | 'team'; onSelect: (id: string) => void }) {
  const container = useRef<HTMLDivElement>(null);
  const cy = useRef<cytoscape.Core | null>(null);
  const previousKey = useRef('');
  const remembered = useRef<{ zoom: number; pan: cytoscape.Position; positions: Map<string, cytoscape.Position> } | null>(null);
  useEffect(() => {
    if (!container.current) return;
    const projection = projectNetwork(frame,view);
    const hosts = projection.hosts;
    // Discovery may add a zone before an existing zone. Reusing the old
    // absolute positions then overlaps hosts belonging to different parents.
    // Retain the camera only while the displayed node/zone inventory is stable.
    const inventory = mode==='network' ? hosts.map(h=>`${h.id}:${h.subnet}`).sort().join('|') : Object.keys(frame.private_views).join('|');
    const layoutKey = `${run.id}:${mode}:${view}:${inventory}`;
    const sameView = previousKey.current === layoutKey;
    const camera = sameView ? remembered.current : null;
    const savedPositions = camera?.positions || new Map<string, cytoscape.Position>();
    let elements: cytoscape.ElementDefinition[] = [];
    if (mode === 'network') {
      const zones = projection.zones;
      const columns = zones.length > 4 ? 3 : zones.length;
      const zoneHeight = Math.max(320,...zones.map(zone=>Math.ceil(hosts.filter(h=>h.subnet===zone.id && !h.router).length / 2)*100 + 90));
      elements = zones.map(s => ({ data: { id: 'zone-' + s.id, label:s.label }, classes: 'zone' }));
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
      const actors = Object.keys(frame.private_views);
      const hierarchy = run.architecture === 'hierarchy';
      elements = [...actors, ...(hierarchy ? ['Coordinator'] : [])].map(id => ({ data: { id, label: id === 'Coordinator' ? 'COORDINATOR' : id.replace('Red_', 'WORKER '), color: id === 'Coordinator' ? '#a74327' : '#366661' } }));
      for (const link of projectTeam(frame,run,frame.tick)) elements.push({data:{id:link.sender + '-to-' + link.recipient,source:link.sender,target:link.recipient,label:String(projectLinkCount(frame,view,link.sender,link.recipient)??'—')},classes:link.active ? 'communication-link' : 'communication-link interrupted'});
    }
    cy.current?.destroy();
    const instance = cytoscape({ container: container.current, elements, style: [
      { selector: 'node', style: { 'background-color': 'data(color)', 'label': 'data(label)', 'width': 32, 'height': 32, 'font-size': 14, 'font-family': 'Consolas, monospace', 'color': '#243833', 'text-valign': 'bottom', 'text-margin-y': 9, 'text-wrap': 'wrap', 'text-max-width':'150px', 'border-width': 2, 'border-color': '#fff', 'overlay-opacity': 0 } },
      { selector: 'node.router', style: { 'shape': 'diamond', 'width': 23, 'height': 23 } },
      { selector: 'node.zone', style: { 'background-color': '#eff2ed', 'background-opacity': 0.9, 'border-color': '#d5ddd6', 'border-width': 1, 'shape': 'round-rectangle', 'padding': '30px', 'text-valign': 'top', 'text-halign': 'center', 'text-margin-y': -12, 'font-size': 12, 'color': '#5a6e64' } },
      { selector: 'edge', style: { 'width': 1.4, 'line-color': '#c3cec7', 'curve-style': 'bezier', 'label': 'data(label)', 'font-size': 10, 'color': '#4c6761', 'text-background-color': '#f7f8f3', 'text-background-opacity': 1, 'text-background-padding': '3px' } },
      { selector: 'node:selected', style: { 'border-color': '#b85a37', 'border-width': 4 } }
      ,{selector:'edge.communication-link',style:{'target-arrow-shape':'triangle','target-arrow-color':'#8ba49a','control-point-step-size':30}}
      ,{selector:'edge.interrupted',style:{'line-color':'#a74327','target-arrow-color':'#a74327','line-style':'dashed'}}
      ,{selector:'edge.observed-probe',style:{'target-arrow-shape':'triangle','target-arrow-color':'#476c91','line-color':'#476c91'}}
      ,{selector:'edge.reported-probe',style:{'line-style':'dashed'}}
      ,{selector:'edge.failed-probe',style:{'line-color':'#a74327','target-arrow-color':'#a74327'}}
    ], layout: mode === 'team' ? { name: 'circle', padding: 80 } : { name: 'preset', padding: 25 }, minZoom: 0.05, maxZoom: 3 });
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
