import { useState } from 'react'
import Map, { Layer, Marker, Popup, Source } from 'react-map-gl/maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Pause, Play, RotateCcw } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getAttackMap } from '@/services/api'

const severityColor: Record<string, string> = { critical: '#b94747', high: '#c97929', medium: '#b08a2e', low: '#6fbf95' }
const styleUrl = import.meta.env.VITE_MAP_STYLE_URL || 'https://demotiles.maplibre.org/style.json'

export function LiveThreatMap() {
  const [paused, setPaused] = useState(false)
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['attack-map-threat'],
    queryFn: () => getAttackMap(24, 200),
    refetchInterval: 10_000,
  })

  const attacks = (data?.attacks || []).filter((a) => a.latitude !== null && a.longitude !== null)
  const totalSources = data?.total_unique_sources || 0
  const criticalCount = attacks.filter((a) => a.rule_level >= 13).length
  const highCount = attacks.filter((a) => a.rule_level >= 10 && a.rule_level < 13).length

  const geoData = {
    type: 'FeatureCollection' as const,
    features: attacks.map((a) => ({
      type: 'Feature' as const,
      properties: { severity: a.rule_level >= 13 ? 'critical' : a.rule_level >= 10 ? 'high' : 'medium' },
      geometry: { type: 'LineString' as const, coordinates: [[a.longitude!, a.latitude!], [0, 0]] },
    })),
  }

  if (isLoading) {
    return (
      <section className="flex h-full min-h-[480px] items-center justify-center bg-[#111315]">
        <p className="text-xs text-stone-500">Loading threat map...</p>
      </section>
    )
  }

  if (attacks.length === 0) {
    return (
      <section className="flex h-full min-h-[480px] flex-col items-center justify-center bg-[#111315] gap-3">
        <p className="text-sm text-stone-500">No geolocated attack sources detected</p>
        <p className="text-xs text-stone-600">Attack map will populate when Wazuh alerts contain GeoIP data</p>
      </section>
    )
  }

  return (
    <section className="relative h-full min-h-[480px] overflow-hidden bg-[#111315]">
      <div className="absolute left-5 top-5 z-10"><p className="eyebrow">Global telemetry</p><h2 className="text-base font-semibold text-white">Live attack surface</h2></div>
      <div className="absolute right-5 top-5 z-10 flex gap-1"><button className="icon-button" aria-label="Reset map" onClick={() => setSelectedIdx(null)}><RotateCcw size={15} /></button><button className="icon-button" aria-label={paused ? 'Resume live events' : 'Pause live events'} onClick={() => setPaused(!paused)}>{paused ? <Play size={15} /> : <Pause size={15} />}</button></div>
      <div className="h-full w-full"><Map initialViewState={{ longitude: 8, latitude: 29, zoom: 1.2 }} mapStyle={styleUrl} attributionControl={false} onClick={() => setSelectedIdx(null)}>
        <Source id="flows" type="geojson" data={geoData}><Layer id="flows-line" type="line" paint={{ 'line-color': ['match', ['get', 'severity'], 'critical', '#b94747', 'high', '#c97929', '#b08a2e'], 'line-width': ['match', ['get', 'severity'], 'critical', 3, 2], 'line-opacity': paused ? .2 : .72 }} /></Source>
        {attacks.map((a, i) => {
          const sev = a.rule_level >= 13 ? 'critical' : a.rule_level >= 10 ? 'high' : 'medium'
          return <Marker key={`${a.source_ip}-${i}`} longitude={a.longitude!} latitude={a.latitude!} anchor="center"><button aria-label={`Investigate ${a.source_ip}`} onClick={(event) => { event.stopPropagation(); setSelectedIdx(i) }} className="h-3 w-3 rounded-full border-2 border-[#111315]" style={{ background: severityColor[sev] }} /></Marker>
        })}
        {selectedIdx !== null && attacks[selectedIdx] && (
          <Popup longitude={attacks[selectedIdx].longitude!} latitude={attacks[selectedIdx].latitude!} closeButton={false} closeOnClick={false} offset={12}>
            <div className="min-w-[210px] p-1 text-slate-900">
              <p className="text-xs font-semibold">{attacks[selectedIdx].country || 'Unknown'} · {attacks[selectedIdx].source_ip}</p>
              <p className="mt-1 text-[11px]">{attacks[selectedIdx].rule_description}</p>
              <p className="mt-2 text-[11px] font-medium" style={{ color: severityColor[attacks[selectedIdx].rule_level >= 13 ? 'critical' : attacks[selectedIdx].rule_level >= 10 ? 'high' : 'medium'] }}>
                L{attacks[selectedIdx].rule_level} · {attacks[selectedIdx].count} alerts
              </p>
            </div>
          </Popup>
        )}
      </Map></div>
      <div className="absolute bottom-4 left-5 z-10 flex gap-4 rounded bg-[#191c1f]/95 px-3 py-2 text-[11px] text-slate-300 shadow-lg">
        <span><b className="text-[#b94747]">●</b> Critical {criticalCount}</span>
        <span><b className="text-[#c97929]">●</b> High {highCount}</span>
        <span><b className="text-emerald-400">●</b> Sources {totalSources}</span>
      </div>
    </section>
  )
}
