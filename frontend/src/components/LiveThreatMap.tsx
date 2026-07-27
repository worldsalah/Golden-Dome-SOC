import { useMemo, useState } from 'react'
import Map, { Layer, Marker, Popup, Source } from 'react-map-gl/maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Pause, Play, RotateCcw } from 'lucide-react'

type Threat = { id: number; country: string; asn: string; ip: string; protocol: string; severity: 'critical' | 'high' | 'medium'; source: [number, number]; target: [number, number]; asset: string; mitre: string }

const threats: Threat[] = [
  { id: 1, country: 'Romania', asn: 'AS8708', ip: '185.220.101.4', protocol: 'RDP', severity: 'critical', source: [26.1, 44.4], target: [-0.1, 51.5], asset: 'EDGE-RDP-01', mitre: 'T1110' },
  { id: 2, country: 'Singapore', asn: 'AS7473', ip: '103.8, 1.3', protocol: 'HTTPS', severity: 'high', source: [103.8, 1.3], target: [-74, 40.7], asset: 'API-GATEWAY-02', mitre: 'T1190' },
  { id: 3, country: 'Brazil', asn: 'AS28573', ip: '177.84.11.29', protocol: 'SSH', severity: 'medium', source: [-46.6, -23.5], target: [2.3, 48.8], asset: 'BASTION-01', mitre: 'T1021' },
]

const severityColor = { critical: '#b94747', high: '#c97929', medium: '#b08a2e' }
const styleUrl = import.meta.env.VITE_MAP_STYLE_URL || 'https://demotiles.maplibre.org/style.json'

export function LiveThreatMap() {
  const [paused, setPaused] = useState(false)
  const [selected, setSelected] = useState<Threat | null>(threats[0])
  const data = useMemo(() => ({ type: 'FeatureCollection' as const, features: threats.map((threat) => ({ type: 'Feature' as const, properties: { severity: threat.severity }, geometry: { type: 'LineString' as const, coordinates: [threat.source, threat.target] } })) }), [])
  return (
    <section className="relative h-full min-h-[480px] overflow-hidden bg-[#111315]">
      <div className="absolute left-5 top-5 z-10"><p className="eyebrow">Global telemetry</p><h2 className="text-base font-semibold text-white">Live attack surface</h2></div>
      <div className="absolute right-5 top-5 z-10 flex gap-1"><button className="icon-button" aria-label="Reset map" onClick={() => setSelected(threats[0])}><RotateCcw size={15} /></button><button className="icon-button" aria-label={paused ? 'Resume live events' : 'Pause live events'} onClick={() => setPaused(!paused)}>{paused ? <Play size={15} /> : <Pause size={15} />}</button></div>
      <div className="h-full w-full"><Map initialViewState={{ longitude: 8, latitude: 29, zoom: 1.2 }} mapStyle={styleUrl} attributionControl={false} onClick={() => setSelected(null)}>
        <Source id="flows" type="geojson" data={data}><Layer id="flows-line" type="line" paint={{ 'line-color': ['match', ['get', 'severity'], 'critical', '#b94747', 'high', '#c97929', '#b08a2e'], 'line-width': ['match', ['get', 'severity'], 'critical', 3, 2], 'line-opacity': paused ? .2 : .72 }} /></Source>
        {threats.map((threat) => <Marker key={threat.id} longitude={threat.source[0]} latitude={threat.source[1]} anchor="center"><button aria-label={`Investigate ${threat.ip}`} onClick={(event) => { event.stopPropagation(); setSelected(threat) }} className="h-3 w-3 rounded-full border-2 border-[#111315]" style={{ background: severityColor[threat.severity] }} /></Marker>)}
        {threats.map((threat) => <Marker key={`target-${threat.id}`} longitude={threat.target[0]} latitude={threat.target[1]} anchor="center"><span className="block h-3 w-3 rounded-full border-2 border-[#111315] bg-emerald-400" /></Marker>)}
        {selected && <Popup longitude={selected.source[0]} latitude={selected.source[1]} closeButton={false} closeOnClick={false} offset={12}><div className="min-w-[210px] p-1 text-slate-900"><p className="text-xs font-semibold">{selected.country} · {selected.ip}</p><p className="mt-1 text-[11px]">{selected.asn} · {selected.protocol} → {selected.asset}</p><p className="mt-2 text-[11px] font-medium" style={{ color: severityColor[selected.severity] }}>{selected.severity.toUpperCase()} · {selected.mitre}</p></div></Popup>}
      </Map></div>
      <div className="absolute bottom-4 left-5 z-10 flex gap-4 rounded bg-[#191c1f]/95 px-3 py-2 text-[11px] text-slate-300 shadow-lg"><span><b className="text-[#b94747]">●</b> Critical 4</span><span><b className="text-[#c97929]">●</b> High 11</span><span><b className="text-emerald-400">●</b> Protected assets 28</span></div>
    </section>
  )
}
