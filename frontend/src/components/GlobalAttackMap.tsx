import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

type City = { name: string; lon: number; lat: number }
type Severity = 'critical' | 'high' | 'medium'

type LiveAttack = {
  key: number
  from: City
  to: City
  ip: string
  vector: string
  severity: Severity
  travel: number
  path: string
  samples: { x: number[]; y: number[] }
  x1: number
  y1: number
  x2: number
  y2: number
}

const sources: City[] = [
  { name: 'Moscow', lon: 37.6, lat: 55.75 },
  { name: 'Beijing', lon: 116.4, lat: 39.9 },
  { name: 'Tehran', lon: 51.4, lat: 35.7 },
  { name: 'Bucharest', lon: 26.1, lat: 44.4 },
  { name: 'Lagos', lon: 3.4, lat: 6.45 },
  { name: 'São Paulo', lon: -46.6, lat: -23.5 },
  { name: 'Karachi', lon: 67.0, lat: 24.86 },
  { name: 'Kyiv', lon: 30.5, lat: 50.45 },
  { name: 'Jakarta', lon: 106.85, lat: -6.2 },
  { name: 'Mexico City', lon: -99.1, lat: 19.4 },
  { name: 'Cairo', lon: 31.24, lat: 30.04 },
  { name: 'Manila', lon: 120.98, lat: 14.6 },
  { name: 'Hanoi', lon: 105.85, lat: 21.03 },
  { name: 'Minsk', lon: 27.56, lat: 53.9 },
  { name: 'Pyongyang', lon: 125.75, lat: 39.03 },
  { name: 'Shenzhen', lon: 114.05, lat: 22.55 },
]

const targets: City[] = [
  { name: 'London', lon: -0.1, lat: 51.5 },
  { name: 'New York', lon: -74.0, lat: 40.7 },
  { name: 'Frankfurt', lon: 8.68, lat: 50.1 },
  { name: 'Paris', lon: 2.35, lat: 48.85 },
  { name: 'Virginia', lon: -77.4, lat: 38.9 },
  { name: 'Amsterdam', lon: 4.9, lat: 52.37 },
  { name: 'Tokyo', lon: 139.7, lat: 35.68 },
  { name: 'Sydney', lon: 151.2, lat: -33.87 },
  { name: 'Dubai', lon: 55.3, lat: 25.27 },
  { name: 'Toronto', lon: -79.38, lat: 43.65 },
  { name: 'Seoul', lon: 126.98, lat: 37.57 },
  { name: 'Stockholm', lon: 18.07, lat: 59.33 },
]

const vectors: [string, Severity][] = [
  ['Ransomware C2 beacon', 'critical'],
  ['Zero-day exploitation', 'critical'],
  ['RDP brute force', 'critical'],
  ['Data exfiltration', 'critical'],
  ['Credential stuffing', 'high'],
  ['SQL injection', 'high'],
  ['Phishing infrastructure', 'high'],
  ['Malware distribution', 'high'],
  ['DDoS amplification', 'medium'],
  ['Port scanning sweep', 'medium'],
  ['Bot traffic surge', 'medium'],
  ['SSH anomaly', 'medium'],
]

const severityColor: Record<Severity, string> = {
  critical: '#e05252',
  high: '#e08a45',
  medium: '#d4b05e',
}

const W = 1000
const H = 500
const LINGER = 1.6

const rand = (min: number, max: number) => Math.random() * (max - min) + min
const pick = <T,>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)]

function project(lon: number, lat: number): [number, number] {
  return [((lon + 180) / 360) * W, ((90 - lat) / 180) * H]
}

function randomIp() {
  return `${Math.floor(rand(2, 223))}.${Math.floor(rand(0, 255))}.${Math.floor(rand(0, 255))}.${Math.floor(rand(1, 254))}`
}

let attackCounter = 0

function makeAttack(): LiveAttack {
  const from = pick(sources)
  const to = pick(targets)
  const [x1, y1] = project(from.lon, from.lat)
  const [x2, y2] = project(to.lon, to.lat)
  const [vector, severity] = pick(vectors)
  // Arc control point — height scales with distance, with slight random wobble
  const mx = (x1 + x2) / 2 + rand(-30, 30)
  const my = Math.min(y1, y2) - Math.max(30, Math.abs(x2 - x1) * rand(0.14, 0.3))
  // Sample the quadratic bezier for the packet keyframes
  const N = 28
  const sx: number[] = []
  const sy: number[] = []
  for (let i = 0; i <= N; i++) {
    const t = i / N
    const inv = 1 - t
    sx.push(inv * inv * x1 + 2 * inv * t * mx + t * t * x2)
    sy.push(inv * inv * y1 + 2 * inv * t * my + t * t * y2)
  }
  return {
    key: ++attackCounter,
    from,
    to,
    ip: randomIp(),
    vector,
    severity,
    travel: rand(2.2, 4.2),
    path: `M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`,
    samples: { x: sx, y: sy },
    x1,
    y1,
    x2,
    y2,
  }
}

export function GlobalAttackMap() {
  const [attacks, setAttacks] = useState<LiveAttack[]>([])
  const [latest, setLatest] = useState<LiveAttack | null>(null)
  const [total, setTotal] = useState(0)
  const timers = useRef<ReturnType<typeof setTimeout>[]>([])

  useEffect(() => {
    let alive = true
    function spawn() {
      if (!alive) return
      const attack = makeAttack()
      setAttacks((prev) => [...prev.slice(-8), attack])
      setLatest(attack)
      setTotal((t) => t + 1)
      // Retire the attack after its full lifecycle
      timers.current.push(
        setTimeout(() => {
          if (alive) setAttacks((prev) => prev.filter((a) => a.key !== attack.key))
        }, (attack.travel + LINGER) * 1000),
      )
      // Schedule the next strike at a random cadence
      timers.current.push(setTimeout(spawn, rand(500, 1600)))
    }
    // Opening salvo — a few staggered attacks so the map is instantly alive
    for (let i = 0; i < 4; i++) timers.current.push(setTimeout(spawn, i * 420))
    return () => {
      alive = false
      timers.current.forEach(clearTimeout)
      timers.current = []
    }
  }, [])

  return (
    <div className="relative h-full w-full">
      <svg viewBox={`0 0 ${W} ${H}`} className="h-full w-full" aria-label="Live global attack map" role="img">
        <defs>
          <linearGradient id="mapFade" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#0d0f0f" stopOpacity=".85" />
            <stop offset=".18" stopColor="#0d0f0f" stopOpacity="0" />
            <stop offset=".85" stopColor="#0d0f0f" stopOpacity="0" />
            <stop offset="1" stopColor="#0d0f0f" stopOpacity=".9" />
          </linearGradient>
          <filter id="mapTone">
            <feColorMatrix type="saturate" values="0.28" />
            <feComponentTransfer>
              <feFuncR type="linear" slope="0.62" intercept="0.015" />
              <feFuncG type="linear" slope="0.60" intercept="0.013" />
              <feFuncB type="linear" slope="0.52" intercept="0.010" />
            </feComponentTransfer>
          </filter>
          <filter id="glow" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="2.6" result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="hardGlow" x="-150%" y="-150%" width="400%" height="400%">
            <feGaussianBlur stdDeviation="5" result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        <image href="/textures/earth.jpg" x="0" y="0" width={W} height={H} preserveAspectRatio="none" filter="url(#mapTone)" />
        <rect x="0" y="0" width={W} height={H} fill="url(#mapFade)" />

        <g stroke="#e8e2d9" strokeOpacity=".05" strokeWidth="1">
          {[...Array(11)].map((_, i) => <line key={`v${i}`} x1={(i + 1) * (W / 12)} y1="0" x2={(i + 1) * (W / 12)} y2={H} />)}
          {[...Array(5)].map((_, i) => <line key={`h${i}`} x1="0" y1={(i + 1) * (H / 6)} x2={W} y2={(i + 1) * (H / 6)} />)}
        </g>

        {/* Defended hubs — always-on subtle emerald presence */}
        {targets.map((c) => {
          const [x, y] = project(c.lon, c.lat)
          return <circle key={c.name} cx={x} cy={y} r="2" fill="#6fbf95" opacity=".45" />
        })}

        <AnimatePresence>
          {attacks.map((a) => {
            const color = severityColor[a.severity]
            return (
              <motion.g key={a.key} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, transition: { duration: 0.8 } }}>
                {/* Arc draws itself in as the packet flies */}
                <motion.path
                  d={a.path}
                  fill="none"
                  stroke={color}
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  filter="url(#glow)"
                  initial={{ pathLength: 0, opacity: 0.9 }}
                  animate={{ pathLength: 1, opacity: [0.9, 0.9, 0.25] }}
                  transition={{ pathLength: { duration: a.travel, ease: 'easeInOut' }, opacity: { duration: a.travel + LINGER, times: [0, 0.7, 1] } }}
                />
                {/* Packet racing along the arc */}
                <motion.circle
                  r="3.2"
                  fill="#fff"
                  filter="url(#hardGlow)"
                  initial={{ cx: a.x1, cy: a.y1 }}
                  animate={{ cx: a.samples.x, cy: a.samples.y, opacity: [1, 1, 0] }}
                  transition={{ cx: { duration: a.travel, ease: 'easeInOut' }, cy: { duration: a.travel, ease: 'easeInOut' }, opacity: { duration: a.travel + 0.3, times: [0, 0.96, 1] } }}
                />
                {/* Launch pulse at the source */}
                <circle cx={a.x1} cy={a.y1} r="2.8" fill={color} />
                <motion.circle
                  cx={a.x1}
                  cy={a.y1}
                  fill="none"
                  stroke={color}
                  strokeWidth="1.2"
                  initial={{ r: 3, opacity: 0.8 }}
                  animate={{ r: 16, opacity: 0 }}
                  transition={{ duration: 1.4, ease: 'easeOut' }}
                />
                {/* Impact shockwave — double ring + flash on arrival */}
                <motion.circle
                  cx={a.x2}
                  cy={a.y2}
                  fill={color}
                  filter="url(#hardGlow)"
                  initial={{ r: 0, opacity: 0 }}
                  animate={{ r: [0, 5.5, 3], opacity: [0, 1, 0.85] }}
                  transition={{ delay: a.travel - 0.1, duration: 0.5 }}
                />
                <motion.circle
                  cx={a.x2}
                  cy={a.y2}
                  fill="none"
                  stroke={color}
                  strokeWidth="1.6"
                  initial={{ r: 3, opacity: 0 }}
                  animate={{ r: 26, opacity: [0, 0.9, 0] }}
                  transition={{ delay: a.travel, duration: 1.1, ease: 'easeOut' }}
                />
                <motion.circle
                  cx={a.x2}
                  cy={a.y2}
                  fill="none"
                  stroke="#8fe0b7"
                  strokeWidth="1"
                  initial={{ r: 3, opacity: 0 }}
                  animate={{ r: 40, opacity: [0, 0.5, 0] }}
                  transition={{ delay: a.travel + 0.15, duration: 1.4, ease: 'easeOut' }}
                />
                {/* Labels fade in with the strike */}
                <motion.text
                  x={a.x1 + 7}
                  y={a.y1 + 3}
                  fontSize="10"
                  fill="#c4b8a2"
                  fontFamily="ui-monospace, monospace"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: [0, 0.9, 0.9, 0] }}
                  transition={{ duration: a.travel + LINGER, times: [0, 0.1, 0.75, 1] }}
                >
                  {a.from.name}
                </motion.text>
                <motion.text
                  x={a.x2 + 8}
                  y={a.y2 - 7}
                  fontSize="10"
                  fill="#9fd6ba"
                  fontFamily="ui-monospace, monospace"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: [0, 0, 1, 0] }}
                  transition={{ duration: a.travel + LINGER, times: [0, 0.6, 0.75, 1] }}
                >
                  {a.to.name}
                </motion.text>
              </motion.g>
            )
          })}
        </AnimatePresence>
      </svg>

      {/* Live attack readout */}
      <AnimatePresence mode="wait">
        {latest && (
          <motion.div
            key={latest.key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="absolute bottom-3 left-3 rounded border border-white/[0.1] bg-[#0d0f0f]/90 px-3.5 py-2.5 backdrop-blur-sm"
          >
            <div className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full" style={{ background: severityColor[latest.severity] }} />
              <span className="font-mono text-[11px] text-stone-300">{latest.ip}</span>
              <span className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: severityColor[latest.severity] }}>{latest.severity}</span>
            </div>
            <p className="mt-1 text-xs text-stone-200">{latest.vector}</p>
            <p className="mt-0.5 font-mono text-[10px] text-stone-500">{latest.from.name} → {latest.to.name}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Session counter */}
      <div className="absolute bottom-3 right-3 rounded border border-white/[0.1] bg-[#0d0f0f]/90 px-3 py-2 text-right backdrop-blur-sm">
        <p className="font-mono text-lg font-medium tabular-nums text-stone-100">{total.toLocaleString()}</p>
        <p className="text-[9px] font-semibold uppercase tracking-[.14em] text-stone-500">Attacks observed</p>
      </div>
    </div>
  )
}
