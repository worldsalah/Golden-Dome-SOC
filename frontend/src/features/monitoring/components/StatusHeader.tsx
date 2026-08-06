import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import type { ServiceHealthMap } from '../types'

export function StatusHeader({ services, lastUpdated }: { services: ServiceHealthMap; lastUpdated: number }) {
  const [secondsAgo, setSecondsAgo] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setSecondsAgo(Math.round((Date.now() - lastUpdated) / 1000)), 1000)
    return () => clearInterval(t)
  }, [lastUpdated])

  const values = Object.values(services)
  const offlineCount = values.filter((s) => s === 'offline').length
  const warningCount = values.filter((s) => s === 'warning').length

  const overall =
    offlineCount > 0 ? 'degraded' : warningCount > 0 ? 'warning' : values.length ? 'operational' : 'unknown'

  const meta = {
    operational: { color: 'bg-emerald-400', label: 'Operational', text: 'text-emerald-400' },
    warning: { color: 'bg-amber-400', label: 'Degraded Performance', text: 'text-amber-400' },
    degraded: { color: 'bg-red-400', label: 'Service Disruption', text: 'text-red-400' },
    unknown: { color: 'bg-stone-500', label: 'Unknown', text: 'text-stone-500' },
  }[overall]

  return (
    <div className="flex flex-col items-start justify-between gap-3 rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 sm:flex-row sm:items-center">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">Golden Dome Infrastructure</p>
        <div className="mt-1.5 flex items-center gap-2">
          <motion.span
            className={`h-2.5 w-2.5 rounded-full ${meta.color}`}
            animate={{ opacity: [1, 0.4, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <span className={`text-lg font-medium ${meta.text}`}>{meta.label}</span>
        </div>
      </div>
      <div className="text-right">
        <p className="text-xs text-stone-500">Last Update</p>
        <p className="text-sm font-medium text-stone-300">{secondsAgo}s ago</p>
      </div>
    </div>
  )
}
