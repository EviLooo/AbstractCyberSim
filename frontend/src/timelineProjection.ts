import type {Frame} from './types';
export type TimelineEntry={tick:number;received?:number;actor:string;host:string;event:string};
export function projectTimeline(frame:Frame,view:string) {
  const tracks:Record<string,TimelineEntry[]>={};
  if(view==='truth') {
    const response=frame.truth.research_truth?.response as {history?:Record<string,unknown>[]} | undefined;
    for(const [kind,title,clock] of [['signal','Defender signals','signal_tick'],['decision','Defender decisions','decision_tick'],['effect','Defender effects','effect_tick']]) {
      tracks[title]=(response?.history??[]).filter(e=>e.type===`research_defender_${kind}`).map(e=>({
        tick:Number(e[clock]),actor:String(e.actor??e.sensor??'Sensor'),host:String(e.host??''),
        event:String(e.action??kind)+(e.outcome?` · ${e.outcome}`:'')}));
    }
  }
  tracks['Observed worker symptoms']=Object.entries(frame.private_views).filter(([a])=>view==='truth'||a===view).flatMap(([actor,data])=>[
    ...(data.beliefs?.events??[]).map(e=>({tick:e.tick,actor,host:e.host,event:e.type.replaceAll('_',' ')})),
    ...(data.research_evidence??[]).filter(e=>e.response).map(e=>({tick:e.observed_tick,received:e.received_tick,
      actor,host:e.host,event:`${e.response} · ${e.origin} · ${e.source}`}))
  ]).sort((a,b)=>a.tick-b.tick);
  return tracks;
}
