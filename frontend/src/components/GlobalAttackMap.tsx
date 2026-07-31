import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Globe, MapPin, AlertCircle } from 'lucide-react'
import { getAttackMap, type AttackMapEntry } from '@/services/api'

const W = 1000
const H = 500

function project(lon: number, lat: number): [number, number] {
  return [((lon + 180) / 360) * W, ((90 - lat) / 180) * H]
}

function severityColor(level: number): string {
  if (level >= 13) return '#e05252'
  if (level >= 10) return '#e08a45'
  if (level >= 4) return '#d4b05e'
  return '#6fbf95'
}

function severityLabel(level: number): string {
  if (level >= 13) return 'critical'
  if (level >= 10) return 'high'
  if (level >= 4) return 'medium'
  return 'low'
}

export function GlobalAttackMap() {
  const { data, isLoading } = useQuery({
    queryKey: ['attack-map'],
    queryFn: () => getAttackMap(24, 200),
    refetchInterval: 10_000,
  })

  const attacks = data?.attacks || []
  const hasGeoip = data?.has_geoip || false
  const totalSources = data?.total_unique_sources || 0

  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <p className="text-xs text-stone-500">Loading attack telemetry...</p>
      </div>
    )
  }

  if (attacks.length === 0) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center gap-3">
        <Globe className="h-10 w-10 text-stone-700" />
        <p className="text-sm text-stone-500">No attack source IPs detected in recent alerts</p>
        <p className="text-xs text-stone-600">Attack map will populate when Wazuh alerts contain source IP data</p>
      </div>
    )
  }

  if (!hasGeoip) {
    return (
      <div className="flex h-full w-full flex-col">
        <div className="flex items-center gap-2 border-b border-white/[0.08] px-4 py-3">
          <AlertCircle className="h-4 w-4 text-amber-400" />
          <p className="text-xs text-stone-400">
            GeoIP enrichment is unavailable — {totalSources} source IP(s) detected without geolocation data
          </p>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-2">
            {attacks.slice(0, 20).map((a, i) => (
              <div key={`${a.source_ip}-${i}`} className="flex items-center justify-between rounded-md border border-white/[0.06] bg-[#17181b]/50 px-3 py-2">
                <div className="flex items-center gap-3">
                  <MapPin className="h-4 w-4 text-stone-600" />
                  <span className="font-mono text-xs text-stone-300">{a.source_ip}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-stone-500">{a.rule_description.slice(0, 40)}</span>
                  <span className="text-[10px] font-semibold uppercase" style={{ color: severityColor(a.rule_level) }}>
                    {severityLabel(a.rule_level)}
                  </span>
                  <span className="text-xs text-stone-600">{a.count}x</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

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

        {attacks.filter((a) => a.latitude !== null && a.longitude !== null).map((a: AttackMapEntry, i) => {
          const [x, y] = project(a.longitude!, a.latitude!)
          const color = severityColor(a.rule_level)
          return (
            <motion.g key={`${a.source_ip}-${i}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }}>
              <circle cx={x} cy={y} r="3" fill={color} filter="url(#glow)" />
              <motion.circle
                cx={x} cy={y} fill="none" stroke={color} strokeWidth="1.2"
                initial={{ r: 3, opacity: 0.8 }}
                animate={{ r: 16, opacity: 0 }}
                transition={{ duration: 1.4, ease: 'easeOut', repeat: Infinity, repeatDelay: 2 }}
              />
              <text x={x + 7} y={y + 3} fontSize="9" fill="#c4b8a2" fontFamily="ui-monospace, monospace" opacity="0.7">
                {a.source_ip}
              </text>
            </motion.g>
          )
        })}
      </svg>

      <div className="absolute bottom-3 right-3 rounded border border-white/[0.1] bg-[#0d0f0f]/90 px-3 py-2 text-right backdrop-blur-sm">
        <p className="font-mono text-lg font-medium tabular-nums text-stone-100">{totalSources}</p>
        <p className="text-[9px] font-semibold uppercase tracking-[.14em] text-stone-500">Unique sources</p>
      </div>
    </div>
  )
}
