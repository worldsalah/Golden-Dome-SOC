import { useMemo, useState } from 'react'
import { Pause, Play, RotateCcw, SlidersHorizontal } from 'lucide-react'
import { motion } from 'framer-motion'

type Attack = {
  origin: string
  asn: string
  ip: string
  protocol: string
  severity: 'critical' | 'high' | 'medium'
  source: [number, number]
  target: [number, number]
  asset: string
}

const attacks: Attack[] = [
  { origin: 'Bucharest, RO', asn: 'AS8708', ip: '185.220.101.4', protocol: 'RDP', severity: 'critical', source: [26.1, 44.4], target: [-0.1, 51.5], asset: 'EDGE-RDP-01' },
  { origin: 'Singapore, SG', asn: 'AS7473', ip: '103.28.41.17', protocol: 'HTTPS', severity: 'high', source: [103.8, 1.3], target: [-74, 40.7], asset: 'API-GATEWAY-02' },
  { origin: 'São Paulo, BR', asn: 'AS28573', ip: '177.84.11.29', protocol: 'SSH', severity: 'medium', source: [-46.6, -23.5], target: [2.3, 48.8], asset: 'BASTION-01' },
]

const color = { critical: '#b94747', high: '#c97929', medium: '#b08a2e' }
const point = ([lng, lat]: [number, number]) => ({ x: ((lng + 180) / 360) * 100, y: ((90 - lat) / 180) * 100 })

export function EnterpriseAttackMap() {
  const [paused, setPaused] = useState(false)
  const [selected, setSelected] = useState<Attack>(attacks[0])
  const [hours, setHours] = useState('1h')
  const attackPoints = useMemo(() => attacks.map((attack) => ({ attack, from: point(attack.source), to: point(attack.target) })), [])

  return (
    <section className="enterprise-panel relative min-h-[390px] overflow-hidden">
      <div className="flex items-start justify-between border-b border-white/[0.07] px-5 py-4">
        <div><p className="eyebrow">Live telemetry</p><h2 className="text-base font-semibold text-slate-100">Attack activity</h2></div>
        <div className="flex gap-1"><select aria-label="Attack map time range" value={hours} onChange={(event) => setHours(event.target.value)} className="control"><option>1h</option><option>6h</option><option>24h</option></select><button aria-label="Reset map" className="icon-button" onClick={() => setSelected(attacks[0])}><RotateCcw size={15} /></button><button aria-label={paused ? 'Resume animation' : 'Pause animation'} className="icon-button" onClick={() => setPaused(!paused)}>{paused ? <Play size={15} /> : <Pause size={15} />}</button></div>
      </div>
      <div className="relative grid min-h-[334px] grid-cols-1 lg:grid-cols-[1fr_235px]">
        <div className="map-grid relative overflow-hidden p-5" aria-label="Interactive attack activity map">
          <svg viewBox="0 0 100 50" className="h-full min-h-[270px] w-full" role="img" aria-label="Global attack paths">
            <path d="M3 14 L14 9 22 13 27 11 34 15 38 13 44 17 49 15 55 18 60 14 66 16 71 13 78 17 85 15 95 20 97 28 88 31 79 28 73 31 65 28 57 31 49 28 43 32 35 28 29 31 20 27 13 30 6 26Z" fill="none" stroke="rgba(203,213,225,.16)" strokeWidth=".25" />
            <path d="M20 30 L27 34 31 42 27 47 22 42 18 34Z M70 31 L80 34 85 42 82 48 75 44Z" fill="none" stroke="rgba(203,213,225,.16)" strokeWidth=".25" />
            {attackPoints.map(({ attack, from, to }, index) => <g key={attack.ip} onMouseEnter={() => setSelected(attack)} className="cursor-pointer"><path d={`M${from.x} ${from.y / 2} Q${(from.x + to.x) / 2} ${Math.min(from.y, to.y) / 2 - 9} ${to.x} ${to.y / 2}`} fill="none" stroke={color[attack.severity]} strokeWidth={attack.severity === 'critical' ? .55 : .35} opacity=".7" /><circle cx={from.x} cy={from.y / 2} r=".9" fill={color[attack.severity]} /><circle cx={to.x} cy={to.y / 2} r="1.2" fill="#d9e3db" />{!paused && <motion.circle cx={from.x} cy={from.y / 2} r=".8" fill={color[attack.severity]} animate={{ cx: [from.x, to.x], cy: [from.y / 2, to.y / 2] }} transition={{ duration: 2.5 + index, repeat: Infinity, ease: 'linear' }} />}</g>)}
          </svg>
          <div className="absolute bottom-4 left-5 flex gap-4 text-[11px] text-slate-400"><span className="flex items-center gap-1"><i className="h-2 w-2 rounded-full bg-[#b94747]" />Critical</span><span className="flex items-center gap-1"><i className="h-2 w-2 rounded-full bg-[#c97929]" />High</span><span className="flex items-center gap-1"><SlidersHorizontal size={13} />Hover a path</span></div>
        </div>
        <aside className="border-t border-white/[0.07] bg-[#17191c] p-4 lg:border-l lg:border-t-0"><p className="eyebrow">Selected flow</p><p className="mt-2 text-sm font-medium text-slate-100">{selected.origin}</p><p className="mt-1 font-mono text-xs text-slate-400">{selected.ip} · {selected.asn}</p><dl className="mt-6 space-y-4 text-xs"><div><dt>Target asset</dt><dd>{selected.asset}</dd></div><div><dt>Protocol</dt><dd>{selected.protocol}</dd></div><div><dt>Severity</dt><dd className="capitalize" style={{ color: color[selected.severity] }}>{selected.severity}</dd></div><div><dt>Observed</dt><dd>Just now</dd></div></dl></aside>
      </div>
    </section>
  )
}
