import { useState } from 'react'
import { Pause, Play, RotateCcw, SlidersHorizontal } from 'lucide-react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { getAttackMap } from '@/services/api'

const color: Record<string, string> = { critical: '#b94747', high: '#c97929', medium: '#b08a2e', low: '#6fbf95' }
const point = ([lng, lat]: [number, number]) => ({ x: ((lng + 180) / 360) * 100, y: ((90 - lat) / 180) * 100 })

export function EnterpriseAttackMap() {
  const [paused, setPaused] = useState(false)
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null)
  const [hours, setHours] = useState('24h')

  const { data, isLoading } = useQuery({
    queryKey: ['attack-map-enterprise', hours],
    queryFn: () => getAttackMap(parseInt(hours) || 24, 200),
    refetchInterval: 10_000,
  })

  const attacks = (data?.attacks || []).filter((a) => a.latitude !== null && a.longitude !== null)

  if (isLoading) {
    return (
      <section className="enterprise-panel relative min-h-[390px] flex items-center justify-center">
        <p className="text-xs text-stone-500">Loading attack telemetry...</p>
      </section>
    )
  }

  if (attacks.length === 0) {
    return (
      <section className="enterprise-panel relative min-h-[390px] flex flex-col items-center justify-center gap-2">
        <p className="text-sm text-stone-500">No geolocated attack sources detected</p>
        <p className="text-xs text-stone-600">Map will populate when Wazuh alerts contain GeoIP data</p>
      </section>
    )
  }

  return (
    <section className="enterprise-panel relative min-h-[390px] overflow-hidden">
      <div className="flex items-start justify-between border-b border-white/[0.07] px-5 py-4">
        <div><p className="eyebrow">Live telemetry</p><h2 className="text-base font-semibold text-slate-100">Attack activity</h2></div>
        <div className="flex gap-1"><select aria-label="Attack map time range" value={hours} onChange={(event) => setHours(event.target.value)} className="control"><option value="1">1h</option><option value="6">6h</option><option value="24">24h</option></select><button aria-label="Reset map" className="icon-button" onClick={() => setSelectedIdx(null)}><RotateCcw size={15} /></button><button aria-label={paused ? 'Resume animation' : 'Pause animation'} className="icon-button" onClick={() => setPaused(!paused)}>{paused ? <Play size={15} /> : <Pause size={15} />}</button></div>
      </div>
      <div className="relative grid min-h-[334px] grid-cols-1 lg:grid-cols-[1fr_235px]">
        <div className="map-grid relative overflow-hidden p-5" aria-label="Interactive attack activity map">
          <svg viewBox="0 0 100 50" className="h-full min-h-[270px] w-full" role="img" aria-label="Global attack paths">
            <path d="M3 14 L14 9 22 13 27 11 34 15 38 13 44 17 49 15 55 18 60 14 66 16 71 13 78 17 85 15 95 20 97 28 88 31 79 28 73 31 65 28 57 31 49 28 43 32 35 28 29 31 20 27 13 30 6 26Z" fill="none" stroke="rgba(203,213,225,.16)" strokeWidth=".25" />
            <path d="M20 30 L27 34 31 42 27 47 22 42 18 34Z M70 31 L80 34 85 42 82 48 75 44Z" fill="none" stroke="rgba(203,213,225,.16)" strokeWidth=".25" />
            {attacks.map((a, index) => {
              const from = point([a.longitude!, a.latitude!])
              const sev = a.rule_level >= 13 ? 'critical' : a.rule_level >= 10 ? 'high' : 'medium'
              return <g key={`${a.source_ip}-${index}`} onMouseEnter={() => setSelectedIdx(index)} className="cursor-pointer">
                <circle cx={from.x} cy={from.y / 2} r=".9" fill={color[sev]} />
                {!paused && <motion.circle cx={from.x} cy={from.y / 2} r=".8" fill={color[sev]} animate={{ opacity: [1, 0.3, 1] }} transition={{ duration: 2.5 + index, repeat: Infinity, ease: 'linear' }} />}
              </g>
            })}
          </svg>
          <div className="absolute bottom-4 left-5 flex gap-4 text-[11px] text-slate-400"><span className="flex items-center gap-1"><i className="h-2 w-2 rounded-full bg-[#b94747]" />Critical</span><span className="flex items-center gap-1"><i className="h-2 w-2 rounded-full bg-[#c97929]" />High</span><span className="flex items-center gap-1"><SlidersHorizontal size={13} />Hover a point</span></div>
        </div>
        <aside className="border-t border-white/[0.07] bg-[#17191c] p-4 lg:border-l lg:border-t-0">
          {selectedIdx !== null && attacks[selectedIdx] ? (
            <>
              <p className="eyebrow">Selected source</p>
              <p className="mt-2 text-sm font-medium text-slate-100">{attacks[selectedIdx].country || 'Unknown'}</p>
              <p className="mt-1 font-mono text-xs text-slate-400">{attacks[selectedIdx].source_ip}</p>
              <dl className="mt-6 space-y-4 text-xs">
                <div><dt>Rule</dt><dd>{attacks[selectedIdx].rule_description}</dd></div>
                <div><dt>Alerts</dt><dd>{attacks[selectedIdx].count}</dd></div>
                <div><dt>Severity</dt><dd className="capitalize" style={{ color: color[attacks[selectedIdx].rule_level >= 13 ? 'critical' : attacks[selectedIdx].rule_level >= 10 ? 'high' : 'medium'] }}>L{attacks[selectedIdx].rule_level}</dd></div>
              </dl>
            </>
          ) : (
            <p className="text-xs text-slate-500">Hover over a point to see details</p>
          )}
        </aside>
      </div>
    </section>
  )
}
